import time
import re
import json
import hashlib
import os

import requests
from bs4 import BeautifulSoup as bs

from aitextgen.TokenDataset import TokenDataset
from aitextgen.tokenizers import train_tokenizer
from aitextgen.utils import GPT2ConfigCPU
from aitextgen import aitextgen

baseurl = "http://limburgslied.nl"
def check_number_of_lyrics_online():
    r = requests.get(baseurl+'/glossary')
    soup = bs(r.text, 'html.parser')
    numbers = soup.find_all("span", {"class": "views-summary views-summary-unformatted"})
    x = []
    for span in numbers:
        link = baseurl + span.a['href']
        cat = span.a.text.rstrip().lstrip()
        count = span.a.next_sibling.lstrip().rstrip().replace("(","").replace(")","")
        x.append({cat: [int(count), link]})
    return x

def add_new_songs(database, cat_lyrics_online):
    database_delta = [] # stores the categories with different amount of songs
    temp_existing_cat_dict = {}
    temp_online_cat_dict = {}

    for existing_cat in database["count"]: #convert json to dict, so it is easier to handle
        cat_name = list(existing_cat.keys())[0]
        cat_number_local = existing_cat[cat_name][0] #the number of songs in a category
        cat_link = existing_cat[cat_name][1]
        temp_existing_cat_dict[cat_name] = (cat_number_local, cat_link)

    for online_cat in cat_lyrics_online: #convert json to dict, so it is easier to handle
        online_cat_name = list(online_cat.keys())[0]
        cat_number_online = online_cat[online_cat_name][0] #the number of songs in a category
        cat_link = online_cat[online_cat_name][1]
        temp_online_cat_dict[online_cat_name] = (cat_number_online, cat_link)

    for cat, value in temp_online_cat_dict.items(): #check for differences in the two dicts
        if cat in temp_existing_cat_dict:
            if temp_online_cat_dict[cat] > temp_existing_cat_dict[cat]:
                print(f"Extra songs found in category: '{cat}'")
                database_delta.append({cat: value})
        else:
            print(f"New category found: '{cat}'")
            database_delta.append({cat: value})
    if len(database_delta) == 0:
        print("No new songs to download")
        anws = input("Do you want to check the whole database? Type yes or no: ")
        if anws == 'yes':
            begin_download(cat_lyrics_online)
        elif anws == 'no':
            exit()
        else:
            print("Wrong anwser. Please type yes or no")
            print("Exiting")
            exit()
    else:
        print("Begin downloading of lyrics not already in database")
        database["count"] = cat_lyrics_online
        file = open("database.txt", 'w', encoding='utf8')
        file.write(json.dumps(database, ensure_ascii=False, indent=4))
        file.close()
        begin_download(database_delta)


def replace_with_newlines(element):
    text = ''
    for elem in element.recursiveChildGenerator():
        if isinstance(elem, str):
            text += elem.strip()
        elif elem.name == 'br':
            text += '\n'
    return text

def download_song_data(link, cat_name):
    file = open("database.txt", 'r', encoding='utf8')
    database = json.load(file)
    file.close()
    try:
        database["links"]
    except:
        database["links"] = {}
    if cat_name in database["links"]:
        for song in database["links"][cat_name]:
            if song["link"].strip() == link:
                print("link", link, "al gedownload!")
                return
        print("downloading", link)
    else:
        database["links"][cat_name] = []

    r = requests.get(link)
    time.sleep(3)
    soup = bs(r.text, 'html.parser')
    try:
        title = soup.find("h1", {"class": "title"}).text.lstrip().rstrip()
    except:
        title = False
    try:
        tekst = soup.find("div", {"class": "field field-name-field-auteur field-type-text field-label-inline clearfix"}).find("div", {"class": "field-items"}).text.lstrip().rstrip()
    except:
        tekst = False
    try:
        muziek = soup.find("div", {"class": "field field-name-field-componist field-type-text field-label-inline clearfix"}).find("div", {"class": "field-items"}).text.lstrip().rstrip()
    except:
        muziek = False
    try:
        zang = soup.find("div", {"class": "field field-name-field-artiest field-type-text field-label-inline clearfix"}).find("div", {"class": "field-items"}).text.lstrip().rstrip()
    except:
        zang = False
    try:
        album = soup.find("div", {"class": "field field-name-field-album field-type-text field-label-inline clearfix"}).find("div", {"class": "field-items"}).text.lstrip().rstrip()
    except:
        album = False
    try:
        plaats = soup.find("div", {"class": "field field-name-field-plaats field-type-list-text field-label-inline clearfix"}).find("div", {"class": "field-items"}).text.lstrip().rstrip()
    except:
        plaats = False
    try:
        lyrics = replace_with_newlines(soup.find("div", {"class": "field field-name-body field-type-text-with-summary field-label-hidden"})).lstrip().rstrip()
    except:
        lyrics = False

    x = {
        "title": title,
        "tekst": tekst,
        "muziek": muziek,
        "zang": zang,
        "album": album,
        "plaats": plaats,
        "lyrics": lyrics,
        "link": link
    }
    database["links"][cat_name].append(x) #TODO insert new lyric alphabetically
    file = open("database.txt", 'w', encoding='utf8')
    file.write(json.dumps(database, ensure_ascii=False, indent=4))
    file.close()

def get_last_page_int(r):
    soup = bs(r.text, 'html.parser')
    last_link = soup.find("li", {"class": "pager-last last"}).a['href']
    num = re.search("page=([0-9]*)", last_link).group(1)
    return int(num)

def get_data_one_page_from_cat_link(r, cat_name):
    soup = bs(r.text, 'html.parser')
    tbody = soup.find("tbody")
    links_raw = tbody.find_all('a')
    links = []
    for link in links_raw:
        link = baseurl + link['href']
        download_song_data(link, cat_name)

def get_all_data_from_cat_link(link, cat_name):
    r = requests.get(link)
    get_data_one_page_from_cat_link(r, cat_name)
    try:
        last_page_int = get_last_page_int(r) #TODO checken of dit niet +1 moet zijn
    except:
        return
    print("page 1 of", str(last_page_int+1)+":")
    for n in range(1, last_page_int+1):
        time.sleep(1)
        print("page", str(n+1), "of", str(last_page_int+1)+":")
        full_url = link+"?page="+str(n)
        r = requests.get(full_url)
        get_data_one_page_from_cat_link(r, cat_name)

def begin_download(categories):
    for cat in categories:
        cat_name = list(cat.keys())[0]
        print(f"category '{cat_name}'")
        link = cat[cat_name][1]
        get_all_data_from_cat_link(link, cat_name)

def download_database():
    cat_lyrics_online = check_number_of_lyrics_online()
    file = open("database.txt", 'r', encoding='utf8')
    try:
        database = json.load(file)
    except:
        database = {}
    file.close()

    if "count" in database: #database exists, search for extra songs
        add_new_songs(database, cat_lyrics_online)

    else: #database does not exist, download everything. But still check for paritial database (done in begin_download())
        database["count"] = cat_lyrics_online
        file = open("database.txt", 'w', encoding='utf8')
        file.write(json.dumps(database, ensure_ascii=False, indent=4))
        file.close()
        begin_download(database["count"])

def get_hash(text):
    return hashlib.md5(text.encode('utf8')).hexdigest()


def clean_lyrics(lyrics): #TODO totaal niet optimized -> lookbehind/lookahead is je vriend
    lyrics = lyrics.replace('”','"').replace('“','"').replace('’', "'").replace('´',"'").replace('‘',"'").replace('…','.') #standaard quotes, geen utf-8 shit
    lyrics = lyrics.replace('O.K', 'OK') #afkortingen fixen voor zinnen
    lyrics = lyrics.replace('o.k', 'OK')
    lyrics = lyrics.replace('K.O', 'ko')
    lyrics = lyrics.replace('A.O.W', 'AOW')
    lyrics = lyrics.replace('C.D', 'CD')
    lyrics = re.sub('(?<!\d)\.(?=[^\.\n!?\'":\)])', '.\n', lyrics) #newline altijd na punt, behalve als het een punt is of een newline of ervoor een cijfer, eg. Urges aan d’n euverkantj...
    lyrics = re.sub('\ *(?=\.)', '.', lyrics) # geen spatie voor punt
    lyrics = re.sub('\.{1,}', '', lyrics) #verwijder alle punten
    lyrics = re.sub('\!(?=[^\!\n\W])', '?!\n', lyrics) #altijd newline na uitroepteken, behalve na uitroepteken of newline
    lyrics = re.sub('\ (?=!)','', lyrics)
    lyrics = re.sub('\ (?=\?)','', lyrics)
    lyrics = re.sub('\(\d*x\)', '', lyrics) #geen (2x), (3x) enz
    lyrics = re.sub('^\ *', '', lyrics) # geen spatie als begin van een zin
    lyrics = lyrics.replace("REFREIN","Refrein")
    lyrics = lyrics.replace("Refrein :", "Refrein:")
    lyrics = lyrics.replace("Couplet :", "Couplet:")
    lyrics = re.sub('(?<=(Refrein|Couplet))(?=\d)', ' ', lyrics) #altijd spatie tussen Refrein/Couplet en cijfer
    lyrics = re.sub('(?<=(Refrein|Couplet))(?!(:|\ \d))', ':', lyrics) #altijd ':' na Refrein of Couplet behalve bij ':' of een spatie + cijfer
    lyrics = re.sub('(?<=[^\n])Refrein:', '\nRefrein:', lyrics) #altijd newline voor Refrein:
    lyrics = re.sub('Refrein:(?=[^\n])', 'Refrein:\n', lyrics) #altijd newline na Refrein:
    lyrics = re.sub('(?!=[^\n])(?=Couplet)', '\n', lyrics) #altijd newline voor Couplet
    lyrics = re.sub('(?<=Couplet:)(?=[^\n])', '\n', lyrics) #altijd newline na Couplet met cijfer
    lyrics = re.sub('(?<=Couplet \d:)(?=[^\n])', '\n', lyrics) #altijd newline na Couplet met cijfer

    return lyrics

def database_2_csv():
    '''Genereerd tsv bestand'''
    #https://github.com/kylemcdonald/gpt-2-poetry TODO
    file = open("database.txt", 'r', encoding='utf8')
    database = json.load(file)
    file.close()
    cats = database["links"]

    with open("output.csv", 'a', encoding='utf8') as csvFile:
        csvFile.write("author\tsong\ttext\n")
    for cat in cats:
        for song in cats[cat]:
            author = song["zang"]
            title = song["title"]
            lyrics = song["lyrics"]
            lyrics=lyrics.replace('\r', '').replace('\t', ' ')

            #if not author: #TODO vervang author naar tekst or muziek als deze false is
            #    continue
            songString = f"{author}\t{title}\t\"{lyrics}\n\n\"\n"
            with open("output.csv", 'a', encoding='utf8') as csvFile:
                csvFile.write(songString)
    print("File generation done.")

def database_2_txt():
    import re
    '''Genereerd bestand met alleen maak lyrics'''
    #https://github.com/kylemcdonald/gpt-2-poetry TODO
    file = open("database.txt", 'r', encoding='utf8')
    database = json.load(file)
    file.close()
    cats = database["links"]

    blacklistFile = open("blacklist.txt", 'r').read().splitlines()
    for cat in cats:
        for song in cats[cat]:
            #author = song["zang"]
            #title = song["title"]
            lyrics = song["lyrics"]
            if song["link"] in blacklistFile:
                continue #skip als link in blacklist
            lyrics = clean_lyrics(lyrics)

            with open("lyrics.txt", 'a', encoding='utf8') as csvFile:
                csvFile.write(lyrics)
                csvFile.write('\n\n')
    print("File generation done.")


def convert_to_pd(): #not used
    import pandas as pd
    dfs = []
    dfs.append(pd.read_csv("output.csv", sep='\t'))
    df = pd.concat(dfs).reset_index(drop=True)
    print(df)
    if not os.path.exists('content'):
        os.makedirs('content')

    pd.DataFrame({"lyrics": df['text']})\
        .to_csv(os.path.join('content', 'lyrics.csv'), index=False)

def train_data(): #not used
    import gpt_2_simple as gpt2
    gpt2.download_gpt2(model_name="124M")
    learning_rate = 0.0001
    optimizer = 'adam' # adam or sgd
    batch_size = 1
    model_name = "124M" # has to match one downloaded locally
    sess = gpt2.start_tf_sess()

    gpt2.finetune(sess, 'content/lyrics.csv', model_name=model_name,sample_every=50,same_every=50, print_every=10, learning_rate=learning_rate, batch_size=batch_size,restore_from='latest',steps=500)

    lst_results=gpt2.generate(
        sess,
        prefix="<|startoftext|>",
        nsamples=10,
        temperature=0.8, # change me
        top_p=0.9, # Change me
        return_as_list=True,
        truncate="<|endoftext|>",
        include_prefix=True
    )
    for res in lst_results:
        print(res)
        print('\n -------//------ \n')

def train_data_2(cpu_training):
    # The name of the text for training
    file_name = "lyrics.txt"

    # Train a custom BPE Tokenizer on the downloaded text
    # This will save two files: aitextgen-vocab.json and aitextgen-merges.txt,
    # which are needed to rebuild the tokenizer.
    train_tokenizer(file_name)
    vocab_file = "aitextgen-vocab.json"
    merges_file = "aitextgen-merges.txt"

    # GPT2ConfigCPU is a mini variant of GPT-2 optimized for CPU-training
    # e.g. the # of input tokens here is 64 vs. 1024 for base GPT-2.
    if cpu_training:
        config = GPT2ConfigCPU()
        ai = aitextgen(vocab_file=vocab_file, merges_file=merges_file, config=config)
    else: #GPU training, 548M GPT-2 model automatically downloaded
        ai = aitextgen(vocab_file=vocab_file, merges_file=merges_file)

    # You can build datasets for training by creating TokenDatasets,
    # which automatically processes the dataset with the appropriate size.
    data = TokenDataset(file_name, vocab_file=vocab_file, merges_file=merges_file, block_size=64)

    # Train the model! It will save pytorch_model.bin periodically and after completion.
    # On a 2016 MacBook Pro, this took ~25 minutes to run.
    ai.train(data, batch_size=16, num_steps=25000)

    # Generate text from it!
    ai.generate(10)

cpu_training = True
#download_database()
#database_2_csv()
if __name__ == '__main__':
    if not os.path.isfile("./lyrics.txt"):
        database_2_txt()
    exit()
    train_data_2(cpu_training)

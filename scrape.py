import time
import re
import json
import hashlib
import os
import unicodedata

import requests
from bs4 import BeautifulSoup as bs

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
        anws = input("Do you want to check the whole database? y/n: ")
        if anws == 'y':
            begin_download(cat_lyrics_online)
        else:
            return
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
        lyrics = soup.find("div", {"class": "field field-name-body field-type-text-with-summary field-label-hidden"})
        lyrics = str(lyrics) #we laten de lyrics in raw html want er zit veel variatie in de html opmaak
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
    try:
        file = open("database.txt", 'r', encoding='utf8')
        database = json.load(file)
        file.close()
    except:
        database = {}

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
    #begin. Eerst van raw html naar text:
    lyrics = lyrics.replace('\n','').replace('\t', '').replace('<p>', '\n').replace('</p>', '\n').replace('<br/>', '\n') #newlines kunnen in de html kunnen zitten. Laatste is null space character
    lyricssoup = bs(lyrics, 'html.parser') #weer terug naar bs object om rest van de tags te filteren
    lyrics = lyricssoup.text.lstrip().rstrip() #newlines begin en eind van tekst weghalen

    lyrics = unicodedata.normalize('NFC', lyrics) #non-standard chars to standard chars (UTF-8 null spaces etc)
    unicode_replace_dict = { #replacement map
	    '”': '"',
	    '“': '"',
	    '’': "'",
	    '´': "'",
	    '‘': "'",
	    '`': "'",
	    '‚': ',',
	    '„': '"',
	    '_': ' ',
	    '—': '-',
	    '–': '-',
	    '•': '',
	    '©': '',
	    '¢': '\'',
	    '|': '',
	    '×': 'x',
	    '\u2028': '\n',
	    '\u00AD': '',
	    '~': ' ',
	    '{': '',
	    '\\': '',
	    '\u00A0': ' ',
	    '\u00B2': '2',
	    '\u2026': '...',
	    'œ': 'oe',
        '+': '',
    }
    for key, value in unicode_replace_dict.items():
    	lyrics = lyrics.replace(key, value)

    lyrics = re.sub('\.+$', '', lyrics) #geen punten eind vd zin
    lyrics = re.sub('\ +(?=\.)', '.', lyrics) # geen spatie voor punt
    lyrics = re.sub('\ +(?=,)','',lyrics) # geen spaties voor komma
    lyrics = re.sub('\ (?=(\!|\?))', '', lyrics) # geen spatie voor vraag/uitroepteken
    lyrics = lyrics.replace("\n!","!") #verwijder newline voor uitroepteken
    lyrics = lyrics.replace("\n?","?") #verwijder newline voor vraagteken
    #lyrics = re.sub('(?<=\!|\?)(?=[^\n\?\!\'])', '\n', lyrics) #altijd newline na vraag/uitroepteken, behalve na vraag/uitroepteken, newline of '
    #lyrics = re.sub('\(\d*x\)', '', lyrics) #geen (2x), (3x) enz

    lyrics = re.sub('refr(ei|e|i)ng?(\ ?:)?', 'Refrein', lyrics, flags=re.IGNORECASE) #vervang refrein/refreng/refring naar Refrein
    lyrics = re.sub('(k|c)o(e|u)plet(\ ?:)?', 'Couplet', lyrics, flags=re.IGNORECASE) #vervang couplet/koeplet naar Couplet
    lyrics = re.sub('(?<=(Refrein|Couplet)).*', '', lyrics) #verwijder alles na Refrein/Couplet

    #lyrics = re.sub('(?<=(Refrein|Couplet))(?=\d)', ' ', lyrics) #altijd spatie tussen Refrein/Couplet en cijfer
    #lyrics = re.sub('(?<=(Refrein|Couplet))(?!(:|\ \d))', ':', lyrics) #altijd ':' na Refrein of Couplet behalve bij ':' of een spatie + cijfer
    #lyrics = re.sub('(?<=[^\n])Refrein:', '\nRefrein:', lyrics) #altijd newline voor Refrein:
    #lyrics = re.sub('Refrein:(?=[^\n])', 'Refrein:\n', lyrics) #altijd newline na Refrein:
    #lyrics = re.sub('(?!=[^\n])(?=Couplet)', '\n', lyrics) #altijd newline voor Couplet
    #lyrics = re.sub('(?<=Couplet:)(?=[^\n])', '\n', lyrics) #altijd newline na Couplet met cijfer
    #lyrics = re.sub('(?<=Couplet \d:)(?=[^\n])', '\n', lyrics) #altijd newline na Couplet met cijfer
    lyrics = re.sub('\ {2,}', ' ', lyrics) #verwijder meer dan 1 spatie achterelkaar
    lyrics = re.sub('^\'+(?!\w)','', lyrics) #random ' regels
    lyrics = re.sub('(?<=\n)\ *|\ *(?=\n)','',lyrics) # geen spaties begin & eind van zin
    lyrics = re.sub('(?<=\n)^\ *(?=\n)','',lyrics) #geen witregels

    lyrics = re.sub('\n{3,}', '\n\n', lyrics)

    return lyrics

def database_2_csv():
    '''Genereerd tsv bestand'''
    #https://github.com/kylemcdonald/gpt-2-poetry TODO
    print("(re)generating csv file..")
    if os.path.exists("lyrics.csv"): #remove existing lyrics.txt
        os.remove("lyrics.csv")

    file = open("database.txt", 'r', encoding='utf8')
    database = json.load(file)
    file.close()
    cats = database["links"]

    blacklistFile = open("blacklist.txt", 'r').read().splitlines()
    with open("lyrics.csv", 'a', encoding='utf8') as csvFile:
        csvFile.write("lyrics\n")
    for cat in cats:
        for song in cats[cat]:
            author = song["zang"]
            title = song["title"]
            lyrics = song["lyrics"]
            if song["link"] in blacklistFile:
                continue #skip als link in blacklist
            lyrics = clean_lyrics(lyrics).lower()
            #lyrics = re.sub('\n{2,}', '', lyrics)
            #lyrics = "".join([s for s in lyrics.splitlines(True) if s.strip("\r\n")])

            #if not author: #TODO vervang author naar tekst or muziek als deze false is
            #    continue
            songString = f"\"{lyrics}\n\n\"\n"
            with open("lyrics.csv", 'a', encoding='utf8') as csvFile:
                csvFile.write(songString)
    print("File generation done.")

def database_2_txt():
    '''Genereerd bestand met alleen maar lyrics'''
    #https://github.com/kylemcdonald/gpt-2-poetry TODO
    print("(re)generating raw lyrics file..")
    if os.path.exists("lyrics.txt"): #remove existing lyrics.txt
	    os.remove("lyrics.txt")

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
            #lyrics = '\n'.join(str(filter(lambda x: not re.match(r'^\s*$', x), lyrics)))

            with open("lyrics.txt", 'a', encoding='utf8') as txtfile:
                txtfile.write(lyrics)
                #txtfile.write('\n\n')
    print("File generation done.")

if __name__ == '__main__':
    download_database()
    anws = input("Do you want to regenerate the raw lyrics file? y/n: ")
    if anws == 'y':
        database_2_csv()
    else:
    	exit()

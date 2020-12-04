# Limburg Lyrics Database
A database containing over 9000 Dutch carnevals songs in the Limburgish (Limburgs) dialect. Used in the project [ZuujeAI](https://github.com/TomJansen/ZuujeAI).

Code tested with Python 3.7, 64 bits

## Installation
In this folder, run `python -m pip install -r requirements.txt` and then run the main file `scrape.py`.

## Files
### scrape.py
This is the main python file for scraping the website and putting it in `database.txt`. It has the ability to check for new songs and put these in the database as well, without redownloading everything.

One imporant thing for AI training is a clean dataset. `scrape.py` handles this as well, and can generate clean lyrics from the raw html lyrics. These clean lyrics are stored in `lyrics.txt`, but a better format will come soon.

### database.txt
This is the main database file in json. It per song it contains the author, lyrics, in which place it was written, etc. The lyrics are in raw html

### lyrics.txt
Is a long list of all lyrics cleaned.

### blacklist.txt
Some links on the website are not lyrics but blogposts (or really shitty formatted lyrics). The links to these blogposts can be stored in `blacklist.txt` and are consequently not included in `lyrics.txt`.

### count.py
The lyrics on the website contains many weird UTF-8 characters. Many of these characters are cleaned in `scrape.py`, but when new lyrics are added new weird chars can appear. `count.py` lists all characters in `lyrics.txt` and their occurence. When new weird characters appear, these can thus be identified and added to the `unicode_replace_dict` dictionary.

Usage: `python .\count.py .\lyrics.txt`

## TODO
- Better alternative to `lyrics.txt` (csv?)

## Licence
The songtexts are in the licence Attribution-ShareAlike 3.0 Unported.

Code in this repo is MIT licenced

See also http://limburgslied.nl/content/juridisch

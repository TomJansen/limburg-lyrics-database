# Limburg Lyrics Database
A database containing over 9000 Dutch carnevals songs in the Limburgish (Limburgs) dialect. Used in the project [ZuujeAI](https://github.com/TomJansen/ZuujeAI).

Tested with Python 3.7, 64 bits

## count.py
The lyrics on the website contains many weird UTF-8 characters. Many of these characters are cleaned in `scrape.py`, but when new lyrics are added new weird chars can appear. `count.py` lists all characters in `lyrics.txt` and their occurence. When new weird characters appear, these can thus be identified and added to the `unicode_replace_dict` dictionary.

Usage: `python .\count.py .\lyrics.txt`

Warning: this command can potentially garble your terminal!

## Licentie
The songtexts are in the licence Attribution-ShareAlike 3.0 Unported.
Code has the MIT licence
See also http://limburgslied.nl/content/juridisch

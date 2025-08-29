# Import Export Kobo annotation

# Licence

MIT License

Copyright (c) 2025 Froggy / FroggyCorp.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

# Why that program

I can't find any plugin or program for saving Kobo bookmark to Calibre. We can save bookmarks to text file with KoboUtilities but can't put them back (or didn't find). Advantage of Calibre, is to keep bookmark if you move the book to another library. It also create .json inside the directory of book.

# What to conf ?

Edit calibre-kobo-annotation.py and change library_path to the directory of expected calibre library

# How it works ?

1. Plug your kobo, then connect
2. Open a terminal and launch "calibre-debug -e calibre-kobo-annotation.py cmd" cmd can be import or export
3. The program will override all bookmark on Kobo or Calibre for each book present both side, depending on import or export option
4. It saves Kobo bookmark information inside annotation field of Calibre db with new dict. It should be safe, Calibre don't check if there is useless information

# Limitation :

There is no warranty of not loosing everything. It uses direct SQL, and it's more less garbage coding.
Actually, working on Kobo Libra Colour. Should work on any Kobo.

# Todo :

Make some conversion beetween Kobo and Calibre bookmark format. So no more tricks to save data and a bookmark created inside Calibre viewer will be in Kobo and vice versa.
Make it as GUI pluggin for more easy use.
Use the Calibre API despite SQL but it's painfull.

# Version :

0.1 : initial release
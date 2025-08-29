'''
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
'''

#command : calibre-debug -e calibre-kobo-annotation.py cmd
version = 0.1
library_path = '/my/calibre/path'
kobo_path_debug = '/not/to/use/'


import sqlite3
import sys

from calibre.library import db
from calibre.utils.date import *
from calibre.utils.iso8601 import parse_iso8601
from calibre.devices.scanner import *
from calibre.devices.cli import *

cmd = ''
option = ''

#check what to do
if len(sys.argv) >= 2:
    if sys.argv[1] == 'import':
        cmd = 'import'
        print("Kobo -> Calibre")
    elif sys.argv[1] == 'export':
        cmd = 'export'
        print("Calibre -> Kobo")

    #debug on secondary
    if len(sys.argv) >= 3:
        if sys.argv[2] == 'debug':
            option = 'debug'
else:
    print("import to save Kobo > Calibre")
    print('export to save Calibre > Kobo')
    print("version : " + str(version))
    exit()

if option != 'debug':
    if cmd == 'import':
        print("It will erase all annotation inside Calibre with annotation from Kobo, press 'o' to confirm")
    if cmd == 'export':
        print("It will erase all annotation inside Kobo with annotation from Calibre, press 'o' to confirm")
    a = input()
    if a != 'o':
        print("Leaving")
        exit()

#if debug, don't connect to kobo
if option == 'debug':
    kobo_path = kobo_path_debug
    print('DEBUG : overriding kobo_path with : ' + kobo_path_debug)
#if not, try connecting to kobo
elif option != 'debug':
    #Connecting to Kobo
    scanner = DeviceScanner()
    scanner.scan()
    connected_devices = []
    dev = None
    for d in device_plugins():
        try:
            d.startup()
        except Exception:
            print(f'Startup failed for device plugin: {d}')
        if d.MANAGES_DEVICE_PRESENCE:
            cd = d.detect_managed_devices(scanner.devices)
            if cd is not None:
                connected_devices.append((cd, d))
                dev = d
                break
            continue
        ok, det = scanner.is_device_connected(d)
        if ok:
            dev = d
            dev.reset(log_packets=False, detected_device=det)
            connected_devices.append((det, dev))

    if dev is None:
        print('Unable to find a connected ebook reader.', file=sys.stderr)
        shutdown_plugins()
        exit()

    for det, d in connected_devices:
        try:
            d.open(det, 'liseuse')
        except Exception:
            continue
        else:
            dev = d
            d.specialize_global_preferences(device_prefs)
            break

    #check its a kobo
    if (dev.description.find("Kobo")) == -1:
        print("ERROR : Kobo not found")
        exit()

    print("Kobo found : " + dev.name)

    #we set path to kobo related to API
    kobo_path = dev.get_device_information()
    kobo_path = kobo_path[4]['main']['prefix']
    print('Path to mounted Kobo : ' + kobo_path)

if cmd == 'import':
    print('Importing Kobo -> Calibre')

    #loading kobo annotations from sqlite db
    kobo_sql_path = kobo_path + '/.kobo/KoboReader.sqlite'
    kobo_connect = sqlite3.connect(kobo_sql_path)
    kobo_cur = kobo_connect.cursor()

    kobo_bookmark_select = \
                'SELECT c.BookTitle, bm.*  \
                FROM Bookmark bm LEFT OUTER JOIN Content c ON c.ContentID = bm.ContentID \
                ORDER BY c.Booktitle'
    try:
        kobo_cur.execute(kobo_bookmark_select)
    except sqlite3.DatabaseError as er:
        print('File not found, check kobo_path : ' + kobo_sql_path)
        print(er.sqlite_errorcode)
        print(er.sqlite_errorname)
        kobo_connect.close()
        exit()

    kobo_cur.execute(kobo_bookmark_select)
    kobo_bookmark = kobo_cur.fetchall()
    kobo_connect.close()

    #we make annot format for calibre
    import_calibre_annot = {}
    for data in kobo_bookmark:
        tmp_annot = [({'title': data[1], 'type': 'bookmark', 'timestamp': utcnow().isoformat(), \
                    'uuid' : '', 'highlighted_text' : '', 'notes' : '', \
                    'kobo_BookmarkID' : data[1], 'kobo_VolumeID' : data[2], 'kobo_ContentID' : data[3], \
                    'kobo_StartContainerPath' : data[4], 'kobo_StartContainerChildIndex' : data[5], \
                    'kobo_StartOffset' : data[6], 'kobo_EndContainerPath' : data[7], 'kobo_EndContainerChildIndex' : data[8], \
                    'kobo_EndOffset' : data[9], 'kobo_Text' : data[10], 'kobo_Annotation' : data[11], \
                    'kobo_ExtraAnnotationData' : data[12], 'kobo_DateCreated' : data[13], 'kobo_ChapterProgress' : data[14], \
                    'kobo_Hidden' : data[15], 'kobo_Version' : data[16], 'kobo_DateModified' : data[17], \
                    'kobo_Creator' : data[18], 'kobo_UUID' : data[19], 'kobo_UserID' : data[20], \
                    'kobo_SyncTime' : data[21], 'kobo_Published' : data[22], 'kobo_ContextString' : data[23], \
                    'kobo_Type' : data[24], 'kobo_Color' : data[25],  \
                    }, (parse_iso8601(utcnow().isoformat()) - EPOCH).total_seconds())]
        
        if data[0] not in import_calibre_annot:
        #first time ? creating index and add annot
            import_calibre_annot[data[0]] = tmp_annot
        else:
            import_calibre_annot[data[0]] = import_calibre_annot[data[0]] + tmp_annot

    #for each annotations, we check if book exist inside calibre library
    db_calibre = db(library_path).new_api   #use for annotation API

    #with SQL because API or whatever is painfull with no documentation
    con = sqlite3.connect(library_path + '/metadata.db')
    cur = con.cursor()

    for data in import_calibre_annot:
        book_name = data
        cur.execute('SELECT id FROM books WHERE title = "'+ book_name + '"')
        book_id = cur.fetchone()
        if book_id != None:
            print('Saving book to Calibre : ' + book_name)
            #we save annotation for book with the API for more clean usage
            db_calibre.set_annotations_for_book(book_id[0], 'EPUB', import_calibre_annot[book_name])

    con.close()
    db_calibre.close()

if cmd == 'export':

    print('Exporting Calibre -> Kobo')

    #loading kobo books from sqlite db
    kobo_sql_path = kobo_path + '/.kobo/KoboReader.sqlite'
    kobo_connect = sqlite3.connect(kobo_sql_path)
    kobo_cur = kobo_connect.cursor()

    kobo_books_select = \
                'SELECT BookTitle, BookID  \
                FROM Content \
                GROUP BY BookTitle \
                ORDER BY Booktitle'
    try:
        kobo_cur.execute(kobo_books_select)
    except sqlite3.DatabaseError as er:
        print('File not found, check kobo_path : ' + kobo_sql_path)
        print(er.sqlite_errorcode)
        print(er.sqlite_errorname)
        kobo_connect.close()
        exit()

    kobo_cur.execute(kobo_books_select)
    kobo_books = kobo_cur.fetchall()

    #for each books, we check if book exist inside calibre library
    db_calibre = db(library_path).new_api   #use for annotation API

    #with SQL because API or whatever is painfull with no documentation
    con = sqlite3.connect(library_path + '/metadata.db')
    cur = con.cursor()
    
    for books in kobo_books:
        book_name = str(books[0])
        book_kobo_id = books[1]
        cur.execute('SELECT id FROM books WHERE title = "'+ book_name + '"')
        book_id = cur.fetchone()
        if book_id != None:
        #check if book exist
            calibre_annotation = db_calibre.all_annotations_for_book(book_id[0])
            if len(calibre_annotation) > 0:
            #check if there is kobo annot
                if ('kobo_VolumeID' in calibre_annotation[0]['annotation']):
                #here we go
                    print('Synching book : ' + book_name)
                    #we delete annot in Kobo
                    kobo_delete_bookmark = 'DELETE FROM Bookmark WHERE VolumeID = "' + book_kobo_id + '"'
                    kobo_cur.execute(kobo_delete_bookmark)
                    #we add the bookmark
                    for annotation in calibre_annotation:
                        tmp_annotation = annotation['annotation'] #weird
                        kobo_insert_bookmark = 'INSERT INTO Bookmark \
                        (BookmarkID, VolumeID, ContentID, StartContainerPath, StartContainerChildIndex, \
                        StartOffset, EndContainerPath, EndContainerChildIndex, EndOffset, Text, \
                        Annotation, ExtraAnnotationData, DateCreated, ChapterProgress, Hidden, Version, DateModified, Creator, \
                        UUID, UserID, SyncTime, Published, ContextString, Type, Color) VALUES ( \
                        "'+ str(tmp_annotation['kobo_BookmarkID']) +'", "'+ str(tmp_annotation['kobo_VolumeID']) +'", "'+ str(tmp_annotation['kobo_ContentID']) +'",  \
                        "'+ str(tmp_annotation['kobo_StartContainerPath']) +'", "'+ str(tmp_annotation['kobo_StartContainerChildIndex']) +'", "'+ str(tmp_annotation['kobo_StartOffset']) +'",  \
                        "'+ str(tmp_annotation['kobo_EndContainerPath']) +'", "'+ str(tmp_annotation['kobo_EndContainerChildIndex']) +'", "'+ str(tmp_annotation['kobo_EndOffset']) +'",  \
                        "'+ str(tmp_annotation['kobo_Text']) +'", "'+ str(tmp_annotation['kobo_Annotation']) +'", "'+ str(tmp_annotation['kobo_ExtraAnnotationData']) +'",  \
                        "'+ str(tmp_annotation['kobo_DateCreated']) +'", "'+ str(tmp_annotation['kobo_ChapterProgress']) +'", "'+ str(tmp_annotation['kobo_Hidden']) +'",  \
                        "'+ str(tmp_annotation['kobo_Version']) +'", "'+ str(tmp_annotation['kobo_DateModified']) +'", "'+ str(tmp_annotation['kobo_Creator']) +'",  \
                        "'+ str(tmp_annotation['kobo_UUID']) +'", "'+ str(tmp_annotation['kobo_UserID']) +'", "'+ str(tmp_annotation['kobo_SyncTime']) +'",  \
                        "'+ str(tmp_annotation['kobo_Published']) +'", "'+ str(tmp_annotation['kobo_ContextString']) +'", "'+ str(tmp_annotation['kobo_Type']) +'",  \
                        "'+ str(tmp_annotation['kobo_Color']) +'");'
                        kobo_cur.execute(kobo_insert_bookmark)
                    
    cur.close()
    kobo_connect.commit()
    kobo_cur.close()
    db_calibre.close()

if option != 'debug':
    print("Error seems ok, drive should be ejected")
    dev.eject()

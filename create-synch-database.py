#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os
import re

#-------------------------------------------------------------------------
# Опции:

database_name = 'database/synch.sqlite'

#-------------------------------------------------------------------------
# Функции:

def metadict_path (metadict_dir):
    """Возвращает абсолютный путь к каталогу словарей."""
    # Получаем абсолютный путь к каталогу скрипта:
    script_path = os.path.dirname(os.path.abspath(__file__))
    # Добавляем к пути каталог словарей:
    metadict_path = script_path + '/' + metadict_dir
    return metadict_path

def find_files (directory):
    """Возвращает список путей ко всем файлам каталога, включая подкаталоги."""
    path_f = []
    for d, dirs, files in os.walk(directory):
        for f in files:
                # Формирование адреса:
                path = os.path.join(d,f)
                # Добавление адреса в список:
                path_f.append(path)
    return path_f

def create_synch_database (database_name):
    """База данных sqlite, таблица постов на synch."""
    database = sqlite3.connect(metadict_path(database_name))
    cursor = database.cursor()
    cursor.execute("""CREATE TABLE posts (
        post_number INTEGER NOT NULL PRIMARY KEY UNIQUE,
        thread_number INTEGER NOT NULL,
        thread_post_number INTEGER NOT NULL,
        post_datetime INTEGER NOT NULL,
        post_theme TEXT DEFAULT NULL,
        post_email TEXT DEFAULT NULL,
        post_name TEXT DEFAULT NULL,
        post_trip TEXT DEFAULT NULL,
        post_file_name TEXT DEFAULT NULL,
        post_file_link TEXT DEFAULT NULL,
        post_file_prev TEXT DEFAULT NULL,
        post_youtube_video TEXT DEFAULT NULL,
        post_youtube_image TEXT DEFAULT NULL,
        post_content TEXT DEFAULT NULL,
        post_citation TEXT DEFAULT NULL,
        post_urls TEXT DEFAULT NULL,
        post_links TEXT DEFAULT NULL
        )""")
    cursor.execute("""CREATE INDEX index_posts ON posts (
        post_number,
        thread_number,
        thread_post_number,
        post_datetime,
        post_theme,
        post_email,
        post_name,
        post_trip,
        post_file_name,
        post_file_link,
        post_file_prev,
        post_youtube_video,
        post_youtube_image,
        post_content,
        post_citation,
        post_urls,
        post_links
        )""")
    database.close()
    print("[OK] CREATE",database_name)

#-------------------------------------------------------------------------
# Тело программы:

if os.path.exists(metadict_path(database_name)) is not True:
    create_synch_database(database_name)
else:
    print("[FAIL] EXIST", metadict_path(database_name))

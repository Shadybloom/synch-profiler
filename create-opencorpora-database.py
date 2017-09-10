#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os
import re

#-------------------------------------------------------------------------
# Опции:

opencorpora_dir = 'dicts/word-length-dicts'
database_name = 'database/opencorpora-sing-nom.sqlite'

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

def create_database (database_name, opencorpora_dir):
    """База данных sqlite, таблицы под словари"""
    # Составляется список словарей, создаётся база данных и подключение к ней:
    opencorpora_dicts = find_files(metadict_path(opencorpora_dir))
    database = sqlite3.connect(metadict_path(database_name))
    cursor = database.cursor()
    for dict in sorted(opencorpora_dicts):
        table_name = 'opencorpora' + ''.join(re.findall('opencorpora-sing-nom-([0-9]+)\.txt', str(dict)))
        # Форматирование вывода -- удобная штука (хотя ввод данных таким образом, это уязвимость): 
        #create_string = "CREATE TABLE {} (words TEXT DEFAULT NULL)".format(table_name)
        #print(create_string)
        cursor.execute("CREATE TABLE IF NOT EXISTS "+table_name+" (words TEXT DEFAULT NULL)")
        cursor.execute("CREATE INDEX IF NOT EXISTS index_"+table_name+" ON "+table_name+" (words)")
    database.close()
    print("[OK] CREATE",database_name)

def fill_database (database_name, opencorpora_dir):
    """База данных sqlite, заполнение таблиц словарями opencorpora"""
    opencorpora_dicts = find_files(metadict_path(opencorpora_dir))
    database = sqlite3.connect(metadict_path(database_name))
    cursor = database.cursor()
    for dict in sorted(opencorpora_dicts):
        normal_dict_file = open(dict, "r")
        table_name = 'opencorpora' + ''.join(re.findall('opencorpora-sing-nom-([0-9]+)\.txt', str(dict)))
        # Слова переносятся в таблицу базы данных:
        for line in normal_dict_file:
            word = ''.join(re.sub('\n', '', line))
            # Отдельно вносим переменную в строку, и отдельно знаения кортежом (это защита от sql-инъекций)
            cursor.execute("INSERT INTO "+table_name+" VALUES(?)", (word,))
        normal_dict_file.close()
    database.commit()
    database.close()
    print("[OK] INSERT",database_name)

def word_test_sql (word,cursor):
    """Проверяет, есть ли слово в базе данных"""
    # Номер таблицы, это длина слова:
    word_lenght = len(word)
    # А вот не нужно хардкодить (число таблиц в базе данных может измениться)
    if word_lenght > 32:
        word_lenght = 32
    table_name = 'opencorpora' + str(word_lenght)
    #database = sqlite3.connect(metadict_path(database_name))
    #cursor = database.cursor()
    # Вот так делать не нужно, чистейшая уязвимость:
    #test_string = "SELECT words FROM {} WHERE words='{}'".format(table_name, word)
    # Ввод данных должен осуществляться средствами sqlite:
    cursor.execute("SELECT words FROM "+table_name+" WHERE words=?",(word,))
    result = cursor.fetchall()
    #database.close()
    if result:
        return True
    else:
        return False

#-------------------------------------------------------------------------
# Тело программы:

if os.path.exists(metadict_path(database_name)) is not True:
    create_database(database_name,opencorpora_dir)
    fill_database(database_name,opencorpora_dir)
else:
    # Проверка слова:
    word = 'абракадабра'
    database = sqlite3.connect(metadict_path(database_name))
    cursor = database.cursor()
    print(word, word_test_sql(word,cursor))
    database.close()

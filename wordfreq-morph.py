#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Скрипт извлекает слова из текстового файла и сортирует их по частоте.
# С помощью модуля pymorphy2 можно привести слова к начальной форме (единственное число, именительный падеж).

# Нужен pymorphy2 и русскоязычный словарь для него!
# pip install --user pymorphy2

# Примеры:
# ./wordfreq-morph.py ./text-file.txt | less
# xclip -o | ./wordfreq-morph.py -m

# Проверялся на интерпретаторе:
# Python 3.6.1 on linux

import sys
import sqlite3
import os
import re
import argparse
# Сортировка вывода словарей:
from collections import OrderedDict

#------------------------------------------------------------------------------
# Опции:

# Проверочный морфологический словарь (в каталоге скрипта):
NORMAL_DICT_PATH = 'dict.opencorpora-sing-nom.txt'
NORMAL_DICT_DIR = 'word-length-dicts'
database_name = 'opencorpora-sing-nom.sqlite'

#-------------------------------------------------------------------------
# Аргументы командной строки:

def create_parser():
    """Список доступных параметров скрипта."""
    parser = argparse.ArgumentParser()
    parser.add_argument('file',
                        nargs='*',
                        help='Русскоязычный текстовый файл в UTF-8'
                        )
    parser.add_argument('-m', '--morph',
                        action='store_true', default='False',
                        help='Преобразование слов в начальную форму (нужен pymorphy2)'
                        )
    return parser

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

def lowercase (text):
    """Создаёт из текста список слов в нижнем регистре"""
    # Переводим текст в нижний регистр:
    text = str(text.lower())
    # Регексп вытаскивает из текста слова:
    words = re.findall(r"(\w+)", text, re.UNICODE)
    # Восстанавливаются ссылки:
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    words = words + urls
    return words

def wordfreq_old (words):
    """Создаёт словарь с частотой слов"""
    stats = {}
    # Слово -- ключ словаря, значение, это его частота:
    for word in words:
        stats[word] = stats.get(word, 0) + 1
    return stats

def word_test_slow (word):
    """Светяет слово со словарём, выбирая словарь по длине слова."""
    # Определяем длину слова:
    search_string = '-' + str(len(word)) + '.txt'
    dicts_list = find_files(metadict_path(NORMAL_DICT_DIR))
    test = False
    # Подключаем словарь для проверки:
    for dict in dicts_list:
        if search_string in dict:
            normal_dict_file = open(dict, "r")
            normal_dict = normal_dict_file.read()
            normal_dict_file.close()
            if word in normal_dict:
                return True
            else:
                return False

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
    cursor.execute("SELECT words FROM "+table_name+" WHERE words=?",(word,))
    result = cursor.fetchall()
    #database.close()
    if result:
        return True
    else:
        return False

def wordfreq_morph (words):
    """Создаёт словарь с частотой слов (в начальной форме)"""
    # Морфологический анализатор:
    import pymorphy2
    stats = {}
    n_stats = {}
    for word in words:
        stats[word] = stats.get(word, 0) + 1
    morph = pymorphy2.MorphAnalyzer()
    for item in stats:
        # Слово приводится к начальной форме:
        n_word = morph.parse(item)[0].normal_form
        # Неологизмы оставляем без изменений:
        if word_test_sql(n_word,cursor) is not True:
            n_word = item
        # Создаётся новый ключ, или прибавляется значение к существующему:
        if n_word not in n_stats:
            n_stats[n_word] = stats[item]
        else:
            n_stats[n_word] = n_stats[n_word] + stats[item]
    return n_stats

def dict_sort (stats):
    """Сортировка словаря по частоте и алфавиту"""
    stats_sort = OrderedDict(sorted(stats.items(), key=lambda x: x[0], reverse=False))
    stats_list = OrderedDict(sorted(stats_sort.items(), key=lambda x: x[1], reverse=True))
    return stats_list

#-------------------------------------------------------------------------
# Тело программы:

# Создаётся список аргументов скрипта:
parser = create_parser()
namespace = parser.parse_args()

# Проверяем, существует ли указанный файл:
file_patch = ' '.join(namespace.file)
if namespace.file is not None and os.path.exists(file_patch):
    file = open(file_patch, "r")
    text = file.read()
    file.close()
# Если нет, читаем стандартный ввод:
else:
    text = sys.stdin.read()

# Извлекаем из текста слова:
words = lowercase(text)

# Подключение к базе данных:
database = sqlite3.connect(metadict_path(database_name))
cursor = database.cursor()

# Если указано преобразование слов:
if namespace.morph is True:
    wordfreq = wordfreq_morph(words)
else:
    wordfreq = wordfreq_old(words)

# Отключаемся от базы данных:
database.close()

# Вывод словаря:
wordfreq_sort=dict_sort(wordfreq)
for word, count in wordfreq_sort.items():
    print (count, word)

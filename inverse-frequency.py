#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Выборка ключевых слов, сравнение с другими словарями.

import re
import os
import sys
import argparse
from math import log
from collections import OrderedDict

#-------------------------------------------------------------------------
# Опции:

METADICT_DIR = 'dict/test/'

#-------------------------------------------------------------------------
# Аргументы командной строки:

def create_parser():
    """Список доступных параметров скрипта."""
    parser = argparse.ArgumentParser()
    parser.add_argument('file',
                        nargs='*',
                        help='Файл словаря, который сравниваем с другими'
                        )
    parser.add_argument('-d', '--dict',
                        action='store', dest='dict', type=str,
                        help='Ссылка на каталог словарей для сравнения'
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
    for d, dirs, text_files in os.walk(directory):
        for f in text_files:
                # Формирование адреса:
                path = os.path.join(d,f)
                # Добавление адреса в список:
                path_f.append(path)
    return path_f

def gen_corpora (text_files):
    """Создаёт текстовый корпус из кучи словарей (или любых текстовых файлов)."""
    dict_corpora = {}
    for file in text_files:
        f = open(file, "r")
        text = f.read()
        dict_corpora[file] = text
        f.close()
    return dict_corpora

def gen_metadict (wordlist, text_files, corpora):
    """Создаёт словарь со словами и их характеристиками (частотой, значимостью).
    
    TF-IDF вычисляется для каждого слова по оче простой формуле TF x IDF, где:
    - TF (Term Frequency) — частота слова в треде, я взял просто количество повторений.
    - IDF (Inverse Document Frequency) — величина, обратная количеству тредов, содержащих в себе это слово.
    Я взял log(N/n), где N — общее кол-во тредов в выборке, n — кол-во тредов, в которых есть это слово.
    То есть, если из 30 тредов, включая наш, 29 содержат слово «не», его вес уменьшается в 0.033 раз.
    А слово «отряд», которое есть только в нашем треде, напротив, получает вес в log(N) раз больше.
    Таким образом можно узнать, чем тред двух слоупоков отличается от других в выборке.
    """
    metadict = {}
    metadict_key = 0
    for line in wordlist:
        # Извлекаем из строки слово и число совпадений:
        word = ''.join(re.findall('[а-яёa-z0-9]+$', line))
        frequency = ''.join(re.findall('^[0-9]+', line))
        # Создаём временный словарь:
        dict_word = {}
        dict_word['word'] = word
        dict_word['frequency'] = frequency
        dict_word['IDF_N'] = len(text_files) + 1
        # Определяем сколько раз встречается слово в дргуих словарях:
        n = 0
        for content in corpora.values():
            if word in content:
                n = n + 1
        dict_word['IDF_n'] = n + 1
        # Логарифм от ( общего числа словарей / число совпадений ) = редкость слова
        dict_word['IDF-TF'] = log(dict_word['IDF_N']/dict_word['IDF_n'])
        # Число совпадение x редкость слова = значимость слова
        # Числа с плавающей запятой превращаются в натуральные
        dict_word['IDF-TF-frequency'] = int(dict_word['frequency']) * \
                int((dict_word['IDF-TF'] * 1000) / 1000)
        # Временный словарь переносится в метасловарь:
        metadict[metadict_key] = dict_word
        metadict_key = metadict_key + 1
    return metadict

#-------------------------------------------------------------------------
# Обработка аргументов командной строки:

# Создаётся список аргументов скрипта:
parser = create_parser()
namespace = parser.parse_args()

# Проверяем, существует ли целевой файл:
file_patch = ' '.join(namespace.file)
# Если существует, переносим его в список:
wordlist = []
if namespace.file is not None and os.path.exists(file_patch):
    file = open(file_patch, "r")
    for line in file:
        wordlist.append(line)
    file.close()
# Если нет, читаем стандартный ввод:
else:
    for line in sys.stdin:
        wordlist.append(line)

# Проверка, указан ли каталог словарей:
if namespace.dict != None:
    text_files = find_files(namespace.dict)
else:
    # Если нет, мспользовать стандартную:
    metadict_dir = METADICT_DIR
    text_files = find_files(metadict_path(metadict_dir))

#-------------------------------------------------------------------------
# Тело программы:

# Формируем текстовый корпус:
corpora = gen_corpora(text_files)
# Вычисляем IDF и заносим в метасловарь:
metadict = gen_metadict(wordlist, text_files, corpora)

# Упрощённый словарь для вывода данных:
idf_dict = {}
for key in metadict:
    word = metadict[key]['word']
    idf_frequency = metadict[key]['IDF-TF-frequency']
    idf_dict[word] = idf_frequency

# Сортируем упрощённый словарь:
idf_sort = OrderedDict(sorted(idf_dict.items(), key=lambda x: x[0], reverse=False))
idf_list = OrderedDict(sorted(idf_sort.items(), key=lambda x: x[1], reverse=True))

# Вывод данных:
for word, count in idf_list.items():
    print (count, word)

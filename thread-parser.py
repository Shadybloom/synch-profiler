#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Скрипт извлекает посты из треда.
# python ~/workspace/thread-parser.py | sed 's/>>[0-9]\{7\}//g' | ~/workspace/wordfreq-morph.py -m | less

# Так можно вытащить посты нужного неймфага:
# name='Jerry' ; for file in * ; do ~/workspace/word-frequency/scripts/thread-parser.py $file -n $name ; done

# А так всех неймфагов:
# mkdir namefags ; IFS=$'\n' ; for file in * ; do ~/workspace/word-frequency/scripts/thread-parser.py $file -l > /tmp/names ; for name in $(cat /tmp/names) ; do ~/workspace/word-frequency/scripts/thread-parser.py $file -n $name >> ./namefags/$name ; done ; done

# Так можно создать словари из кучи тредов:
# for file in * ; do ~/workspace/thread-parser.py $file | sed 's/>>[0-9]\{7\}//g' | ~/workspace/wordfreq-morph.py -m > /tmp/dicts/$file-dict ; done

import os
import sys
import re
import argparse
import lxml.html
from datetime import datetime

#-------------------------------------------------------------------------
# Аргументы командной строки:

def create_parser():
    """Список доступных параметров скрипта."""
    parser = argparse.ArgumentParser()
    parser.add_argument('file',
                        nargs='*',
                        help='Файл в формате html'
                        )
    parser.add_argument('-l', '--list',
                        action='store_true', default='False',
                        help='Список всех имён в треде'
                        )
    parser.add_argument('-n', '--name',
                        action='store', dest='name', type=str,
                        help='Имя, посты с которым выбираем'
                        )
    return parser

#-------------------------------------------------------------------------
# Функции

def synch_thread_parser (thread):
    """Извлекаем из треда на синче содержание постов"""
    # Меняем <br> на символы новой строки:
    for br in thread.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    # Извлекаем посты из треда:
    elements = thread.xpath('.//div[@class="body" or @class="body media-body"]')
    for el in elements:
        print (el.text_content())

def macaque_thread_parser (thread):
    """Извлекаем из треда на дваче содержание постов"""
    for br in thread.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    elements = thread.xpath('.//blockquote[@class="post-message"]')
    for el in elements:
        print (el.text_content())

def synch_thread_names (thread):
    """Берём из треда на синче имена неймфагов"""
    # Меняем <br> на символы новой строки:
    for br in thread.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    # Извлекаем имена из треда:
    elements = thread.xpath('.//span[@class="name"]')
    # Все имена в список:
    list = []
    for el in elements:
        list.append(el.text_content())
    # Удаляем повторы и сортируем:
    list = sorted(set(list))
    return list

def synch_thread_namefag (thread, name):
    """Берём из треда на синче посты неймфага"""
    # Меняем <br> на символы новой строки:
    for br in thread.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    # Извлекаем из треда блоки постов:
    posts = thread.xpath(".//div[@class='post reply row' or @class='post op']")
    for post in posts:
        postname = post.xpath('.//span[@class="name"]')[0]
        # Если имя совпадает
        if postname.text_content() == name:
            elements = post.xpath('.//div[@class="body" or @class="body media-body"]')
            for el in elements:
                print (el.text_content())

#----------------------------------------------------------------------
# Тело программы:

# Создаётся список аргументов скрипта:
parser = create_parser()
namespace = parser.parse_args()

# Проверяем, существует ли указанный файл:
file_patch = ' '.join(namespace.file)
if namespace.file is not None and os.path.exists(file_patch):
    thread = lxml.html.parse(file_patch).getroot()
    if namespace.list is True:
        for name in synch_thread_names(thread):
            print (name)
        exit()
    if namespace.name != None:
        name = ''.join(namespace.name)
        synch_thread_namefag(thread, name)
    else:
        synch_thread_parser(thread)
        macaque_thread_parser(thread)
# Если нет, читаем стандартный ввод:
else:
    thread = lxml.html.fromstring(sys.stdin.read())
    if namespace.list is True:
        for name in synch_thread_names(thread):
            print (name)
        exit()
    if namespace.name != None:
        name = ''.join(namespace.name)
        synch_thread_namefag(thread, name)
    else:
        synch_thread_parser(thread)
        macaque_thread_parser(thread)

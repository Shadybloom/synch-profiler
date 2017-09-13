#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Скрипт извлекает посты из треда и переносит их в базу данных.

import os
import sys
import re
import argparse
import lxml.html
from lxml import etree
from bs4 import BeautifulSoup
import time
import datetime
import sqlite3

#-------------------------------------------------------------------------
# Опции:

database_name = 'database/synch.sqlite'
threads_dir = 'threads'

#-------------------------------------------------------------------------
# Аргументы командной строки:

def create_parser():
    """Список доступных параметров скрипта."""
    parser = argparse.ArgumentParser()
    parser.add_argument('file',
                        nargs='*',
                        help='Файл в формате html'
                        )
    return parser

#-------------------------------------------------------------------------
# Функции

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

def pathfinder (pathlist):
    """Возвращает абсолютный путь к файлам в каталогах или к файлам в списке."""
    filelist = [ ]
    for file_path in pathlist:
        if os.path.isfile(file_path):
            filelist.append(file_path)
        if os.path.isdir(file_path):
            files = find_files(file_path)
            for file in files:
                filelist.append(file)
    return filelist

def create_synch_database (database_name):
    """База данных sqlite, таблица постов на synch."""
    database = sqlite3.connect(metadict_path(database_name))
    cursor = database.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS posts (
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
    cursor.execute("""CREATE INDEX IF NOT EXISTS index_posts ON posts (
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

def synch_post_file_name (post):
    """Извлекаем название картинки из поста"""
    post_file_name = post.xpath('.//span[@class="unimportant"]')
    # Проверка, не пустой ли список:
    if len(post_file_name) >= 1:
        post_file_name = etree.tostring(post_file_name[0], pretty_print=True)
        # Decode HTML entities:
        post_file_name = BeautifulSoup(post_file_name, "lxml")
        # Очистка от тегов html:
        post_file_name = ''.join(re.findall('a download="(.*)">', str(post_file_name)))
        post_file_name = ''.join(re.sub(' href=.*$', '', str(post_file_name)))
        post_file_name = ''.join(re.sub('"', '', str(post_file_name)))
        return post_file_name

def synch_post_file_link (post):
    """Ссылка на картинку"""
    post_file_link = post.xpath('.//span[@class="unimportant"]')
    # Проверка, не пустой ли список:
    if len(post_file_link) >= 1:
        post_file_link = etree.tostring(post_file_link[0], pretty_print=True)
        # Очистка от тегов html:
        post_file_link = ''.join(re.findall('href="(.*)">', str(post_file_link)))
        post_file_link = ''.join(re.sub('">.*', '', str(post_file_link)))
        return post_file_link

def synch_post_file_prev (post):
    """Ссылка на превью картинки"""
    post_file_prev = post.xpath('.//img[@class="post-image"]')
    # Проверка, не пустой ли список:
    if len(post_file_prev) >= 1:
        post_file_prev = etree.tostring(post_file_prev[0], pretty_print=True)
        # Очистка от тегов html:
        post_file_prev = ''.join(re.findall('src="(.*)" ', str(post_file_prev)))
        post_file_prev = ''.join(re.findall('(.*)" ', str(post_file_prev)))
        return post_file_prev

def synch_post_theme (post):
    """Тема поста"""
    post_theme = post.xpath('.//span[@class="subject"]')
    # Проверка, не пустой ли список:
    if len(post_theme) >= 1:
        post_theme = etree.tostring(post_theme[0], pretty_print=True)
        # Decode HTML entities:
        post_theme = BeautifulSoup(post_theme, "lxml")
        # Очистка от тегов html:
        post_theme = ''.join(re.findall('class="subject">(.*)<', str(post_theme)))
        return post_theme

def synch_post_email (post):
    """Поле email"""
    post_email = post.xpath('.//a[@class="email"]')
    # Проверка, не пустой ли список:
    if len(post_email) >= 1:
        post_email = etree.tostring(post_email[0], pretty_print=True)
        # Очистка от тегов html:
        post_email = ''.join(re.sub('^.*href="','', str(post_email)))
        post_email = ''.join(re.sub(';">.*','', str(post_email)))
        return post_email

def synch_post_name (post):
    """Поле имя"""
    post_name = post.xpath('.//span[@class="name"]')
    # Проверка, не пустой ли список:
    if len(post_name) >= 1:
        post_name = etree.tostring(post_name[0], pretty_print=True)
        # Decode HTML entities:
        post_name = BeautifulSoup(post_name, "lxml")
        # Очистка от тегов html:
        post_name = ''.join(re.findall('class="name">(.*)<', str(post_name)))
        return post_name

def synch_post_trip (post):
    """Трипкод"""
    post_trip = post.xpath('.//span[@class="trip"]')
    # Проверка, не пустой ли список:
    if len(post_trip) >= 1:
        post_trip = etree.tostring(post_trip[0], pretty_print=True)
        # Decode HTML entities:
        post_trip = BeautifulSoup(post_trip, "lxml")
        # Очистка от тегов html:
        post_trip = ''.join(re.findall('class="trip">(.*)<', str(post_trip)))
        return post_trip

def synch_post_number (post):
    """Номер поста"""
    post_number = post.xpath('.//a[@class="post_no"]')
    # Проверка, не пустой ли список:
    if len(post_number) >= 1:
        post_number = post_number[1].text_content()
        return post_number

def synch_post_datetime (post):
    """Время создания поста в формате unixtime"""
    post_datetime = post.xpath('.//time')
    # Проверка, не пустой ли список:
    if len(post_datetime) >= 1:
        post_datetime = etree.tostring(post_datetime[0], pretty_print=True)
        post_datetime = ''.join(re.findall('datetime="(.*)">', str(post_datetime)))
        post_date = ''.join(re.findall('^(.*)T', str(post_datetime)))
        year = int(''.join(re.findall('^(.*)-.*-', str(post_date))))
        month = int(''.join(re.findall('^.*-(.*)-', str(post_date))))
        day = int(''.join(re.findall('^.*-.*-(.*)', str(post_date))))
        post_time = ''.join(re.findall('T(.*)Z', str(post_datetime)))
        hour = int(''.join(re.findall('^(.*):.*:', str(post_time))))
        minute = int(''.join(re.findall('^.*:(.*):', str(post_time))))
        second = int(''.join(re.findall('^.*:.*:(.*)', str(post_time))))
        datetime_object = datetime.datetime(year,month,day,hour,minute,second)
        unixtime = int(time.mktime(datetime_object.timetuple()))
        return unixtime

def synch_post_youtube_video (post):
    """Ссылка на ютуб с картинкой"""
    post_youtube_video = post.xpath('.//div[@class="video-container"]')
    # Проверка, не пустой ли список:
    if len(post_youtube_video) >= 1:
        post_youtube_video = post_youtube_video[0].xpath('.//a[@class="file"]')
        post_youtube_video = etree.tostring(post_youtube_video[0], pretty_print=True)
        youtube_video = ''.join(re.findall('a href="(.*)" target', str(post_youtube_video)))
        return youtube_video

def synch_post_youtube_image (post):
    """Ссылка на картинку к видео с ютуба"""
    post_youtube_image = post.xpath('.//div[@class="video-container"]')
    # Проверка, не пустой ли список:
    if len(post_youtube_image) >= 1:
        post_youtube_image = post_youtube_image[0].xpath('.//a[@class="file"]')
        post_youtube_image = etree.tostring(post_youtube_image[0], pretty_print=True)
        youtube_image = ''.join(re.findall('src="(.*)"', str(post_youtube_image)))
        youtube_image = 'https:' + youtube_image
        return youtube_image

def synch_post_content (post):
    """Содержимое поста"""
    post_content = post.xpath('.//div[@class="body" or @class="body media-body"]')
    # Меняем <br> на символы новой строки:
    for br in post.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    post_content = post_content[0].text_content()
    # Чистим пост от цитат и ссылок на другие посты (Так себе идея):
    post_content = ''.join(re.sub('>>([0-9]+)', '',post_content))
    post_content = ''.join(re.sub('>[^0-9]+', '',post_content))
    # Очищает пост от включений url:
    post_content = ''.join(re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '',post_content))
    # Криво-косо убираем пустые посты (а нужно сделать чисту пустых строк)
    post_test = ''.join(re.sub('\n', '',post_content))
    if post_test:
        return post_content

def synch_post_urls (post):
    """Извлекает url из поста"""
    post_urls = post.xpath('.//div[@class="body" or @class="body media-body"]')
    # Меняем <br> на символы новой строки:
    for br in post.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    post_urls = post_urls[0].text_content()
    post_urls_list = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(post_urls))
    if post_urls_list:
        return post_urls_list

def synch_post_citation (post):
    """Цитаты из содержимого поста"""
    post_citation = post.xpath('.//div[@class="body" or @class="body media-body"]')
    # Меняем <br> на символы новой строки:
    for br in post.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    post_citation = post_citation[0].text_content()
    #post_citation = ' '.join(re.findall("^>>[0-9]+", str(post_citation)))
    # Находит цитаты кроме начинающихся с цифры:
    post_citation_list = re.findall(">[a-zA-Zа-яёЁА-Я].*", str(post_citation))
    if post_citation_list:
        return post_citation_list

def synch_post_links (post):
    """Ссылки на другие посты"""
    post_links = post.xpath('.//div[@class="body" or @class="body media-body"]')
    # Меняем <br> на символы новой строки:
    for br in post.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    post_links = post_links[0].text_content()
    post_links_list = re.findall(">>([0-9]+)", str(post_links))
    if post_links_list:
        return post_links_list

def synch_thread_parser_dict (thread):
    """Тред на синче разбиваетсяна посты, все поля постов переносятся в словарь"""
    # Проблема: картинки из оп-постов не получается вытащить (они выше тега оп-поста).
    metadict_thread = {}
    posts = thread.xpath('.//div[@class="post op" or @class="post reply row" or @class="post reply"]')
    # Проверка, есть ли посты в треде:
    if not posts:
        print('Парсер не нашёл постов:', file_path)
        return None
    thread_number = synch_post_number(posts[0])
    post_number = 0
    for post in posts:
        post_dict = {}
        # Ненулевые значения, должны быть заданы числами:
        post_dict['thread_number'] = thread_number
        post_dict['thread_post_number'] = post_number
        post_dict['post_number'] = synch_post_number(post)
        post_dict['post_datetime'] = synch_post_datetime(post)
        # Заполняемые пользователем поля (бойся sql-injection!):
        post_dict['post_theme'] = synch_post_theme(post)
        post_dict['post_email'] = synch_post_email(post)
        post_dict['post_name'] = synch_post_name(post)
        post_dict['post_trip'] = synch_post_trip(post)
        post_dict['post_file_name'] = synch_post_file_name(post)
        post_dict['post_file_link'] = synch_post_file_link(post)
        post_dict['post_file_prev'] = synch_post_file_prev(post)
        post_dict['post_youtube_video'] = synch_post_youtube_video(post)
        post_dict['post_youtube_image'] = synch_post_youtube_image(post)
        # Содержимое поста, обработка:
        post_dict['post_content'] = synch_post_content(post)
        post_dict['post_citation'] = synch_post_citation(post)
        post_dict['post_urls'] = synch_post_urls(post)
        # Предельно аккуратная обработка ссылок на другие посты (задавай числами):
        post_dict['post_links'] = synch_post_links(post)
        metadict_thread[post_number] = post_dict
        post_number = post_number + 1
    return metadict_thread

def synch_thread_sqlite (database_name, metadict_thread):
    """Словарь треда переносится в базу данных."""
    # Создаётся база данных, если её нет:
    if os.path.exists(metadict_path(database_name)) is not True:
        create_synch_database(database_name)
    # Проверка, сработал ли парсер:
    if not metadict_thread:
        return None
    # Подключается база данных:
    database = sqlite3.connect(metadict_path(database_name))
    cursor = database.cursor()
    # Список отброшенных постов (уникальные номера не перезаписываются):
    drop_posts = [ ]
    for post,post_dict in metadict_thread.items():
        # Обработка словаря
        post_number = int(post_dict["post_number"])
        thread_number = int(post_dict["thread_number"])
        thread_post_number = int(post_dict["thread_post_number"])
        post_datetime = int(post_dict["post_datetime"])
        post_theme = post_dict["post_theme"]
        post_email = post_dict["post_email"]
        post_name = post_dict["post_name"]
        post_trip = post_dict["post_trip"]
        post_file_name = post_dict["post_file_name"]
        post_file_link = post_dict["post_file_link"]
        post_file_prev = post_dict["post_file_prev"]
        post_youtube_video = post_dict["post_youtube_video"]
        post_youtube_image = post_dict["post_youtube_image"]
        post_content = post_dict["post_content"]
        if post_dict["post_citation"]:
            post_citation = str(' '.join(post_dict["post_citation"]))
        else:
            post_citation = None
        if post_dict["post_urls"]:
            post_urls = str(' '.join(post_dict["post_urls"]))
        else:
            post_urls = None
        if post_dict["post_links"]:
            post_links = str(' '.join(post_dict["post_links"]))
        else:
            post_links = None
        # Надо использовать именованные переменные (но пока сойдёт):
        try:
            cursor.execute("INSERT INTO posts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [\
                post_number,\
                thread_number,\
                thread_post_number,\
                post_datetime,\
                post_theme,\
                post_email,\
                post_name,\
                post_trip,\
                post_file_name,\
                post_file_link,\
                post_file_prev,\
                post_youtube_video,\
                post_youtube_image,\
                post_content,\
                post_citation,\
                post_urls,\
                post_links,\
                ])
        except sqlite3.IntegrityError:
            drop_posts.append(post_number)
    if drop_posts:
        print('Посты уже в БД:',len(drop_posts),file_path)
    database.commit()
    database.close()

#----------------------------------------------------------------------
# Тело программы:

# Создаётся список аргументов скрипта:
parser = create_parser()
namespace = parser.parse_args()
# Проверяем, существует ли указанные файлы/файл:
found_threads = find_files(metadict_path(threads_dir))
# Если указаны файлы:
if namespace.file:
    filelist = pathfinder(namespace.file)
    for n,file_path in enumerate(filelist,1):
        print(n, '/', len(filelist), file_path)
        thread = file_path
        thread_raw = lxml.html.parse(file_path).getroot()
        synch_thread_sqlite(database_name, synch_thread_parser_dict(thread_raw))
# Если файла нет, берём все файлы из стандартного каталога (если он не пуст):
elif not namespace.file and found_threads:
    for n,file_path in enumerate(found_threads,1):
        print(n, '/', len(found_threads), file_path)
        thread = file_path
        thread_raw = lxml.html.parse(file_path).getroot()
        synch_thread_sqlite(database_name, synch_thread_parser_dict(thread_raw))
# Если и в каталоге тредов ничего нет, читаем стандартный ввод:
else:
    print('Не указан файл, нет файлов в каталоге, читаем стандартный ввод')
    thread = lxml.html.fromstring(sys.stdin.read())
    synch_thread_sqlite(database_name, synch_thread_parser_dict(thread))

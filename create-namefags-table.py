#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Скрипт создаёт таблицу неймфагов в synch.sqlite

import os
import sqlite3

#-------------------------------------------------------------------------
# Опции:

database_dir = 'database/'
database_name = 'database/synch.sqlite'

#-------------------------------------------------------------------------
# Функции

def metadict_path (metadict_dir):
    """Возвращает абсолютный путь к каталогу словарей."""
    # Получаем абсолютный путь к каталогу скрипта:
    script_path = os.path.dirname(os.path.abspath(__file__))
    # Добавляем к пути каталог словарей:
    metadict_path = script_path + '/' + metadict_dir
    return metadict_path

def create_namelist_super_fast_pro_gleam_shady_algorithm (cursor):
    """Список всех сочетаний имён и трипкодов."""
    # Для начала загружаем имена и трипкоды в отдельные списки:
    names = cursor.execute("SELECT DISTINCT (post_name) FROM posts").fetchall()
    tripcodes = cursor.execute("SELECT DISTINCT (post_trip) FROM posts").fetchall()
    # Узнаём, какие имена относятся к трипкоду:
    namelist = [ ]
    print('Создаётся список трипкодов и связанных с ними имён:')
    for n,tripcode in enumerate(tripcodes,1):
        trip_names = cursor.execute(\
                "SELECT DISTINCT (post_name) FROM posts WHERE post_trip=?"\
                ,(tripcode[0],)).fetchall()
        for name in trip_names:
            nametuple = (name[0], tripcode[0])
            if tripcode[0] is not None:
                namelist.append(nametuple)
        print (n, '/', len(tripcodes), tripcode)
    # А теперь перебираем имена без трипкодов:
    print('Создаётся список имён без трипкодов:')
    for n,name in enumerate(names,1):
        notrip_name = cursor.execute(\
                "SELECT DISTINCT (post_trip) FROM posts WHERE post_name=? AND post_trip IS NULL"\
                ,(name[0],)).fetchall()
        if notrip_name:
            nametuple = (name[0], None)
            namelist.append(nametuple)
            print (n, '/', len(names), name)
    return(namelist)

def create_namelist_lazy_greedy_pegasus_algorithm (cursor):
    """Список всех сочетаний имён и трипкодов."""
    # А вот не нужно было делать циклы в циклах. 2 триллиона запросов, это не шутки!
    # Для начала загружаем имена и трипкоды в отдельные списки:
    names = cursor.execute("SELECT DISTINCT (post_name) FROM posts").fetchall()
    tripcodes = cursor.execute("SELECT DISTINCT (post_trip) FROM posts").fetchall()
    namelist = [ ]
    print('Создаётся список сочетаний имён-трипкодов:')
    # Цикл с нумерацией вывода (для удобства и красоты):
    for n,name in enumerate(names,1):
        for trip in tripcodes:
            # Сначала выбираем трипфагов, то есть любые имена + наличие трипкода:
            nametrip = cursor.execute("SELECT DISTINCT (post_trip) FROM posts WHERE post_name=? AND post_trip=?",(name[0],trip[0],)).fetchall()
            if len(nametrip) > 0:
                tuple = (name[0],nametrip[0][0])
                namelist.append(tuple)
                print(n, '/', len(names), tuple)
        # А затем заносим в базу данных чистых неймфагов с NULL в трипкоде:
        name_clear = cursor.execute("SELECT DISTINCT (post_trip) FROM posts WHERE post_name=? AND post_trip IS NULL",(name[0],)).fetchall()
        if len(name_clear) > 0 and name_clear[0][0] is None:
            tuple = (name[0],None)
            namelist.append(tuple)
            print(n, '/', len(names), tuple)
    return namelist

def recreate_namefags_table (cursor):
    """Создаёт или пересоздаёт таблицу неймфагов."""
    # Дропаем старую таблицу:
    cursor.execute("DROP TABLE IF EXISTS namefags")
    cursor.execute("""CREATE TABLE IF NOT EXISTS namefags (
        number INTEGER NOT NULL PRIMARY KEY UNIQUE,
        name TEXT DEFAULT NULL,
        tripcode TEXT DEFAULT NULL,
        postcount INTEGER NULL,
        posts TEXT DEFAULT NULL,
        links TEXT DEFAULT NULL
        )""")
    cursor.execute("""CREATE INDEX IF NOT EXISTS index_namefags ON namefags (
        number,
        name,
        tripcode,
        postcount,
        posts,
        links
        )""")
    # Заполняем таблицу сочетаниями имён-трипкодов (остальные значения пока что нули):
    namelist = create_namelist_super_fast_pro_gleam_shady_algorithm(cursor)
    for n,nametuple in enumerate(namelist,1):
        cursor.execute("INSERT INTO namefags VALUES(?,?,?,NULL,NULL,NULL)", (n,nametuple[0],nametuple[1],))
    database.commit()
    print("[OK] CREATE",database_name)

def gen_postcount (cursor, nametuple):
    """Записывает в базу данных число постов неймфагов."""
    if nametuple[-1] is None:
        postcount = cursor.execute(\
                "SELECT COUNT(post_number) FROM posts WHERE post_name=? AND post_trip IS NULL"\
                ,(nametuple[0],)).fetchall()
        postcount = int(postcount[0][0])
        cursor.execute("UPDATE namefags SET postcount=? WHERE name=? AND tripcode IS NULL"\
                ,(postcount,nametuple[0],)).fetchall()
    else:
        postcount = cursor.execute(\
                "SELECT COUNT(post_number) FROM posts WHERE post_name=? AND post_trip=?"\
                ,(nametuple)).fetchall()
        postcount = int(postcount[0][0])
        cursor.execute("UPDATE namefags SET postcount=? WHERE name=? AND tripcode=?"\
                ,(postcount,nametuple[0],nametuple[1],)).fetchall()

def gen_posts_list (cursor,nametuple):
    """Записывает в базу данных номера неймфажьих постов."""
    if nametuple[-1] is None:
        postlist = cursor.execute(\
                "SELECT post_number FROM posts WHERE post_name=? AND post_trip IS NULL"\
                ,(nametuple[0],)).fetchall()
        # Кортежи в строчные элементы списка:
        postlist = [str(i[0]) for i in postlist]
        # А список в строку:
        postlist = ' '.join(postlist)
        cursor.execute("UPDATE namefags SET posts=? WHERE name=? AND tripcode IS NULL"\
                ,(postlist,nametuple[0],)).fetchall()
    else:
        postlist = cursor.execute(\
                "SELECT post_number FROM posts WHERE post_name=? AND post_trip=?"\
                ,(nametuple)).fetchall()
        postlist = [str(i[0]) for i in postlist]
        postlist = ' '.join(postlist)
        cursor.execute("UPDATE namefags SET posts=? WHERE name=? AND tripcode=?"\
                ,(postlist,nametuple[0],nametuple[1],)).fetchall()

def gen_link_list (cursor,nametuple):
    """Записывает в базу данных ссылки неймфага на другие посты."""
    if nametuple[-1] is None:
        linklist = cursor.execute(\
                "SELECT post_links FROM posts WHERE post_links IS NOT NULL AND post_name=? AND post_trip IS NULL"\
                ,(nametuple[0],)).fetchall()
        linklist = [str(i[0]) for i in linklist]
        if len(linklist) == 0:
            linklist = None
        else:
            linklist = ' '.join(linklist)
        cursor.execute("UPDATE namefags SET links=? WHERE name=? AND tripcode IS NULL"\
                ,(linklist,nametuple[0],)).fetchall()
    else:
        linklist = cursor.execute(\
                "SELECT post_links FROM posts WHERE post_links IS NOT NULL AND post_name=? AND post_trip=?"\
                ,(nametuple)).fetchall()
        linklist = [str(i[0]) for i in linklist]
        if len(linklist) == 0:
            linklist = None
        else:
            linklist = ' '.join(linklist)
        cursor.execute("UPDATE namefags SET links=? WHERE name=? AND tripcode=?"\
                ,(linklist,nametuple[0],nametuple[1],)).fetchall()

def database_test (cursor,nametuple):
    """Проверяет postcount на значение NULL (чтобы не начинать всё заново в случае прерывания)"""
    if nametuple[-1] is None:
        database_test = cursor.execute("SELECT postcount FROM namefags WHERE postcount IS NOT NULL AND name=? AND tripcode IS NULL"\
                ,(nametuple[0],)).fetchall()
    else:
        database_test = cursor.execute("SELECT postcount FROM namefags WHERE postcount IS NOT NULL AND name=? AND tripcode=?"\
                ,(nametuple[0],nametuple[1],)).fetchall()
    if database_test:
        return True

def fill_namefags_table (cursor):
    """Добавляем значения в таблицу. Последовательно, с возможностью прерывания, это долгий процесс."""
    try:
        namelist = cursor.execute("SELECT name,tripcode FROM namefags").fetchall()
    except sqlite3.OperationalError:
        recreate_namefags_table(cursor)
        namelist = cursor.execute("SELECT name,tripcode FROM namefags").fetchall()
    # Цикл с нумерацией вывода (для удобства и красоты):
    for n,nametuple in enumerate(namelist,1):
        # Проверка на случай прерывания:
        if database_test(cursor,nametuple) is not True:
            gen_posts_list(cursor,nametuple)
            gen_link_list(cursor,nametuple)
            gen_postcount(cursor,nametuple)
            database.commit()
            print(n, '/', len(namelist), nametuple)
    print("[OK] INSERT",database_name)

#-------------------------------------------------------------------------
# Тело программы:

# Подключение к базе данных:
database = sqlite3.connect(metadict_path(database_name))
cursor = database.cursor()

# Основная функция:
fill_namefags_table(cursor)

# Отключаемся от базы данных:
database.close()

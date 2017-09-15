#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Скрипт строит граф социальных связей по ссылкам между постами:

import os
import sqlite3
import graphviz
from datetime import datetime

#-------------------------------------------------------------------------
# Опции:

# Вывод в файл:
IMG = 'output/img'
# Выборка по количеству постов:
POSTCOUNT_MIN = 500
POSTCOUNT_MAX = 1000000
# Процент ссылок от общего числа:
FRIENDSHIP_LVL = 1
# Список в формате: (имя, трипкод),
IGNORE_NAMES = [
        ('Аноним',None),
        ]
database_name = './database/synch.sqlite'

# Настройки вывода через grahviz (circo для малой выборки, twopi для большой):
graph_engine = 'circo'
#graph_engine = 'twopi'
graph_output = 'png'
graph_conf = {
        'mindist':'2.5',
        'overlap':'scale',
        #'splines':'true',
        #'spines':'spline',
        #'concentrate':'true',
        }
node_conf = {
        'shape':'circle',
        'fixedsize':'True',
        'width':'2',
        'style':'filled',
        'penwidth':'0.5',
        }
edge_conf = {
        'arrowsize':'0.5',
        #'arrowshape':'vee',
        }

#-------------------------------------------------------------------------
# Функции:

def metadict_path (metadict_dir):
    """Возвращает абсолютный путь к каталогу словарей."""
    # Получаем абсолютный путь к каталогу скрипта:
    script_path = os.path.dirname(os.path.abspath(__file__))
    # Добавляем к пути каталог словарей:
    metadict_path = script_path + '/' + metadict_dir
    return metadict_path

def nametrip_to_string (nametrip):
    name_number = nametrip[0]
    name_postcount = cursor.execute("SELECT postcount FROM namefags WHERE number=?"\
            ,(name_number,)).fetchall()
    if nametrip[2] is not None:
        nametrip_string = '\n'.join(nametrip[1:3])+'\n\n'+str(name_postcount[0][0])
    else:
        nametrip_string = nametrip[1]+'\n\n'+str(name_postcount[0][0])
    return nametrip_string

def namefags_select(cursor,POSTCOUNT_MIN,POSTCOUNT_MAX,IGNORE_NAMES):
    """Собирает данные неймфагов с выборкой по минимальному числу постов."""
    namefags_select = [ ]
    namefags = cursor.execute("SELECT number,name,tripcode,posts,links,postcount FROM namefags").fetchall()
    for nametuple in namefags:
        postcount = nametuple[5]
        nametrip = nametuple[0:3]
        if postcount > POSTCOUNT_MIN and postcount < POSTCOUNT_MAX and nametrip[1:3] not in IGNORE_NAMES:
            namefags_select.append(nametuple)
    return namefags_select

def friend_score(cursor,nametuple,namefags):
    """Определяет число ссылок неймфага на посты других неймфагов, вычислет процент от общего числа ссылок."""
    score_dict = {}
    # Процент обработанных ссылок(для проверки):
    percent_sum = 0
    # Сначала смотрим, на какие посты ссылается наш неймфаг:
    if nametuple[4] is not None:
        links_cloud = nametuple[4].split()
        linkcount = len(links_cloud)
    else:
        links_cloud = None
        linkcount = 0
    # Берём срез из базы данных и перебираем неймфагов поочерёдно:
    for subject in namefags:
        nametrip = subject[0:3]
        post_cloud = subject[3].split()
        # Отбрасываем ссылки на самого себя:
        if nametuple[0:3] != nametrip and links_cloud is not None:
            # Сравниваем списки, находим одинаковые посты:
            equal_list = list(set(links_cloud) & set(post_cloud))
            if equal_list:
                score = len(equal_list)
                # Нас интересует не число ссылок на другого неймфага, а процент ссылок от общего числа.
                percent_score = round(score / linkcount * 100, 3)
                if int(percent_score) > FRIENDSHIP_LVL:
                    percent_sum = percent_sum + percent_score
                    #percent_score = '{0:.0%}'.format(score/linkcount)
                    score_dict[nametrip] = percent_score
                    #print(nametuple,nametrip,percent_score)
    #print(percent_sum)
    return score_dict

def collect_friends(cursor):
    """Создаётся метасловарь неймфагов и их друзей."""
    metadict_friends = {}
    namefags = namefags_select(cursor,POSTCOUNT_MIN,POSTCOUNT_MAX,IGNORE_NAMES)
    for n,nametuple in enumerate(namefags,1):
        nametrip = nametuple[0:3]
        metadict_friends[nametrip] = friend_score(cursor,nametuple,namefags)
        print(n, '/', len(namefags), nametrip)
    return metadict_friends

def postcount_test(metadict_friends):
    """Среднее число постов по выборке, чтобы выделить активных/неактивных неймфагов."""
    all_postcount = 0
    for namefag in metadict_friends.keys():
        name_number = namefag[0]
        name_postcount = cursor.execute("SELECT postcount FROM namefags WHERE number=?"\
                ,(name_number,)).fetchall()
        all_postcount = all_postcount + int(name_postcount[0][0])
    name_number = len(metadict_friends)
    medial_postcount = all_postcount / name_number
    return medial_postcount,all_postcount

def graphviz_test(metadict_friends):
    """Создаётся граф социальных связей. Ужасный код, нужно отделить вывод графики и вызовы бд."""
    # Для начала создаём проект и подключаем опции graphviz:
    dot = graphviz.Digraph(\
            format=graph_output, engine=graph_engine, graph_attr=graph_conf,\
            node_attr=node_conf, edge_attr=edge_conf,\
            )
    # Общее и усреднённое число постов:
    all_postcount = postcount_test(metadict_friends)[1]
    medial_postcount = postcount_test(metadict_friends)[0]
    # Создаём ноды, поочерёдно перебирая неймфагов из словаря:
    hsv_color = 0
    for namefag in metadict_friends.keys():
        name_number = namefag[0]
        name = namefag[1]
        trip = namefag[2]
        # Имя ноды, это имя неймфага + трипкод + число постов.
        node_name = nametrip_to_string(namefag)
        # Толщина обводки, текста и размер ноды -- относительное число постов:
        name_postcount = cursor.execute("SELECT postcount FROM namefags WHERE number=?"\
                ,(name_number,)).fetchall()
        node_strength = str(int(name_postcount[0][0]) / medial_postcount + 1)
        font_strength = str(float(node_strength) * 10)
        # Цвет в формате HSV, шаг зависит от числа неймфагов в словаре:
        hsv_color = round(hsv_color + 1 / len(metadict_friends),4)
        hsv_border=str(hsv_color)+','+'1'+','+'1'
        # Насыщенность цвета зависит от числа постов, меньше -- бледнее:
        hsv_saturation = str(int(name_postcount[0][0]) / all_postcount * 3)
        hsv_fill=str(hsv_color)+','+str(hsv_saturation)+','+'1'
        # Выделяем трипфагов двойной обводкой:
        if trip is not None:
            dot.node(node_name, color=hsv_border, fillcolor=hsv_fill, fontsize=font_strength,\
                    width=node_strength, penwidth=node_strength, shape='doublecircle')
        else:
            dot.node(node_name, color=hsv_border, fillcolor=hsv_fill, fontsize=font_strength,\
                    width=node_strength, penwidth=node_strength)
    # Создаём линии связей, поочерёдно перебирая друзей каждого неймфага:
    hsv_color = 0
    for namefag,dict_friends in metadict_friends.items():
        name_number = namefag[0]
        # Опять же, насыщенность цвета зависит от числа постов:
        name_postcount = cursor.execute("SELECT postcount FROM namefags WHERE number=?"\
                ,(name_number,)).fetchall()
        hsv_color = round(hsv_color + 1 / len(metadict_friends),4)
        hsv_saturation = str(int(name_postcount[0][0]) / all_postcount * 3)
        hsv=str(hsv_color)+','+hsv_saturation+','+'1'
        #print(hsv)
        for friend,score in dict_friends.items():
            node_name = nametrip_to_string(namefag)
            friend_name = nametrip_to_string(friend)
            # А вес связи, это доля от общего числа постов, предназначенная другу:
            connect_value = str(round(score,2))
            dot.edge(node_name, friend_name, color=hsv, penwidth=connect_value)
    # Вывод данных в формате dor:
    print(dot.source)
    # Генерация схемы:
    img = metadict_path(IMG)
    print(dot.render(filename=img))

#-------------------------------------------------------------------------
# Тело программы:

# Подключение к базе данных:
database = sqlite3.connect(metadict_path(database_name))
cursor = database.cursor()

# Основные функции:
metadict_friends = collect_friends(cursor)
if len(metadict_friends) > 0:
    graphviz_test(metadict_friends)
else:
    print('Проверь опции, недостаточно неймфагов.')

# Отключаемся от базы данных:
database.close()

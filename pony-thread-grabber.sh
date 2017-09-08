#!/bin/sh

# Скрипт загружает цепочку пони-тредов с синча. Единственный параметр — ссылка на тред.
# bash ~/my-documents/scripts/pony-thread-grabber.sh 'http://syn-ch.com/b/res/4116392.html'
# Записывает треды в текущий каталог.

thread=$1
board='http://syn-ch.com/b'
# Извлекаем номер треда из ссылки:
thread=`echo $thread | sed 's/arch/res/g'`
thread_number=`echo $thread | sed 's$^.*/b/res/$$g' | sed 's$#.*$$g' | sed 's$.html$$g'`

a=0
while [ $a -lt 300 ]
do
    proxychains curl -L -A 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0' $thread > ./$thread_number.html  2>/dev/null
    # Извлекаем номер прошлого треда из первого поста:
    #thread_next=`cat ./$thread_number.html | egrep -o '<div class="post op" id="reply_[0-9]+">.*</div></div><div class="post reply row" id="reply_[0-9]+">' | egrep -o '&gt;&gt;[0-9]+' | sed 's$&gt;&gt;$$'`
    #thread_next=`cat ./$thread_number.html | egrep -o '<div class="post op" id="reply_[0-9]+">.*</div></div><div class="(post reply row)|(post reply)" id="reply_[0-9]+">' | egrep -o '&gt;&gt;[0-9]+' | sed 's$&gt;&gt;$$'`
    thread_next=`cat ./$thread_number.html | egrep -o '<div class="post op".*</div></div><div class="(post reply row)|(post reply)"' | egrep -o '[0-9]{6,}' | tail -n 1`

    if [ -z $thread_next ]
        then
            echo 'Ошибка: thread_next пуст (ожидание 1 min)'
            sleep 1m
        else
            # Номер треда для вывода:
            thread_number=$thread_next
            # Создание ссылки
            thread_link=`echo "/res/$thread_next.html"`
            # Корректируем ссылку на тред:
            thread=$board$thread_link
            echo $thread
	        a=$(( $a + 1 ))
    fi
done

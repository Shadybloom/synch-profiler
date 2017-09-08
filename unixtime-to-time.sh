#!/usr/bin/env bash
# unixtime to time

IFS=$'\n'
ARRAY_NODES=( `cat  $1`  )

number=0
max_numbers=${#ARRAY_NODES[@]}
while [ $number -lt $max_numbers ]
do
    unixtime=${ARRAY_NODES[$number]}
    time=`date -d @"$unixtime"`
    echo "$time"
    number=$(( $number + 1 ))
done

#!/bin/bash
start=0

_arg1=$1
_file="./stock_data/$_arg1.csv"
_date="${_arg1:0:4}-${_arg1:4:2}-${_arg1:6:2}"
# echo $_date
# echo $_file
while IFS=, read code _time accumu price volume _rest; do
    if [[ "$_time" == "0900"* ]] ; then
        start=1
    fi
    if [[ $start -eq 1 ]] ; then
        _ptime="$_date ${_time:0:2}:${_time:2:2}:${_time:4:2}"
        _millsec="${_time:6}"
        epoch=$(date -d "$_ptime" +%s)
        epoch="$epoch$_millsec"
        if [[ $volume -ne 0  ]]; then
            echo "$code $price $volume $accumu $epoch $_time"
        fi
    fi
    
done < $_file
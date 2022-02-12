#!/bin/bash
cd /home/kctsai/fintech/microcast/upload
export $(cat .env | sed 's/#.*//g' | xargs)
_date=$(date +'%Y%m%d')
tail_result=$(tail ../stock_data/"$_date".csv -n 1 | awk -F, '{print $2}');
if [[ $tail_result == 13* ]]; then
    echo "$_date ok " >> ../log/stock.log
    ./clean $_date > ./insert/"$_date".csv
    echo "influx write -t=$INFLUX -o $ORG -b $DB -f ./insert/$_date.csv"
    influx write -t=$INFLUX -o $ORG -b $DB -f ./insert/"$_date".csv
    ./to_minutes.py $_date
    cd /home/kctsai/fintech/trend_stationary
    /home/kctsai/fintech/trend_stationary/main.py $_date
    /home/kctsai/fintech/trend_stationary/converge.py $_date
    influx write -t=$INFLUX -o $ORG -b converge -f ./converge_data/"$_date".csv
    cd /home/kctsai/fintech/WebPairTrade/myTools/pairstrading
    /home/kctsai/fintech/WebPairTrade/myTools/pairstrading/main.py $_date
    
else
    echo "$_date missing" >> ../log/stock.log
fi
cd -

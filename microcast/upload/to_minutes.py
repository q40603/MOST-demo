#!/home/kctsai/miniconda3/envs/demo/bin/python
import pandas as pd 
import sys
import json
from datetime import datetime
import requests
import os


os.chdir("/home/kctsai/fintech/microcast/upload")
_file = "./insert/" + sys.argv[1] + ".csv"
_date = sys.argv[1]
min_path = "/home/kctsai/fintech/pair_data/" + _date[:4] + "/averageprice"
tick_path = "/home/kctsai/fintech/pair_data/" + _date[:4] + "/minprice"


punish_list = []
try:
    para = {
        "response": "json",
        "startDate": _date,
        "endDate": _date
    }
    twse_puninsh_url = "https://www.twse.com.tw/announcement/punish"
    punish = requests.get(url = twse_puninsh_url, params = para)
    if(punish.status_code == 200):
        punish_list = [i[2] for i in punish.json()["data"]]
    else:
        raise Exception("bad crawling response etf punish list")

except Exception as e:
    print(e)


dt = {'price': float, "vol" : float, "acc_vol": float, "time": int, "m" : str}
data = pd.read_csv(_file, sep="," , skiprows=1, dtype=dt, parse_dates=['time'], date_parser=lambda epoch: pd.to_datetime(epoch, unit='ns'))
data = data[~data["m"].isin(punish_list)]

tick_data = data.copy()


data["time"] = data["time"].dt.round('1min')
min_data = data.groupby(["time","m"]).apply(lambda x: (x['price'] * x['vol']).sum() / x["vol"].sum())
min_data = min_data.unstack().resample('1min').interpolate().bfill().ffill()
min_data = min_data.reset_index(drop=True)
min_data.to_csv("{}/{}_averagePrice_min.csv".format(min_path,_date), index=False)


tick_data["time"] = tick_data["time"].dt.round('15s')
tick_data = tick_data.groupby(["time","m"])["price"].nth(0) 
tick_data = tick_data.unstack().resample('15s').bfill().ffill().bfill()
tick_data = tick_data.reset_index(drop=True)
tick_data = tick_data[tick_data.index%4==1]
tick_data.to_csv("{}/{}_min_stock.csv".format(tick_path,_date), index=False)




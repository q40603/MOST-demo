#!/home/kctsai/miniconda3/envs/micro/bin/python
import MicroCast
import requests
import json
from datetime import datetime
import os

os.chdir("/home/kctsai/fintech/microcast/receive")

_date = datetime.now().strftime("%Y%m%d")




cmoney_url = "https://www.cmoney.tw/etf/ashx/e210.ashx"
query_0050 = dict(
    action = "GetShareholdingDetails",
    stockId = "0050"
)

query_0051 = dict(
    action = "GetShareholdingDetails",
    stockId = "0051"
)

etf_50_list = []

try:
    etf_50_resp = requests.get(url = cmoney_url, params = query_0050)
    if etf_50_resp.status_code == 200:
        etf_50 = etf_50_resp.json()["Data"]
        with open('0050.json', 'w') as f:
            json.dump(etf_50, f)
    else:
        raise Exception("bad crawling response etf 0050.")

except Exception as e:
    print(e)
    with open("0050.json") as json_50:
        etf_50 = json.load(json_50)

finally:
    etf_50_list = [i["CommKey"] for i in etf_50 if i["Type"]=="股票"]
    #print(etf_50_list)


etf_51_list = []

try:
    etf_51_resp = requests.get(url = cmoney_url, params = query_0051)
    if etf_51_resp.status_code == 200:
        etf_51 = etf_51_resp.json()["Data"]
        with open('0051.json', 'w') as f:
            json.dump(etf_51, f)
    else:
        raise Exception("bad crawling response etf 0051.")

except Exception as e:
    print(e)
    with open("0051.json") as json_51:
        etf_51 = json.load(json_51)

finally:
    etf_51_list = [i["CommKey"] for i in etf_51 if i["Type"]=="股票"]
    #print(etf_51_list)

c_list = etf_50_list + etf_51_list
l = len(c_list)
# c_list = "|".join(c_list)

# try:
s=MicroCast.MicroCast_Login('nctu1', 'nctu1', 'ego.haohaninfo.com', 'ego.haohaninfo.com:7501', 'ego.haohaninfo.com', 'ego.haohaninfo.com')
# print(s.user_permission)
for k in range(0, l, 10):
    _file = open("../stock_data/{}_past{}.csv".format(_date, k//10),"w")
    cur_c_list = "|".join(c_list[k:k+10])
    print(cur_c_list, end=" .................", flush=True)
    data = MicroCast.MicroCast_Set(cur_c_list,'Stock','F06',True)
    for i in data.recover_some_days_ago():
        for j in i:
            # print(j,end=",")
            print(j, end=",", file=_file)
        print("", file=_file)
        #print(_date, file=_file)
    print(" done")
# except Exception as e:
#     print(e)

#!/home/kctsai/miniconda3/envs/demo/bin/python
import requests
from bs4 import BeautifulSoup as bs
import json
import time
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from copy import copy
import os
client = MongoClient("mongodb://127.0.0.1:27017/")
news_db = client["News"]

os.chdir("/home/kctsai/fintech/microcast/receive/")

etf_50_list = []
with open("0050.json") as json_50:
    etf_50 = json.load(json_50)

etf_50_list = [i["CommKey"] for i in etf_50 if i["Type"]=="股票"]

with open("0051.json") as json_51:
    etf_51 = json.load(json_51)
etf_51_list = [i["CommKey"] for i in etf_51 if i["Type"]=="股票"]

c_list = etf_50_list + etf_51_list
print(c_list)


headers = {
    'user-agent': 'Mozilla/5.0',
    "accept" : "*/*",
    "cookie": "B=5jlo9gdfku14t&b=3&s=li",
    "accept-encoding": "gzip, deflate, br",
    'Host': 'tw.stock.yahoo.com'
}

for c in c_list:
    cid = f'c_{c}'
    url = f'https://tw.stock.yahoo.com/rss?s={c}'
    rss_result = requests.get(url,headers=headers)
    a = bs(rss_result.text, 'lxml')
    tmp = a.findAll("item")
    insert_data = []
    for i in tmp:
        url = i.text.split("html")[0] + "html"
        if news_db[cid].find({'url': { "$in": [url]}}).count():
            continue
        sub_page = requests.get(url)
        sub_soup = bs(sub_page.text, 'html.parser')
        title = sub_soup.find("h1", {"data-test-locator": "headline"}).text
        content = sub_soup.find("div",{"class":"caas-body"}).text
        provider = sub_soup.find("span",{"class": "caas-attr-provider"}).text
        pubtime  = sub_soup.find("time")["datetime"]
        pubtime = datetime.strptime(pubtime,"%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours = 8)
        data = {
            "url" : url,
            "pubtime" : pubtime,
            "source" : provider,
            "title" : title,
            "content" : content,
        }
        news_db[cid].insert(copy(data))
        time.sleep(1)
    time.sleep(2)

    

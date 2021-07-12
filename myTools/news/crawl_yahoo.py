import requests
from bs4 import BeautifulSoup as bs

url = "https://tw.stock.yahoo.com/news/%E5%8F%B0%E7%A9%8D%E9%9B%BB-%E8%96%AA-%E6%83%85%E5%A5%BD-%E7%A2%A9%E5%A3%AB%E7%95%A2%E5%B9%B4%E8%96%AA180%E8%90%AC-%E5%B9%B3%E5%9D%87%E6%9C%88%E6%94%B6%E9%80%BE%E5%9F%BA%E6%9C%AC%E5%B7%A5%E8%B3%874%E5%80%8D-030500151.html"
a = requests.get(url)
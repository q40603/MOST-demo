#!/usr/bin/python3

from requests import get
from bs4 import BeautifulSoup as bs
import cgi
import json
from urllib.parse import unquote
import datetime
import sys
import time

def yahoo(content, stock):
    b = bs(get('https://tw.stock.yahoo.com/q/h?s=' + stock).text, 'lxml')
    for page in range(1, 1 + int(b.find('span', class_='mtext').text.split()[1])):
        b = bs(get('https://tw.stock.yahoo.com/q/h?s=%s&pg=%d' % (stock, page)).text, 'lxml')
        for i in b.find('table',{'width':'100%'}).findAll('tr')[::2]:
            try:
                url = unquote('https://tw.stock.yahoo.com/' + i.find('a')['href'])
                title = i.text.split('\n')[2]
                B = bs(get(url).text, 'lxml')
                time = B.find('time')['datetime']
                text = ' '.join(j.text for j in B.findAll('p'))
                content.append({'url': url, 'title': title, 'time': time, 'text': text})
            except:
                pass

def ctee(content, stock):
    b = bs(get('https://ctee.com.tw/tag/' + stock).text, 'lxml')
    try:
        pages = int(b.findAll('a', class_='page-numbers')[-2].text)
    except:
        pages = 1
    for page in range(1, 1 + pages):
        b = bs(get('https://ctee.com.tw/tag/%s/page/%d' % (stock, page)).text, 'lxml')
        for i in b.findAll('article'):
            title = i.find('h2').text.replace('\n', '').replace('\t', '')
            url = i.find('h2').find('a')['href']
            time = i.find('time')['datetime']
            excerpt = i.find('div', class_='post-summary').text.strip()
            B = bs(get(url).text, 'lxml')
            text = ' '.join(j.text for j in B.find('div', class_='entry-content clearfix single-post-content').findAll('p'))
            content.append({'url': url, 'title': title, 'time': time, 'text': text})

def udn(content, stock):
    b = bs(get('https://money.udn.com/search/tagging/1001/' + stock).text, 'lxml')
    for page in range(1, 1 + int(b.find(class_='total').text.split()[1])):
        b = bs(get('https://money.udn.com/search/tagging/1001/%s/%d' % (stock, page)).text, 'lxml')
        for i in b.find(id='search_content').findAll('a', {'target': '_blank'}):
            try:
                url = i['href']
                title = i.find('h3').text
                B = bs(get(url).text, 'lxml')
                time = B.find('div',class_='shareBar__info--author').find('span').text
                text = ' '.join(i.text.strip() for i in B.find(id='article_body').findAll('p'))
                content.append({'url': url, 'title': title, 'time': time, 'text': text})
            except:
                pass

def sg(content, qstock):
    sg_lookup = {"1101":"1", "1102":"2", "1216":"13", "1301":"33", "1303":"34", "1326":"51", "1402":"58", "1476":"106", "1722":"193", "2002":"246", "2105":"285", "2201":"292", "2207":"295", "2227":"298", "2301":"305", "2303":"307", "2308":"309", "2311":"310", "2317":"315", "2324":"318", "2325":"319", "2327":"320", "2330":"323", "2347":"332", "2353":"337", "2354":"338", "2357":"341", "2382":"361", "2395":"370", "2408":"378", "2409":"379", "2412":"380", "2448":"408", "2454":"413", "2474":"429", "2492":"444", "2498":"449", "2618":"496", "2633":"497", "2801":"533", "2823":"538", "2880":"555", "2881":"556", "2882":"557", "2883":"558", "2884":"559", "2885":"560", "2886":"561", "2887":"562", "2888":"563", "2890":"565", "2891":"566", "2892":"567", "2912":"577", "3008":"590", "3045":"623", "3231":"710", "3474":"801", "3481":"804", "3673":"930", "3697":"2103", "3711":"2420", "4904":"1126", "4938":"1149", "5854":"2284", "5871":"1360", "5876":"1361", "5880":"1363", "6505":"1614", "9904":"1805", "9910":"1810"}
    stock = sg_lookup[qstock]
    tz = datetime.timezone(datetime.timedelta(hours=8))
    b = json.loads(get('https://statementdog.com/api/v1/feeds?type=news&stock_id=' + stock).text)
    while True:
        for i in b['items']:
            if i['type'] != 'news' or not i['source_url']:
                continue
            time.sleep(.7)
            try:
                for j in range(3):
                    B = bs(get(i['source_url']).text, 'html5lib')
                    if B.find('p').text.strip() != 'Request denied':
                        break
                    sys.stderr.write('Blocked\n')
                    time.sleep(600)
                    if j == 2:
                        return
                text = ' '.join(j.text for j in B.find('article').findAll('p'))
                if not text:
                    continue
                content.append({
                    'url': unquote(i['source_url']), 
                    'title': i['title'], 
                    'time': i['created_at'],
                    'text': text,
                    'stock': qstock})
                sys.stderr.write('.')
                sys.stderr.flush()
            except:
                #sys.stderr.write('\n' + i['source_url'] + '\n')
                continue
        if not b['pagination']['has_more_items'] or datetime.datetime.strptime(b['pagination']['next_url'][47:66], '%Y-%m-%dT%H:%M:%S').astimezone(tz).year < 2017:
            break
        #sys.stderr.write(b['pagination']['next_url'] + '\n')
        b = json.loads(get(b['pagination']['next_url']).text)

content = []
code_to_name = dict(i.decode('utf-8').strip().split(',') for i in open('stock_codec.csv', 'rb'))
src, stock = ['sg'], [sys.argv[1]]

for st in stock:
    for sr in src:
        if sr == 'ctee':
            ctee(content, code_to_name[st])
        elif sr == 'yahoo':
            yahoo(content, st)
        elif sr == 'udn':
            udn(content, code_to_name[st])
        elif sr == 'sg':
            sg(content, st)
print(json.dumps(content, ensure_ascii=False))
sys.stderr.write('\n')

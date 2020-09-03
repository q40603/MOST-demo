import pymysql
import os
import json
import csv
import time
import sys
import requests
from bs4 import BeautifulSoup
from .formation_period import formation_period_single #, formation_period_pair
from .trading_period import pairs
from datetime import datetime
from . import accelerate_formation
from . import accelerate_trading
from . import ADF
#import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pymongo import MongoClient
from .vecm import para_vecm
from .Matrix_function import order_select



db_host = '140.113.24.2'
db_name = 'fintech'
db_user = 'fintech'
db_passwd = 'financefintech'

fin_db = pymysql.connect(
	host = db_host,
	user = db_user,
	password = db_passwd,
	db = db_name,

)
fin_cursor = fin_db.cursor(pymysql.cursors.DictCursor)

client = MongoClient("mongodb://localhost:27017/")
news_db = client["cfda"]





def get_stock_news(choose_date,cusip):
	date = choose_date
	start = choose_date + " 09:00"
	end = choose_date + " 13:30"
	tmp = news_db["c_{}".format(cusip)].find(
		{
			"time": {
				"$gte": datetime.strptime( start, "%Y-%m-%d %H:%M"), 
				"$lte": datetime.strptime( end, "%Y-%m-%d %H:%M")
			}
		}, 
		{"_id": 0, "time":1,"url":1, "title": 1})

	final = []
	for i in tmp:
		#i["time"] = i["time"].strftime("%H:%M")
		final.append(i)
	return final 


def get_s_name(s1,s2):
	query = "select * from stock_name where s_id = {} or s_id = {}".format(s1, s2)
	fin_cursor.execute(query)
	result = fin_cursor.fetchall()
	return(result)


def spread_mean(stock1,stock2,table):
    model = ""
    #print(stock1, stock2)
    if table["model_type"] == 'model1':
        model = 'H2'
    elif table["model_type"] == 'model2':
        model = 'H1*'
    elif table["model_type"] == 'model3':
        model = 'H1'
    #print(model)
    stock1 = stock1[15:]
    stock2 = stock2[15:]
    stock1 = stock1[:150]
    stock2 = stock2[:150]
    b1 = table["w1"]
    b2 = table["w2"]
    y = np.vstack( [stock1, stock2] ).T
    logy = np.log(y)#y.copy()
    lyc = logy.copy()
    p = order_select(logy,5)
    #print(logy)
    #print('p:',p)
    _,_,para = para_vecm(logy,model,p)
    logy = np.mat(logy)
    y_1 = np.mat(logy[p:])
    dy = np.mat(np.diff(logy,axis=0))
    for j in range(len(stock1)-p-1):
        if model == 'H1':
            if p!=1:
                delta = para[0] * para[1].T * y_1[j].T + para[2] * np.hstack([dy[j:(j+p-1)].flatten(),np.mat([1])]).T
            else:
                delta = para[0] * para[1].T * y_1[j].T + para[2] * np.mat([1])
        elif model == 'H1*':
            if p!=1:
                delta = para[0] * para[1].T * np.hstack([y_1[j],np.mat([1])]).T + para[2] * dy[j:(j+p-1)].flatten().T
            else:
                delta = para[0] * para[1].T * np.hstack([y_1[j],np.mat([1])]).T
        elif model == 'H2':
            if p!=1:
                delta = para[0] * para[1].T * y_1[j].T + para[2] * dy[j:(j+p-1)].flatten().T
            else:
                delta = para[0] * para[1].T * y_1[j].T
        else:
            print('Errrrror')
            break
        dy[j+p,:] = delta.T            
        y_1[j+1] = y_1[j] + delta.T
    b = np.mat([[b1],[b2]])
    spread_m = np.array(b.T*y_1.T).flatten()
    return spread_m

def get_pairs_spread(choose_date, s1, s2, w1, w2, model_type):
	fin_db.ping(reconnect = True)
	query1 = "select left(stime, 16) as mtimestamp, sum(volume * price)/(100*sum(volume)) as avg_price from " + s1 +  " where stime >= '"+ choose_date +" 09:00' and stime <= '"+ choose_date +" 13:30' GROUP BY mtimestamp;" 
	fin_cursor.execute(query1)
	result1 = fin_cursor.fetchall()
	fin_db.commit()
	df = pd.DataFrame(list(result1))
	df['mtimestamp'] = pd.to_datetime(df['mtimestamp'])
	df = df.set_index('mtimestamp').resample('T')
	df = df.fillna(method='ffill')
	stock_1 = df.fillna(method='backfill')
	stock_1 = stock_1.reset_index()

	query2 = "select left(stime, 16) as mtimestamp, sum(volume * price)/(100*sum(volume)) as avg_price from " + s2 +  " where stime >= '"+ choose_date +" 09:00' and stime <= '"+ choose_date +" 13:30' GROUP BY mtimestamp;" 
	fin_cursor.execute(query2)
	result2 = fin_cursor.fetchall()
	fin_db.commit()
	df = pd.DataFrame(list(result2))
	df['mtimestamp'] = pd.to_datetime(df['mtimestamp'])
	df = df.set_index('mtimestamp').resample('T')
	df = df.fillna(method='ffill')
	stock_2 = df.fillna(method='backfill')
	stock_2 = stock_2.reset_index()

	stock1_std = stock_1["avg_price"].std() 
	stock2_std = stock_2["avg_price"].std() 

	spread = pd.DataFrame()
	spread["mtimestamp"] = stock_2["mtimestamp"]
	spread["avg_price"] = w1 * np.log(stock_1.avg_price) + w2 * np.log(stock_2.avg_price)
	spread = spread.fillna(method='ffill')
	spread = spread.fillna(method='backfill')


	table = {
		"w1" : w1,
		"w2" : w2,
		"model_type" : model_type
	}

	spread_m = spread_mean(stock_1["avg_price"], stock_2["avg_price"], table )
	return {
		"s1" : stock_1.to_dict("records"),
		"s1_std" : stock1_std,
		"s2" : stock_2.to_dict("records"),
		"s2_std" : stock2_std,
		"spread" : spread.to_dict("records"),
		"spread_m" : spread_m.tolist()
	}

def get_all_pairs(choose_date):
	fin_db.ping(reconnect = True)
	query = "select stock1, stock2, w1, w2, model_type, snr, zcr, mu, stdev, e_mu, e_stdev, action from pairs where f_date = '" + choose_date + "' ;"
	fin_cursor.execute(query)
	data = fin_cursor.fetchall()
	return json.dumps(data)





def trade_certain_pairs(choose_date, capital, maxi, open_time, stop_loss_time, tax_cost, pair_list):
	fin_db.ping(reconnect = True)
	query = "select left(stime, 16) as mtimestamp, code , sum(volume * price)/(100*sum(volume)) as avg_price from s_price_tick where stime >= '"+ choose_date +" 09:00' and stime <= '"+ choose_date +" 13:25' GROUP BY code, mtimestamp;"
	fin_cursor.execute(query)
	result = fin_cursor.fetchall()
	fin_db.commit()
	df = pd.DataFrame(list(result))
	df["avg_price"] = df["avg_price"].apply(lambda x: x/100)
	df = df.pivot(index='mtimestamp', columns='code', values='avg_price')
	df = df.fillna(method='ffill')
	day1 = df.fillna(method='backfill')
	day1 = day1.reset_index()
	day1.index = np.arange(0,len(day1),1)


	# print(df)

	# query = "select distinct f_date from pairs where f_date = '"+ choose_date +"';"
	# fin_cursor.execute(query)
	# result = list(fin_cursor.fetchall())
	# fin_db.commit()


	query = "select * from pairs where f_date = '"+ choose_date +"';"
	fin_cursor.execute(query)
	result = fin_cursor.fetchall()
	fin_db.commit()
	table = pd.DataFrame(list(result))
	table.index = np.arange(0,len(table),1)



		
	#========================================== back test ==============================================



	query = "select left(stime, 16) as mtimestamp, code , price from s_price_tick where stime >= '"+ choose_date +" 11:29' and stime <= '"+ choose_date +" 13:25' GROUP BY code, mtimestamp;"   
	fin_cursor.execute(query)
	result = fin_cursor.fetchall()
	fin_db.commit()
	df = pd.DataFrame(list(result))
	df["price"] = df["price"].apply(lambda x: x/100)
	df = df.pivot(index='mtimestamp', columns='code', values='price')
	df = df.fillna(method='ffill')
	tick_data = df.fillna(method='backfill')
	tick_data.index = np.arange(0,len(tick_data),1)

	

	query = "select left(stime, 16) as mtimestamp, code , sum(volume * price)/sum(volume) as avg_price from s_price_tick where stime > '"+ choose_date +" 11:30' and stime <= '"+ choose_date +" 13:25' GROUP BY code, mtimestamp;"
	fin_cursor.execute(query)
	result = fin_cursor.fetchall()
	fin_db.commit()
	df = pd.DataFrame(list(result))
	df["avg_price"] = df["avg_price"].apply(lambda x: x/100)
	df = df.pivot(index='mtimestamp', columns='code', values='avg_price')
	df = df.fillna(method='ffill')
	min_data = df.fillna(method='backfill')
	min_data.index = np.arange(0,len(min_data),1)
	#min_data["avg_price"] = min_data["avg_price"].apply(lambda x: x/100)
	# print(min_data)

	formate_time = 150

	# capital = 3000           # 每組配對資金300萬
	# maxi = 5                 # 股票最大持有張數
	# open_time = 1.5                 # 開倉門檻倍數
	# stop_loss_time = 10                  # 停損門檻倍數
	# tax_cost = 0
	l_table = len(table.index)
	for i in range(l_table):
		
		y = table.iloc[i,:]
		for j in pair_list:
			if (j[0] == y.stock1 and j[1] == y.stock2 ) or (j[0] == y.stock2 and j[1] == y.stock1 ):
				
				result = pairs( i , formate_time , y , min_data , tick_data , open_time , stop_loss_time , day1 , maxi , tax_cost , capital )
				return result





if __name__ == '__main__':
	choose_date = sys.argv[1]
	capital = 3000           # 每組配對資金300萬
	maxi = 5                 # 股票最大持有張數
	open_time = 1.5                 # 開倉門檻倍數
	stop_loss_time = 10                  # 停損門檻倍數
	tax_cost = 0
	pair_list = ["1326","4909"]
	#get_pairs_spread(choose_date, "s_2330", "s_2313")
	trade_certain_pairs(choose_date, capital, maxi, open_time, stop_loss_time, tax_cost)


from optparse import check_choice
import pymysql
import json
import requests
# from .trading_period import pairs
# from .trade_trend import trade_up_slope, trade_down_slope, trade_normal
from datetime import datetime
# import pandas as pd
# import numpy as np
import math
from pymongo import MongoClient
# from .vecm import para_vecm
# from .Matrix_function import order_select

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = "OmMqjkZ7wPS-7Qy-HegGcHXDfdMp7-lWCMAfNlmyT-_xxgQ6R0D2DI1f5-MmHgk7xvs94rKD7PI4dN-DE5rwJQ=="
org = "PairTrade"
bucket = "stock"

db_host = '127.0.0.1'
db_name = 'PairsTrade'
db_user = 'kctsai'
db_passwd = 'financeai'

fin_db = pymysql.connect(
	host = db_host,
	user = db_user,
	password = db_passwd,
	db = db_name,
	autocommit=True
)
fin_cursor = fin_db.cursor(pymysql.cursors.DictCursor)
client = MongoClient("mongodb://127.0.0.1:27017/")
news_db = client["News"]
trade_db = client["Pairs_Trade_Result"]


'''
query the stock news frmo mongodb that are in range 9:00 ~ 13:30
'''
def get_stock_news(choose_date, cusip):
	start = choose_date + " 09:00"
	end = choose_date + " 13:30"
	tmp = news_db["c_{}".format(cusip)].find(
		{
			"pubtime": {
				"$gte": datetime.strptime( start, "%Y%m%d %H:%M"), 
				"$lte": datetime.strptime( end, "%Y%m%d %H:%M")
			}
		}, 
		{"_id": 0, "pubtime":1,"url":1, "title": 1})

	final = []
	for i in tmp:
		final.append(i)
	return final 

'''
query company chinese name
'''
def get_s_name(s1, s2):
	query = "select * from stock_name where s_id = {} or s_id = {}".format(s1, s2)
	fin_cursor.execute(query)
	result = fin_cursor.fetchall()
	return(result)


def get_past_five():
	cursor = trade_db.trade.find({},{
		"_id" : 0,
		"record.total_profit":1,
		"record.win":1,
		"record.loss":1,
		"record.zero":1 ,
		"time":1}).sort("time", -1 ).limit(20)
	result = [i for i in cursor]
	return result

# def spread_mean(stock1, stock2, table):
#     model = ""

#     if table["model_type"] == 'model1':
#         model = 'H2š
#     elif table["model_type"] == 'model2':
#         model = 'H1*'
#     elif table["model_type"] == 'model3':
#         model = 'H1'

#     stock1 = stock1[16:166]
#     stock2 = stock2[16:166]
#     b1 = table["w1"]
#     b2 = table["w2"]
#     y = np.vstack( [stock1, stock2] ).T
#     logy = np.log(y)
#     p = order_select(logy,5)

#     _,_,para = para_vecm(logy,model,p)
#     logy = np.mat(logy)
#     y_1 = np.mat(logy[p:])
#     dy = np.mat(np.diff(logy,axis=0))
#     for j in range(len(stock1)-p-1):
#         if model == 'H1':
#             if p!=1:
#                 delta = para[0] * para[1].T * y_1[j].T + para[2] * np.hstack([dy[j:(j+p-1)].flatten(),np.mat([1])]).T
#             else:
#                 delta = para[0] * para[1].T * y_1[j].T + para[2] * np.mat([1])
#         elif model == 'H1*':
#             if p!=1:
#                 delta = para[0] * para[1].T * np.hstack([y_1[j],np.mat([1])]).T + para[2] * dy[j:(j+p-1)].flatten().T
#             else:
#                 delta = para[0] * para[1].T * np.hstack([y_1[j],np.mat([1])]).T
#         elif model == 'H2':
#             if p!=1:
#                 delta = para[0] * para[1].T * y_1[j].T + para[2] * dy[j:(j+p-1)].flatten().T
#             else:
#                 delta = para[0] * para[1].T * y_1[j].T
#         else:
#             print('Errrrror')
#             break
#         dy[j+p,:] = delta.T            
#         y_1[j+1] = y_1[j] + delta.T
#     b = np.mat([[b1],[b2]])
#     spread_m = np.array(b.T*y_1.T).flatten()
#     return spread_m


def get_pairs_spread(pair_info):

	choose_date = pair_info["time"].replace("-","")
	s1 = pair_info["S1"]
	s2 = pair_info["S2"]
	w1 = pair_info["w1"]
	w2 = pair_info["w2"]
	client = InfluxDBClient(url="http://paris-trading.lab.nycu.edu.tw:8086", token=token)
	start = datetime.strptime(f'{choose_date} 09:00', "%Y%m%d %H:%M").strftime('%Y-%m-%dT%H:%M:%SZ')
	end = datetime.strptime(f'{choose_date} 13:31', "%Y%m%d %H:%M").strftime('%Y-%m-%dT%H:%M:%SZ')
	query = f'\
	import "interpolate"\
	from(bucket: "stock")\
	|> range(start: {start}, stop: {end})\
	|> filter(fn: (r) => r["_measurement"] == "{s1}")\
	|> filter(fn: (r) => r["_field"] == "price" or r["_field"] == "vol")\
	|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")\
	|> window(every:1m)\
	|> reduce(fn: (r, accumulator) => ({{\
		count: accumulator.count + float(v:r.vol),\
		total: accumulator.total + (float(v: r.vol) * r.price),\
	}}),\
		identity: {{count: 0.0, total: 0.0}}\
	)\
	|> map(fn: (r) => ({{ r with _value: float(v: r.total) / r.count }}))\
	|> keep(columns: ["_start", "_value"])\
	|> duplicate(column:"_start", as:"_time")\
	|> window(every:inf)\
	|> interpolate.linear(every: 1m)\
	'

	s1_result = client.query_api().query(org=org, query=query)
	s1_data = []
	for table in s1_result:
		for record in table.records:
			s1_data.append((record.get_time(),record.get_value()))

	query = f'\
	import "interpolate"\
	from(bucket: "stock")\
	|> range(start: {start}, stop: {end})\
	|> filter(fn: (r) => r["_measurement"] == "{s2}")\
	|> filter(fn: (r) => r["_field"] == "price" or r["_field"] == "vol")\
	|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")\
	|> window(every:1m)\
	|> reduce(fn: (r, accumulator) => ({{\
		count: accumulator.count + float(v:r.vol),\
		total: accumulator.total + (float(v: r.vol) * r.price),\
	}}),\
		identity: {{count: 0.0, total: 0.0}}\
	)\
	|> map(fn: (r) => ({{ r with _value: float(v: r.total) / r.count }}))\
	|> keep(columns: ["_start", "_value"])\
	|> duplicate(column:"_start", as:"_time")\
	|> window(every:inf)\
	|> interpolate.linear(every: 1m)\
	'	
	s2_result = client.query_api().query(org=org, query=query)
	s2_data = []
	for table in s2_result:
		for record in table.records:
			s2_data.append((record.get_time(),record.get_value()))

	s1_data = s1_data[:265]
	s2_data = s2_data[:265]

	fin_db.ping(reconnect = True)
	query = f"SELECT cid, cname FROM PairsTrade.company where cid={s1} or cid={s2} order by cid;"
	fin_cursor.execute(query)
	data = fin_cursor.fetchall()

	spread = []
	for i in range(265):
		_spr = w1 * math.log(s1_data[i][1]) + w2 * math.log(s2_data[i][1])
		spread.append((s1_data[i][0], _spr))

	# query =f'\
	# from(bucket: "converge")\
	# |> range(start: {start}, stop: {end})\
	# |> filter(fn: (r) => r["_measurement"] == "{s1}_{s2}")\
	# '
	# converge_mean = client.query_api().query(org=org, query=query)
	# converge_data = []
	# for table in converge_mean:
	# 	for record in table.records:
	# 		converge_data.append((record.get_time(),record.get_value()))	


	mean = []
	mean.append((s1_data[16][0], pair_info["Johansen_intercept"]))
	mean.append((s1_data[264][0], pair_info["Johansen_intercept"] + pair_info["Johansen_slope"]*265))


	s1_news = get_stock_news(choose_date, s1)
	s2_news = get_stock_news(choose_date, s2)


	backtest_result = backtest(choose_date, s1, s2)

	return {
		"s1" : s1_data,
		"s2": s2_data,
		"s_info" : data,
		"spread" : spread,
		"mean" : mean,
		# "converge_mean": converge_data,
		"s1_news" : s1_news,
		"s2_news" : s2_news,
		"backtest" : backtest_result["trading_result"]
	}



def backtest(choose_date, s1, s2):
	start = choose_date + " 11:47"

	result = trade_db.trade.aggregate([
    { "$match": { "time": datetime.strptime( start, "%Y%m%d %H:%M") } },
    { "$project" : { "trading_history" : "$record.trading_history" , "_id" : 0 } },
    { "$project": {
        "trading_result": {
			"$filter": {
            	"input": '$trading_history',
            	"as": 't',
            	"cond": {
                "$and": [
                    {"$eq": ['$$t.s1', f'{s1}']},
                    {"$eq": ['$$t.s2', f'{s2}']}
                ]
            }
        }}
    }},
    {"$unwind":"$trading_result"}
	])	
	# result = trade_db[f'trade_{choose_date}'].find_one(
	# 	{},
	# 	{ 
	# 		"_id": 0,
	# 		"trading_history": {
	# 			"$elemMatch": {
	# 				"s1": s1, 
	# 				"s2": s2
	# 			} 
	# 		} 
	# 	}
	# )

	return list(result)[0]


def get_all_pairs(choose_date):
	fin_db.ping(reconnect = True)
	query = "select * from Pairs where time = '" + choose_date + "' order by _return desc;"
	fin_cursor.execute(query)
	data = fin_cursor.fetchall()


	html = trade_db.table.find(
		{"time" : choose_date},
		{"_id" : 0}
	)
	return json.dumps({
		"data" : data,
		"html" : list(html)[0]["html"]
	})

# def trade(pair_info):


# def trade_pair(choose_date, s1, s2):
# 	fin_db.ping(reconnect = True)
# 	query = "select * from pairs where f_date = '{}' and stock1 in({},{}) and stock2 in({},{});".format(choose_date, s1, s2, s1, s2)
# 	fin_cursor.execute(query)
# 	result = fin_cursor.fetchall()
# 	fin_db.commit()
# 	table = pd.DataFrame(list(result))	



# ################## query pair tick ##################

# 	fin_db.ping(reconnect = True)
# 	query1 = "select left(stime, 16) as mtimestamp, price/100 as '{}' from {} where stime >= '{} 9:00' and stime <= '{} 13:30' GROUP BY mtimestamp;".format(s1,"s_"+s1, choose_date, choose_date) 
# 	fin_cursor.execute(query1)
# 	result1 = fin_cursor.fetchall()
# 	fin_db.commit()
# 	df = pd.DataFrame(list(result1))
# 	df['mtimestamp'] = pd.to_datetime(df['mtimestamp'])
# 	df = df.set_index('mtimestamp').resample('T')
# 	df = df.fillna(method='ffill')
# 	stock_1 = df.fillna(method='backfill')
# 	stock_1 = stock_1.reset_index()

# 	query2 = "select left(stime, 16) as mtimestamp, price/100 as '{}' from {} where stime >= '{} 9:00' and stime <= '{} 13:30' GROUP BY mtimestamp;".format(s2,"s_"+s2, choose_date, choose_date) 
# 	fin_cursor.execute(query2)
# 	result2 = fin_cursor.fetchall()
# 	fin_db.commit()
# 	df = pd.DataFrame(list(result2))
# 	df['mtimestamp'] = pd.to_datetime(df['mtimestamp'])
# 	df = df.set_index('mtimestamp').resample('T')
# 	df = df.fillna(method='ffill')
# 	stock_2 = df.fillna(method='backfill')
# 	stock_2 = stock_2.reset_index(drop=True)

# 	tick_data = pd.concat([stock_1,stock_2],axis=1)[166:].reset_index()


# ################## query pair min average##################


# 	query1 = "select left(stime, 16) as mtimestamp, sum(volume * price)/(100*sum(volume)) as '{}' from {} where stime >= '{} 09:00' and stime <= '{} 13:30' GROUP BY mtimestamp;".format(s1,"s_"+s1, choose_date, choose_date) 
# 	fin_cursor.execute(query1)
# 	result1 = fin_cursor.fetchall()
# 	fin_db.commit()
# 	df = pd.DataFrame(list(result1))
# 	df['mtimestamp'] = pd.to_datetime(df['mtimestamp'])
# 	df = df.set_index('mtimestamp').resample('T')
# 	df = df.fillna(method='ffill')
# 	stock_1 = df.fillna(method='backfill')
# 	stock_1 = stock_1.reset_index(drop=True)

# 	query2 = "select left(stime, 16) as mtimestamp, sum(volume * price)/(100*sum(volume)) as '{}' from {} where stime >= '{} 09:00' and stime <= '{} 13:30' GROUP BY mtimestamp;".format(s2,"s_"+s2, choose_date, choose_date) 
# 	fin_cursor.execute(query2)
# 	result2 = fin_cursor.fetchall()
# 	fin_db.commit()
# 	df = pd.DataFrame(list(result2))
# 	df['mtimestamp'] = pd.to_datetime(df['mtimestamp'])
# 	df = df.set_index('mtimestamp').resample('T')
# 	df = df.fillna(method='ffill')
# 	stock_2 = df.fillna(method='backfill')
# 	stock_2 = stock_2.reset_index(drop=True)

# 	min_data = pd.concat([stock_1,stock_2],axis=1)

# 	result = pairs( 
#         pos = 0,
#         formate_time = 166,  
#         table = table , 
#         min_data = min_data , 
#         tick_data = tick_data ,
#         maxi = 5 ,
#         tax_cost = 0.0015, 
#         cost_gate = 0.000 , 
#         capital = 300000000 
# 	)
# 	return result



# def structure_break_pred(choose_date, s1, s2):
# 	choose_date = choose_date.replace("-","")
# 	print(choose_date, s1, s2)
# 	func_para = '{"date":'+choose_date+',"stock1":'+s1+',"stock2":'+s2+'}' 
# 	res = requests.post('http://mpcdl.cs.nctu.edu.tw:5019/predict/api/', json=func_para)
# 	print(res)
# 	return res.json()

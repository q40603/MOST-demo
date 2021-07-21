#!/home/kctsai/miniconda3/envs/demo/bin/python
import pandas as pd
import numpy as np
import time
import os
import sys
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from trade_trend import trade_down_slope, trade_up_slope, trade_normal
from sqlalchemy import create_engine
from copy import copy
import datetime

client = MongoClient("mongodb://127.0.0.1:27017/")
trade_db = client["Pairs_Trade_Result"]

db_host = '127.0.0.1'
db_name = 'PairsTrade'
db_user = 'kctsai'
db_passwd = 'financeai'
sqlEngine = create_engine('mysql+pymysql://'+db_user+':'+db_passwd+'@'+db_host+'/'+db_name, pool_recycle=3600)
dbConnection = sqlEngine.connect()



form_del_min = 16
#參數
indataNum=150   #建模期間
Cost= 0.0015     #交易成本
CostS=0.0015   #交易門檻
Os=1.5          #開倉倍數(與喬登對齊)
Fs= 10000       #強迫平倉倍數(無限大=沒有強迫平倉) (與喬登對齊)
Cs = 0
MaxVolume=5     #最大張數限制
OpenDrop=16     #開盤捨棄
Min_c_p= 300    #最小收斂點門檻(大於indataNum=沒有設)(與喬登對齊,無收斂點概念)
Max_t_p=190     #最大開盤時間(190        (與喬登對齊)


_date = sys.argv[1]
year = _date[:4]

test_dataPath = "/home/kctsai/fintech/pair_data/" + year + "/minprice/" + _date + "_min_stock.csv"
table_path = "/home/kctsai/fintech/pair_data/newstdcompare" + year + "/{}_table.csv".format(_date)



test_data = pd.read_csv(test_dataPath, index_col=False)
test_data = test_data.iloc[167:266,:]
test_data = test_data.reset_index(drop=True)


dtype = {
    'S1' : str,
    'S2' : str,
    'VECMQ' : float,
    'Johansen_intercept': float,
    'Johansen_slope' : float,
    'std' : float,
    'model' : int,
    'w1' : float,
    'w2' : float
}
table = pd.read_csv(table_path, dtype = dtype)
table["S1"] = table["S1"].apply(lambda x: x.rstrip('0').rstrip('.'))
table["S2"] = table["S2"].apply(lambda x: x.rstrip('0').rstrip('.'))
table["_return"] = np.float(0.0)

start = datetime.datetime.strptime(f'{_date} 11:47', '%Y%m%d %H:%M')
# {
#    "s1_tick",
#    "s2_tick"
#     "table" : {
#         "s1",
#         "s2",
#         "w1",
#         "w2",
#         "Jxx slope",
#         "Jxx intercept",
#         "std"
#     }
#     "strategy" {
#         "up_open_time",
#         "down_open_time",
#         "maxhold",
#         "cost_gate",
#         "capital",
#         "tax_cost"
#     }
# }
strategy = {
    "up_open_time" : 1.5,
    "down_open_time" : 1.5,
    "maxhold" : 5,
    "cost_gate" : 0.0015,
    "capital" : 300000000,
    "tax_cost" : 0.0015
}


result = {}
trading_history = []

up_table = table[table["Johansen_slope"]>0]
total_up = 0
for index, row in up_table.iterrows():
    s1_tick = test_data[row["S1"]]
    s2_tick = test_data[row["S2"]]
    _trade, _profit, _capital, _return, _history = trade_up_slope(s1_tick, s2_tick, row.to_dict(), strategy)
    total_up += _profit
    for i in _history:
        i["time"] = start + datetime.timedelta(minutes=i["time"])
    table.at[index,"_return"] = _return * 100
    trading_history.append({
        "s1" : row["S1"],
        "s2" : row["S2"],
        "profit" : _profit * 1000,
        "return" : _return * 100,
        "capital" : _capital * 1000,
        "trade" : _trade,
        "history" : _history
    })
    # print(index, _return * 100)
    # print("--------------------------------------------")

down_table = table[table["Johansen_slope"]<0]
total_down = 0
for index, row in down_table.iterrows():
    
    s1_tick = test_data[row["S1"]]
    s2_tick = test_data[row["S2"]]
    _trade, _profit, _capital, _return, _history = trade_down_slope(s1_tick, s2_tick, row.to_dict(), strategy)
    total_down += _profit
    for i in _history:
        i["time"] = start + datetime.timedelta(minutes=i["time"])
    table.at[index,"_return"] = _return * 100
    trading_history.append({
        "s1" : row["S1"],
        "s2" : row["S2"],
        "profit" : _profit * 1000,
        "return" : _return * 100,
        "capital" : _capital * 1000,
        "trade" : _trade,
        "history" : _history
    })
    # print(index, _return * 100)
    # print("--------------------------------------------")


normal_table = table[table["model"]<4]
total_normal = 0
for index, row in normal_table.iterrows():
    s1_tick = test_data[row["S1"]]
    s2_tick = test_data[row["S2"]]
    _trade, _profit, _capital, _return, _history = trade_normal(s1_tick, s2_tick, row.to_dict(), strategy)
    total_normal += _profit
    for i in _history:
        i["time"] = start + datetime.timedelta(minutes=i["time"])
    table.at[index,"_return"] = _return * 100
    trading_history.append({
        "s1" : row["S1"],
        "s2" : row["S2"],
        "profit" : _profit * 1000,
        "return" : _return * 100,
        "capital" : _capital * 1000,
        "trade" : _trade,
        "history" : _history
    })
    # print(index, _return * 100)
    # print("--------------------------------------------")



result = {
    "time" : start,
    "record" : {
        "win" : len(table[table["_return"]>0]),
        "loss" : len(table[table["_return"]<0]),
        "zero" : len(table[table["_return"]==0]),
        "total_profit" : total_down + total_up + total_normal,
        "trading_history" : trading_history
    }
}

table.to_sql("Pairs", index=False, con = sqlEngine, if_exists = 'append', chunksize = 1000)
# # print(result)
check = trade_db[f'trade'].insert_one(copy(result))


# {
#     "win" :
#     "loss" :
#     "zero" :
#     "total_profit" :
#     "trading_result" : [
#         {
#             "s1" :
#             "s2" :
#             "profit" :
#             "return" :
#             "captial" :
#             "trade" :
#             "history" : [
#                 {
#                     "time" : 
#                     "type" :
#                     "w1" : 
#                     "s1_payoff" :
#                     "w2" :
#                     "s2_payoff" :
#                 }
#             ]
#         }

#     ]
# }
# dailytable = ptm.formation_table(test_data,indataNum,CostS,Cost,Os,Fs,MaxVolume,OpenDrop,Min_c_p, Max_t_p)                       
# dailytable = pd.DataFrame(dailytable,columns = ['S1','S2','VECMQ','Johansen_intercept','Johansen_slope','std','model','w1','w2'])
# dailytable = dailytable[~dailytable["std"].isnull()]



# dailytable["time"] = _date
# dailytable.to_csv(table_path,index=False)
# dailytable.to_sql("Pairs", index=False,con = sqlEngine, if_exists = 'append', chunksize = 1000)


# table = pd.read_csv(table_path)
# ret = ptm.daily_procces(test_data,indataNum,CostS,Cost,Os,Fs,MaxVolume,OpenDrop,Min_c_p, Max_t_p)



# save_path = r''
# date = ''.join( [ year , month , day]  )
# dailytable.to_csv( ''.join([ date ,"_formationtable.csv" ]))

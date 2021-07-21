#!/home/kctsai/miniconda3/envs/demo/bin/python
"""
Created on Thu Jan 28 11:49:31 2021

@author: MAI
"""

import pandas as pd
import numpy as np
import os
import JCItestpara_20201113 as jci
from Matrix_function import  order_select, spread_mean
import sys
from datetime import datetime

os.chdir("/home/kctsai/fintech/trend_stationary/")

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
_file = open("./converge_data/{}.csv".format(_date),"w")
test_dataPath = "/home/kctsai/fintech/pair_data/" + year + "/averageprice/" + _date + "_averagePrice_min.csv"
table_path = "/home/kctsai/fintech/pair_data/newstdcompare" + year + "/{}_table.csv".format(_date)
test_data = pd.read_csv(test_dataPath,index_col=False)
test_data_iterated = test_data.copy()
test_data = test_data.iloc[form_del_min:266,:]
test_data = test_data.reset_index(drop=True)
test_data_iterated = test_data_iterated.reset_index(drop=True)

table = pd.read_csv(table_path)
converge_mean = {}

start = datetime.strptime(f'{_date} 09:16', "%Y%m%d %H:%M").strftime('%Y-%m-%dT%H:%M:%SZ')
daterange = pd.date_range(start, periods=150, freq='1min')
daterange = [int(i.timestamp()*(10**9)) for i in daterange]
print("#datatype measurement,double,dateTime:number", file=_file)
print("m,mean,time", file=_file)

for i in range(table.shape[0]):
    s1 = str(int(table.S1[i]))
    s2 = str(int(table.S2[i]))
    #if i == 212:
    #Smin為每日的每分鐘股價
    Smin = test_data.iloc[0:250,:] #捨棄最後五分鐘
    Smin_iterated = test_data_iterated.iloc[:-5,:] #捨棄最後五分鐘
    LSmin = np.log(Smin)
    LSmin_iterated = np.log(Smin_iterated)
    DailyNum=len(Smin)
    SStd = table.std
    cy = np.zeros([DailyNum,table.shape[0]]) # cy為Naturn Log共整合序列，以Capital Weight構成
    B = np.zeros([2,table.shape[0]]) #B為共整合係數
    CapitW = np.zeros([2,table.shape[0]]) #CW為資金權重Capital Weight
    CapitW[0,:] = table.w1
    CapitW[1,:] = table.w2
    #for mi in range(table.shape[0]):
    rowLS1 = np.array(LSmin[str(int(table.S1[i]))])
    rowLS2 = np.array(LSmin[str(int(table.S2[i]))])
    rowLS = np.vstack((rowLS1,rowLS2)).T
    rowLS1_iterated = np.array(LSmin_iterated[str(int(table.S1[i]))])
    rowLS2_iterated = np.array(LSmin_iterated[str(int(table.S2[i]))])
    rowLS_iterated = np.vstack((rowLS1_iterated,rowLS2_iterated)).T
    cy_mean = table.Johansen_intercept[i] + table.Johansen_slope[i]*np.linspace(0,249,250)
    #以資金權重建構Naturn Log共整合序列
    cy = pd.DataFrame( np.mat(rowLS) * np.mat(CapitW[:,i]).T).stack()
    SStd = np.array(table['std'])
    #迭帶MEAN
    St = rowLS[0:150]
    p = order_select(St,5)
    F_a, F_b, F_ct, F_ut, F_gam,ct,omega_hat = jci.JCItestpara_spilCt(St,table.model[i],p-1)
    Com_para = []
    Com_para.append(F_a)
    Com_para.append(F_b)
    Com_para.extend(F_ct)
    spread_m= jci.Iteration_Mean_Std(table.model[i], p-1,Com_para, F_gam, rowLS_iterated, 16, 166) 
    distance = np.abs(np.matrix(spread_m[16:166]) - np.matrix(cy_mean[0:150]).T)
    # converge_mean["{}_{}".format(str(int(table.S1[i])),str(int(table.S2[i])))] = spread_m[16:166]
    for j in range(150):
        print(f"{s1}_{s2},{spread_m[j+16].item()},{daterange[j]}", file=_file)



# for k,v in converge_mean.items():
#     for i in range(v):
#         print(f"{k},{v[i]},{daterange[i]}")
            
            
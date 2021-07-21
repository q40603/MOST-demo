# -*- coding: utf-8 -*-
"""
Created on Thu Jul 16 22:39:16 2020

@author: Hua
"""
import pandas as pd
import numpy as np
#import mt 
import matplotlib.pyplot as plt
import PTwithTimeTrend_AllStock as ptm
import time
import os

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

##set the date

years = [str(x) for x in range(2017, 2020)]
# years = ['2016']
# months = ["01"]
months = ["01","02","03","04","05","06","07","08","09","10",
    "11","12"]
# days=["04"]
days = ["01","02","03","04","05","06","07","08","09","10",
   "11","12","13","14","15","16","17","18","19","20",
 "21","22","23","24","25","26","27","28","29","30",
  "31"]


#if False:
#    test_csv_name = '_half_min'
#else:
#   test_csv_name = '_averagePrice_min'
for year in years:
#    YearProfit = np.zeros((2,5))
    
    for month in months:
        
        for day in days:
            try:
                print("Now import: ",year, month, day)
                test_dataPath = r'{}\averageprice'.format(year)
                test_data = pd.read_csv(os.path.join(test_dataPath,'{}{}{}_averagePrice_min.csv'.format(year,month,day)),index_col=False)
                test_data = test_data.iloc[form_del_min:266,:]
                test_data = test_data.reset_index(drop=True)
                dailytable = ptm.formation_table(test_data,indataNum,CostS,Cost,Os,Fs,MaxVolume,OpenDrop,Min_c_p, Max_t_p)                       
                dailytable = pd.DataFrame(dailytable,columns = ['S1','S2','VECM(q)','Johansen_intercept','Johansen_slope','std','model','w1','w2'])
                save_path = r''
                date = ''.join( [ year , month , day]  )
                dailytable.to_csv( ''.join([ date ,"_formationtable.csv" ]))
            except:
                print('error')
                continue
            '''           
            test_dataPath = r'D:\JordanMaiThesis\Thesis\data\min_data\{}\averageprice'.format(year)
            try:
            test_data = pd.read_csv(os.path.join(test_dataPath,'{}{}{}{}.csv'.format(year,month,day,test_csv_name)))
            test_data = test_data.iloc[form_del_min:,:]
            test_data = test_data.reset_index(drop=True)
            except: 
            continue
            #Total = np.zeros((2,5))
            #CumResultMin = np.zeros((1,18))
            #EquityCurveMin  = np.zeros((1,Days))
            
            #Smin為每日的每分鐘股價
            Smin = test_data.iloc[0:250,:] #捨棄最後五分鐘
            #dailyResult = ptm.daily_procces(Smin,indataNum,CostS,Cost,Os,Fs,MaxVolume,OpenDrop,Min_c_p, Max_t_p)
            dailytable = ptm.formation_table(Smin,indataNum,CostS,Cost,Os,Fs,MaxVolume,OpenDrop,Min_c_p, Max_t_p)
            #Total[0, 0:5] = sum(dailyResult[:, 6:11])
            #Total[1, 0:5] = sum(dailyResult[:, 11:16])
            #YearProfit[0, 0:5] = YearProfit[0, 0:5] + Total[0, 0:5]
            #YearProfit [1, 0:5] = YearProfit[1, 0:5]  + Total[1, 0:5]
            date = ''.join( [ year , month , day]  )
            #dailyResult = pd.DataFrame(dailyResult,columns = ['S1','S2','model','w1','w2','converg_point','total profit','close profit',
            #                                                    'stoplossing profit','stopearning profit(change day)','stopelossing profit(change day)','open times','close times',
            #                                                   'stoploss times','stopearning times(change day)','stoplossing times(change day)','up(1)/down(-1)'])
            #Total =  = pd.DataFrame(Total)
            #Total.to_csv(''.join([ save_path ,'/', date ,"_dailytable.csv" ]))
            dailytable = pd.DataFrame(dailytable,columns = ['S1','S2','VECM(q)','Johansen_intercept','Johansen_slope','std','model','w1','w2'])
            save_path = r'D:\HSINHUA\formation_table_20201202\ptstrendPythonCode\allstock_formation_table_adf_trace_test\{}'.format(year)
            dailytable.to_csv( ''.join([ save_path ,'/', date ,"_formationtable.csv" ]))
            #dailyResult.to_csv( ''.join([ save_path ,'/', date ,"_dailytable.csv" ]))
            #save_path2 = r'D:\HSINHUA\formation_table_20201202\ptstrendPythonCode\allstockmodel45\{}'.format(year)
            #YearProfit = pd.DataFrame(YearProfit)
            #YearProfit.to_csv( ''.join([ save_path ,'/', year ,"_yeartable.csv" ]))
            #疊上日期代號
            #dailyResult = np.hstack((dailyResult , np.ones((dailyResult.shape[0],1)) ))
            #把結果疊起來
            #CumResultMin = np.vstack( (CumResultMin, dailyResult) )
            #EquityCurveMin[0,di] = sum(dailyResult[:,6])
            '''          



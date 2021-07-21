#!/home/kctsai/miniconda3/envs/demo/bin/python
import pandas as pd
import numpy as np
import PTwithTimeTrend_AllStock as ptm
import time
import os
import sys
from sqlalchemy import create_engine

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

test_dataPath = "/home/kctsai/fintech/pair_data/" + year + "/averageprice/" + _date + "_averagePrice_min.csv"
table_path = "/home/kctsai/fintech/pair_data/newstdcompare" + year + "/{}_table.csv".format(_date)
test_data = pd.read_csv(test_dataPath,index_col=False)
corp = test_data.columns.values
corp = [i for i in corp if (i.isnumeric() and len(i)==4)]
test_data = test_data[corp]
test_data = test_data.iloc[form_del_min:266,:]
test_data = test_data.reset_index(drop=True)

dailytable = ptm.formation_table(test_data,indataNum,CostS,Cost,Os,Fs,MaxVolume,OpenDrop,Min_c_p, Max_t_p)                       
dailytable = pd.DataFrame(dailytable,columns = ['S1','S2','VECMQ','Johansen_intercept','Johansen_slope','std','model','w1','w2'])
dailytable = dailytable[~dailytable["std"].isnull()]


dailytable["time"] = _date
dailytable.to_csv(table_path, index=False)
# dailytable.to_sql("Pairs", index=False,con = sqlEngine, if_exists = 'append', chunksize = 1000)


# table = pd.read_csv(table_path)
# ret = ptm.daily_procces(test_data,indataNum,CostS,Cost,Os,Fs,MaxVolume,OpenDrop,Min_c_p, Max_t_p)



# save_path = r''
# date = ''.join( [ year , month , day]  )
# dailytable.to_csv( ''.join([ date ,"_formationtable.csv" ]))

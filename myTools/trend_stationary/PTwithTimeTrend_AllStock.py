# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 21:27:14 2020

@author: Hua
"""
import numpy as np
import pandas as pd
import mt 
from Matrix_function import  order_select
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller
import JCItestpara_20201113 as jci
def formation_table(Smin, inNum,costS,cost,os,cs,MaxV,OpenD,Min_cp, Max_tp):
    LSmin = np.log(Smin) #已捨棄前16分鐘與最後五分鐘的股價取log
    #LSmin = Smin
    maxcompanynu = Smin.shape[1] #找出有多少檔
    ind = mt.Binal_comb(range(maxcompanynu))
    ind = np.hstack((ind,np.zeros([ind.shape[0], 7])))
    #ind.columns = [0:S1_inx,1:S2_inx,2:opt_q, 3:Johansen intercept, 4:Johansen slope, 5:std,6:Model,7:W1,8:W2]
    DailyNum=len(Smin)
    cy = np.zeros([DailyNum,ind.shape[0]]) # cy為Naturn Log共整合序列，以Capital Weight構成
    cy_mean = np.zeros([DailyNum,ind.shape[0]]) # cy_mean為共整合序列均值，以Capital Weight構成
    B = np.zeros([2,ind.shape[0]]) #B為共整合係數
    CapitW = np.zeros([2,ind.shape[0]]) #CW為資金權重Capital Weight
    #IntegerB = np.zeros([2,ind.shape[0]]) #IB為CW整數化後的共整合係數
    
    #start_time = time.time()
    for mi in range(ind.shape[0]):
    #for mi in range(1):
        rowS = LSmin.iloc[0:inNum,[int(ind[mi,0]),int(ind[mi,1])]] #150分鐘
        rowLS = LSmin.iloc[:DailyNum,[int(ind[mi,0]),int(ind[mi,1])]]  #250分鐘
        #stock1 = Smin.iloc[inNum-1,[int(ind[mi,0])]]
        #stock2 = Smin.iloc[inNum-1,[int(ind[mi,1])]]
        ind[mi,0:2] = rowS.columns.values
        rowAS = np.array(rowS)
        # 配適 VAR(P) 模型 ，並利用BIC選擇落後期數，max_p意味著會檢查2~max_p
        try:
            max_p = 5
            p = order_select( rowAS , max_p )
            #ADF TEST
            if p < 1:     
                
                    continue
            # adf test
            # portmanteau test
            model = VAR(rowAS)
            
            if model.fit(p).test_whiteness( nlags = 5 ).pvalue < 0.05:
            
                continue
        
            # Normality test
            if model.fit(p).test_normality().pvalue < 0.05:
            
                continue
            
            opt_model = jci.JCI_AutoSelection(rowAS,p-1)        
            #如果有共整合，紀錄下Model與opt_q
            ind[mi,2] = p-1
            ind[mi,6] = opt_model        
            F_a, F_b, F_ct, F_ut, F_gam,ct,omega_hat = jci.JCItestpara_spilCt(rowAS,opt_model,p-1)

            # ind[mi,9] = F_a
            # ind[mi,10] = F_b
            # ind[mi,11] = F_ct
            # ind[mi,12] = F_ut
            # ind[mi,13] = F_gam  
            # ind[mi,14] = ct
            # ind[mi,15] = omega_hat     
     

            Com_para = []
            Com_para.append(F_a)
            Com_para.append(F_b)
            Com_para.extend(F_ct)               
            #把  arrary.shape(2,1) 的數字放進 shape(2,) 的Serires 
            #取出共整合係數
            B[:,mi] =  pd.DataFrame(F_b).stack()
            #將共整合係數標準化，此為資金權重Capital Weight
            CapitW[:,mi] =  B[:,mi] / np.sum( np.absolute(B[:,mi]) )
            ind[mi,7] = CapitW[0,mi]
            ind[mi,8] = CapitW[1,mi]
            '''
            #將資金權重，依股價轉為張數權重
            S1 = CapitW[0][mi]/float(stock1)
            S2 = CapitW[1][mi]/float(stock2)
            
            #將張數權重，做最簡整數比，要求範圍是最大張數+1
            optXY = mt.simp_frac(S1,S2,MaxV+1)
            
            #如果最簡整數比出現[ (MaxV+1) / 1 ] or [ 1 / (MaxV+1) ] 就剃除
            #張數權重整數化後，絕對值小於5的設1（通過），絕對值大於6的設0（沒通過）
            if abs(optXY[0]) <= MaxV  and abs(optXY[1]) <= MaxV:
                ind[mi,4] = 1
                IntegerB[:,mi] = optXY[:]
                ind[mi,7] = optXY[0]
                ind[mi,8] = optXY[1]
            
           '''
            #計算Spread的時間趨勢均值與標準差
            Johansen_intcept, Johansen_slope = jci.Johansen_mean(F_a,F_b,F_gam,F_ct,p-1)
            Johansen_var_correct = jci.Johansen_std_correct(F_a,F_b,F_ut, F_gam,p-1)
            Johansen_std = np.sqrt(Johansen_var_correct)
            ind[mi,3] = Johansen_intcept
            ind[mi,4] = Johansen_slope
            ind[mi,5] = Johansen_std
            SStd = Johansen_std
            cy_mean[:,mi] = Johansen_intcept + Johansen_slope*np.linspace(0,249,250)
            #以資金權重建構Naturn Log共整合序列
            cy[:,mi] = pd.DataFrame( np.mat(rowLS) * np.mat(CapitW[:,mi]).T).stack()
            #拿共整合序列拿去檢定，ADF單根檢定回傳1代表無單根（定態），0代表有單根（非定態）
            #ind[mi,5] = mt.ADFtest_TR(cy[OpenD-1:inNum,mi], opt_p-1 , 0.05)
            #如果收斂點在Trading Period，設為0（沒通過、不交易），反之設為1
            #if converg_Point < inNum:
                #ind[mi,10] = converg_Point
        #Spend_time = time.time() - start_time
            '''
            #畫個圖確認一下
            print(ind[mi,0:2])
            import matplotlib.pyplot as plt
            plotx = [i for i in range(DailyNum)]
            CL = np.zeros((DailyNum,5))
            CL [:,2] = cy_mean[:,mi]
            CL [:,1] = cy_mean[:,mi]+SStd*os
            CL [:,0] = cy_mean[:,mi]+SStd*cs
            CL [:,3] = cy_mean[:,mi]-SStd*os
            CL [:,4] = cy_mean[:,mi]-SStd*cs
            plt.plot(plotx,cy[:,mi],plotx,CL)
            plt.show()
            '''
        except:
            continue
    dd = np.zeros([ind.shape[0],1])
    test_Model = ind[:,6] != 0 
    dd = test_Model 
    ind_select = ind[dd,:] #排除沒有共整合關係的配對
    return ind_select
def daily_procces(Smin, inNum,costS,cost,os,cs,MaxV,OpenD,Min_cp, Max_tp):
    '''
    #Debug 時使用的參數
    Smin = SPmin.iloc[DailyNum*di:DailyNum*(di+1),:].to_numpy()
    inNum,costS,cost,os,cs,MaxV,OpenD = indataNum,CostS,Cost,Os,Fs,MaxVolume,OpenDrop
    Min_cp, Max_tp = Min_c_p, Max_t_p
    '''    
    LSmin = np.log(Smin) #已捨棄前16分鐘與最後五分鐘的股價取log
    maxcompanynu = Smin.shape[1] #找出有多少檔
    ind = mt.Binal_comb(range(maxcompanynu))
    ind = np.hstack((ind,np.zeros([ind.shape[0], 9])))
    #ind.columns = [0:S1_inx,1:S2_inx,2:opt_q, 3:modelH Check, 4:整數 Check, 5:ADF Check,6:Model,7:IB1張數,8:IB2,9:SStd,10:converg_point Check]
    DailyNum=len(Smin)
    cy = np.zeros([DailyNum,ind.shape[0]]) # cy為Naturn Log共整合序列，以Capital Weight構成
    cy_mean = np.zeros([DailyNum,ind.shape[0]]) # cy_mean為共整合序列均值，以Capital Weight構成
    B = np.zeros([2,ind.shape[0]]) #B為共整合係數
    CapitW = np.zeros([2,ind.shape[0]]) #CW為資金權重Capital Weight
    IntegerB = np.zeros([2,ind.shape[0]]) #IB為CW整數化後的共整合係數
    
    #start_time = time.time()
    for mi in range(ind.shape[0]):
    #for mi in range(1):
        rowS = LSmin.iloc[0:inNum,[int(ind[mi,0]),int(ind[mi,1])]]
        rowLS = LSmin.iloc[:DailyNum,[int(ind[mi,0]),int(ind[mi,1])]]
        stock1 = Smin.iloc[inNum-1,[int(ind[mi,0])]]
        stock2 = Smin.iloc[inNum-1,[int(ind[mi,1])]]
        ind[mi,0:2] = rowS.columns.values
        rowAS = np.array(rowS)
        # 配適 VAR(P) 模型 ，並利用BIC選擇落後期數，max_p意味著會檢查2~max_p
        try:
            max_p = 5
            p = order_select( rowAS , max_p )
            opt_model = jci.JCI_AutoSelection(rowAS,p-1)        
            #如果有共整合，紀錄下Model與opt_q
            ind[mi,2] = p-1
            ind[mi,6] = opt_model        
            if opt_model == 4 or  opt_model == 5:
                F_a, F_b, F_ct, F_ut, F_gam,ct,omega_hat = jci.JCItestpara_spilCt(rowAS,opt_model,p-1)
                Com_para = []
                Com_para.append(F_a)
                Com_para.append(F_b)
                Com_para.extend(F_ct)               
                #把  arrary.shape(2,1) 的數字放進 shape(2,) 的Serires 
                #取出共整合係數
                B[:,mi] =  pd.DataFrame(F_b).stack()
                #將共整合係數標準化，此為資金權重Capital Weight
                CapitW[:,mi] =  B[:,mi] / np.sum( np.absolute(B[:,mi]) )
                
                #將資金權重，依股價轉為張數權重
                S1 = CapitW[0][mi]/float(stock1)
                S2 = CapitW[1][mi]/float(stock2)
                
                #將張數權重，做最簡整數比，要求範圍是最大張數+1
                optXY = mt.simp_frac(S1,S2,MaxV+1)
                
                #如果最簡整數比出現[ (MaxV+1) / 1 ] or [ 1 / (MaxV+1) ] 就剃除
                #張數權重整數化後，絕對值小於5的設1（通過），絕對值大於6的設0（沒通過）
                if abs(optXY[0]) <= MaxV  and abs(optXY[1]) <= MaxV:
                    ind[mi,4] = 1
                    IntegerB[:,mi] = optXY[:]
                    ind[mi,7] = optXY[0]
                    ind[mi,8] = optXY[1]
                
               
                #計算Spread的時間趨勢均值與標準差
                Johansen_intcept, Johansen_slope = jci.Johansen_mean(F_a,F_b,F_gam,F_ct,p-1)
                Johansen_var_correct = jci.Johansen_std_correct(F_a,F_b,F_ut, F_gam,p-1)
                Johansen_std = np.sqrt(Johansen_var_correct)
                ind[mi,9] = Johansen_std
                cy_mean[:,mi] = Johansen_intcept + Johansen_slope*np.linspace(0,249,250)
                #以資金權重建構Naturn Log共整合序列
                cy[:,mi] = pd.DataFrame( np.mat(rowLS) * np.mat(CapitW[:,mi]).T).stack()
                #拿共整合序列拿去檢定，ADF單根檢定回傳1代表無單根（定態），0代表有單根（非定態）
                #ind[mi,5] = mt.ADFtest_TR(cy[OpenD-1:inNum,mi], opt_p-1 , 0.05)
                #如果收斂點在Trading Period，設為0（沒通過、不交易），反之設為1
                #if converg_Point < inNum:
                    #ind[mi,10] = converg_Point
        #Spend_time = time.time() - start_time
        except:
            continue
    dd = np.zeros([ind.shape[0],1])
    test_Inter = ind[:,4]==1
    #test_ADF = ind[:,5]==1
    test_Model = ind[:,6]>=4 #挑出model4&5交易
    #test_converg = ind[:,10]>0
    #dd = test_Inter & test_ADF & test_Model & test_converg
    dd = test_Inter & test_Model 
    
    OMinx = ind[dd,:]
    cy = cy[:,dd]
    cy_mean = cy_mean[:,dd]
    IntegerB = IntegerB[:,dd]
    
    DailyResult = np.zeros( (OMinx.shape[0],17) )
    
    DailyResult[:,0:2] = OMinx[:,0:2]
    DailyResult[:,2:5] = OMinx[:,6:9]
    DailyResult[:,5] = OMinx[:,10]
    #DailyResult=[S1,S2,model,SFx資金權重,SFy,Cconverg_point收斂點,...
    
    #DailyResult(:,6:11)
    # ...,總獲利,平倉獲利,停損獲利,換日強停獲利,換日強停虧損,...
    #DailyResult(:,11:17)
    # ...,開倉次數,平倉次數,停損次數,換日強停獲利次數,換日強停虧損次數,向上(1)/向下(-1)]
    
    for pi in range(OMinx.shape[0]):
        SStd = OMinx[pi,9] #標準差
        mean_slope = cy_mean[inNum, pi] - cy_mean[0, pi]
        #Con_Point = int(DailyResult[pi,5])
        smin = Smin[[str(int(OMinx[pi,0])),str(int(OMinx[pi,1]))]][inNum:DailyNum]
        '''
        #畫個圖確認一下
        import matplotlib.pyplot as plt
        plotx = [i for i in range(DailyNum)]
        CL = np.zeros((DailyNum,5))
        CL [:,2] = cy_mean[:,pi]
        CL [:,1] = cy_mean[:,pi]+SStd*os
        CL [:,0] = cy_mean[:,pi]+SStd*cs
        CL [:,3] = cy_mean[:,pi]-SStd*os
        CL [:,4] = cy_mean[:,pi]-SStd*cs
        plt.plot(plotx,cy[:,pi],plotx,CL)
        
        '''
        if SStd*os <= costS:
            continue
        elif SStd*os > costS and mean_slope > 0: #and Con_Point < Min_cp:
            print(mt.trade_up(cy[inNum:DailyNum,pi] , cy_mean[inNum:DailyNum,pi] , 
                                     np.array(smin) , IntegerB[:,pi] , SStd , cost , os, cs, Max_tp ))
            # DailyResult[pi, 6:11]=ProfitU
            # DailyResult[pi, 11:16]=CountU
            # DailyResult[pi, 16] = 1
        elif SStd*os > costS and mean_slope < 0: # and Con_Point < Min_cp:
            print(mt.trade_down(cy[inNum:DailyNum,pi] , cy_mean[inNum:DailyNum,pi] , 
                                     np.array(smin) , IntegerB[:,pi] , SStd , cost , os, cs, Max_tp ))                
            # DailyResult[pi, 6:11]=ProfitD
            # DailyResult[pi, 11:16]=CountD
            # DailyResult[pi, 16] = -1
        
    return DailyResult
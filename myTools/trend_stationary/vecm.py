#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 20:31:47 2019

@author: chaohsien
"""

import pandas as pd
import numpy as np
from scipy.linalg import eigh 

#data = da1
#data = pd.read_csv('20180905_averagePrice_min.csv',encoding='utf-8')
#da1 = day1_1.iloc[:,1:3]

# 估計VECM參數，算出特徵向量與特徵值

#model = 'H2'
#p = 3              # VAR落後期數
def JCItest_withTrace(X_data,model_type,lag_p):
    if model_type == 'model1':
        model_type = 1
    elif model_type == 'model2':
        model_type = 2
    elif model_type == 'model3':
        model_type = 3
    [NumObs,NumDim] = X_data.shape

    dY_ALL = X_data[1:, :] - X_data[0:-1, :] 
    dY = dY_ALL[lag_p:, :] #DY
    Ys = X_data[lag_p:-1, :] #Lag_Y
    
    #底下開始處理估計前的截距項與時間趨勢項
    if lag_p == 0:
        if model_type == 1:
            dX = np.zeros([NumObs-1, NumDim]) #DLag_Y
        elif model_type == 2:
            dX = np.zeros([NumObs-1, NumDim]) #DLag_Y
            Ys = np.hstack( ( Ys, np.ones((NumObs-lag_p-1,1)) ) )#Lag_Y
        elif model_type == 3:
            dX = np.ones((NumObs-lag_p-1,1)) #DLag_Y
        elif model_type == 4:
            dX = np.ones((NumObs-lag_p-1,1)) #DLag_Y
            Ys = np.hstack( ( Ys, np.arange(1,NumObs-lag_p,1).reshape(NumObs-lag_p-1,1) ) )#Lag_Y
        elif model_type == 5:
            dX = np.hstack( ( np.ones((NumObs-lag_p-1,1)) , np.arange(1,NumObs-lag_p,1).reshape(NumObs-lag_p-1,1) ) )
    
    elif lag_p>0:
        dX = np.zeros([NumObs-lag_p-1, NumDim * lag_p]) #DLag_Y
        for xi in range(lag_p):
            dX[:, xi * NumDim:(xi + 1) * NumDim] = dY_ALL[lag_p - xi -1 :NumObs - xi - 2, :]
        if model_type == 2:
            Ys = np.hstack( ( Ys, np.ones((NumObs-lag_p-1,1)) ) )
        elif model_type == 3:
            dX = np.hstack( ( dX, np.ones((NumObs-lag_p-1,1)) ) )
        elif model_type == 4:
            Ys = np.hstack( ( Ys, np.arange(1,NumObs-lag_p,1).reshape(NumObs-lag_p-1,1) ) )
            dX = np.hstack( ( dX, np.ones((NumObs-lag_p-1,1)) ) )
        elif model_type == 5:
            dX = np.hstack( ( dX, np.ones((NumObs-lag_p-1,1)) , np.arange(1,NumObs-lag_p,1).reshape(NumObs-lag_p-1,1) ) )
    
    # 準備開始估計，先轉成matrix，計算比較直觀
    dX, dY, Ys = np.mat(dX), np.mat(dY), np.mat(Ys)

    # 先求dX'*dX 方便下面做inverse
    dX_2 = dX.T * dX
    # I-dX * (dX'*dX)^-1 * dX'
    #python無法計算0矩陣的inverse，用判斷式處理
    if  np.sum(dX_2) == 0:
        M = np.identity(NumObs-lag_p-1) - dX * dX.T
    else:
        M = np.identity(NumObs-lag_p-1) - dX * dX_2.I * dX.T
    
    R0, R1 = dY.T * M, Ys.T * M
    
    S00 = R0 * R0.T / (NumObs-lag_p-1)
    S01 = R0 * R1.T / (NumObs-lag_p-1)
    S10 = R1 * R0.T / (NumObs-lag_p-1)
    S11 = R1 * R1.T / (NumObs-lag_p-1)
    
    #計算廣義特徵值與廣義特徵向量
    eigValue_lambda, eigvecs = eigh(S10 * S00.I * S01, S11, eigvals_only=False)
    
    # 排序特徵向量Eig_vector與特徵值lambda
    sort_ind = np.argsort(-eigValue_lambda)
    eigValue_lambda = eigValue_lambda[sort_ind]
   
    eigVecs = eigvecs[:, sort_ind]
    #將所有eigenvector同除第一行的總和
    #eigVecs_st = eigVecs/np.sum(np.absolute(eigVecs[:,0][0:2])) 
   
    eigValue_lambda = eigValue_lambda.reshape( len(eigValue_lambda) , 1)
    
    #Beta
    #jci_beta = eigVecs_st[:,0][0:2].reshape(NumDim,1)
    jci_beta = eigVecs[:,0][0:2].reshape(NumDim,1)
    
    '''
    #Alpha
    a = np.mat(eigVecs_st[:,0])
    jci_a = S01 * a.T
    jci_alpha = jci_a/np.sum(np.absolute(jci_a)) 
    '''
    #Alpha
    a = np.mat(eigVecs[:,0])
    jci_alpha = S01 * a.T
    
    #初始化 c0, d0, c1, d1
    c0 , d0 = 0, 0
    c1 , d1 = np.zeros([NumDim, 1]), np.zeros([NumDim, 1])

    #計算 c0, d0, c1, d1，與殘差及VEC項的前置
    if model_type == 1:
        W = dY - Ys * jci_beta * jci_alpha.T
        P = dX.I * W  # [B1,...,Bq]
        P = P.T
        cvalue = [12.3329, 4.1475]
    elif model_type == 2:
        #c0 = eigVecs_st[-1, 0:1]
        c0 = eigVecs[-1, 0:1]
        W = dY - (Ys[:,0:2] * jci_beta + numpy.matlib.repmat(c0, NumObs-lag_p-1, 1) )* jci_alpha.T
        P = dX.I * W  # [B1,...,Bq]
        P = P.T
        cvalue = [20.3032, 9.1465]
    elif model_type == 3:
        W = dY - Ys * jci_beta * jci_alpha.T
        P = dX.I * W
        P = P.T
        c = P[:,-1]
        c0 = jci_alpha.I * c
        c1 = c - jci_alpha * c0
        cvalue = [15.4904, 3.8509]
    elif model_type == 4:
        #d0 = eigVecs_st[-1, 0:1]
        d0 = eigVecs[-1, 0:1]
        W = dY - (Ys[:,0:2] * jci_beta + np.arange(1,NumObs-lag_p,1).reshape(NumObs-lag_p-1,1) * d0) * jci_alpha.T
        P = dX.I * W
        P = P.T
        c = P[:,-1]
        c0 = jci_alpha.I * c
        c1 = c - jci_alpha * c0
        cvalue = [25.8863, 12.5142]
    elif model_type == 5:
        W = dY - Ys * jci_beta * jci_alpha.T
        P = dX.I * W  # [B1,...,Bq]
        P = P.T
        c = P[:,-2]
        c0 = jci_alpha.I * c
        c1 = c - jci_alpha * c0
        d = P[:,-1]
        d0 = jci_alpha.I * d
        d1 = d - jci_alpha * d0
        cvalue = [18.3837, 3.8395]
    #計算殘差    
    ut = W - dX * P.T
    Ct_all = jci_alpha*c0 + c1 + jci_alpha*d0 +d1

    #計算VEC項
    gamma = []
    for bi in range(1,lag_p+1):
        Bq = P[:, (bi-1)*NumDim : bi * NumDim]
        gamma.append(Bq)
    temp1 = np.dot(np.dot(jci_beta.transpose(),S11[0:2,0:2]),jci_beta)
    omega_hat = S00[0:2,0:2] - np.dot(np.dot(jci_alpha,temp1),jci_alpha.transpose())
    #把Ct統整在一起
    Ct=[]
    Ct.append(c0)
    Ct.append(d0)
    Ct.append(c1)
    Ct.append(d1)
    
    TraceTest_H = []
    TraceTest_T = []
    for rn in range(0,NumDim):
        eig_lambda = np.cumprod(1-eigValue_lambda[rn:NumDim,:])
        trace_stat = -2 * np.log(eig_lambda[-1] ** ((NumObs-lag_p-1)/2))
        TraceTest_H.append(cvalue[rn] < trace_stat)
        TraceTest_T.append(trace_stat)
    return TraceTest_H, TraceTest_T
def vecm(data,model,p):
    
    k = len(data.T)     # k檔股票

    dY_all = data.diff().drop([0]) ; dY_all.index  = np.arange(0,len(dY_all),1)
    dY = dY_all.iloc[p-1:len(data),:]
    
    Y_1 = data.iloc[p-1:len(data)-1,:] ; Y_1.index  = np.arange(0,len(Y_1),1)
    
    if model == 'H1*':
    
        Y_1 = np.hstack((np.array(Y_1),np.ones([len(dY),1])))
        
    if model == 'H*':
        
        time = np.arange(1,len(dY)+1,1).reshape((len(dY),1))
        
        Y_1 = np.hstack((np.array(Y_1), time ))

    dX = np.zeros([len(dY),k*(p-1)])
    for i in range(p-1):
    
        dX[:,i*k:k*(i+1)] = np.array(dY_all.iloc[(p-i-2):len(data)-i-2,:])
    
    if model == 'H1' or model == 'H*':

        dX = np.hstack((dX,np.ones([len(dY),1])))
    
    M = np.eye(len(dY)) - np.dot(np.dot(dX , np.linalg.inv(np.dot(dX.T , dX))) , dX.T )

    R0 = np.dot( dY.T , M )
    R1 = np.dot( Y_1.T , M )

    S00 = np.dot( R0 , R0.T ) / len(dY)
    S01 = np.dot( R0 , R1.T ) / len(dY)
    S10 = np.dot( R1 , R0.T ) / len(dY)
    S11 = np.dot( R1 , R1.T ) / len(dY)

    A = np.dot(S10 , np.dot(np.linalg.inv(S00) , S01))
    
    eigvals, eigvecs = eigh(A , S11 , eigvals_only=False)
    
    if model == 'H*' or model == 'H1*':
        eigvals = eigvals[1:]
        eigvecs = eigvecs[:,1:]
 
    testStat = -2 * np.log(np.cumprod(1-eigvals) ** (len(dY)/2))
    
    return [ testStat , eigvals , eigvecs ]

def rank(data,model,p):
    
    testStat = vecm( data ,  model , p )[0]       # 第零個位置是檢定統計量
    k = len(data.T)                               # k檔股票
    
    if model == 'H2':

        if k == 2:
    
            if testStat[1] < 12.3329:
        
                rank = 0
        
            elif testStat[0] < 4.1475:
        
                rank = 1
        
            else:
        
                rank = 2

    elif model == 'H1*':
    
        if k == 2:
    
            if testStat[1] < 20.3032:
        
                rank = 0
        
            elif testStat[0] < 9.1465:
        
                rank = 1
        
            else:
        
                rank = 2

    elif model == 'H1':
    
        if k == 2:
    
            if testStat[1] < 15.4904:
        
                rank = 0
        
            elif testStat[0] < 3.8509:
        
                rank = 1
        
            else:
        
                rank = 2
                
    else: # model == 'H*'
        
        if k == 2:
    
            if testStat[1] > 25.8863:
        
                rank = 0
        
            elif testStat[0] < 12.5142:
        
                rank = 1
        
            else:
        
                rank = 2

    return rank

def eig(data,model,p,rank):

    eigvals = vecm( data , model , p )[1][0]   # 第一個位置是特徵值

    return eigvals

def weigh(data,model,p,rank):
    
    eigvecs = vecm( data , model , p )[2]     # 第2個位置是特徵向量
    k = len(data.T)                           # k檔股票
    
    if model == 'H2':

        if k == 2:
    
            wei = eigvecs[:,1]
                
    elif model == 'H1*':
    
        if k == 2:
            
            wei = eigvecs[:,1] 
            
    elif model == 'H1':
    
        if k == 2:
            
           wei = eigvecs[:,1] 
           
    else: # model == 'H*'
        
        if k == 2:
            
            wei = eigvecs[:,1] 

    return wei.T

def para_vecm(data,model,p):
    '''
    if model == 'model1':
        model = 'H2'
    elif model == 'model2':
        model = 'H1*'
    elif model == 'model3':
        model = 'H1'
    '''
    if model == 1:
        model = 'H2'
    elif model == 2:
        model = 'H1*'
    elif model == 3:
        model = 'H1'
     
    data = pd.DataFrame(data)
    
    k = len(data.T)     # k檔股票

    dY_all = data.diff().drop([0]) ; dY_all.index  = np.arange(0,len(dY_all),1)
    dY = dY_all.iloc[p-1:len(data)-1,:]
    
    Y_1 = data.iloc[p-1:len(data)-1,:] ; Y_1.index  = np.arange(0,len(Y_1),1)
    
    if model == 'H1*':
    
        Y_1 = np.hstack((np.array(Y_1),np.ones([len(dY),1])))
        
    if model == 'H*':
        
        time = np.arange(1,len(dY)+1,1).reshape((len(dY),1))
        
        Y_1 = np.hstack((np.array(Y_1), time ))

    dX = np.zeros([len(dY),k*(p-1)])
    for i in range(p-1):
    
        dX[:,i*k:k*(i+1)] = np.array(dY_all.iloc[(p-i-2):len(data)-i-2,:])
    
    if model == 'H1' or model == 'H*':

        dX = np.hstack((dX,np.ones([len(dY),1])))
    
    M = np.eye(len(dY)) - np.dot(np.dot(dX , np.linalg.inv(np.dot(dX.T , dX))) , dX.T )

    R0 = np.dot( dY.T , M )
    R1 = np.dot( Y_1.T , M )

    S00 = np.dot( R0 , R0.T ) / len(dY)
    S01 = np.dot( R0 , R1.T ) / len(dY)
    S10 = np.dot( R1 , R0.T ) / len(dY)
    S11 = np.dot( R1 , R1.T ) / len(dY)

    A = np.dot(S10 , np.dot(np.linalg.inv(S00) , S01))
    
    eigvals, eigvecs = eigh(A , S11 , eigvals_only=False)
    
    if model == 'H2':
        
        beta = np.mat(eigvecs[:,1]).T
        
    elif model == 'H1':
        
        beta = np.mat(eigvecs[:,1]).T
        
    else :
        
        beta = np.mat(eigvecs[:,2]).T                                  # 共整合係數
    
    alpha = np.dot(S01,beta)
    
    D = np.dot( np.dot(dY.T - np.dot(np.dot(alpha,beta.T),Y_1.T) , dX ) , np.linalg.inv(np.dot(dX.T,dX)) )
    
    at = np.array(dY).T - np.dot(np.dot(alpha,beta.T),Y_1.T) - np.dot(D,dX.T)    # 殘差
    
    Dc = D.copy()
    betac = beta.copy()
    #sigma_u = np.dot(at,at.T)/len(data)                                # 殘差共變異數
    
    if model == 'H1':
        
        intercept = np.mat(D[:,len(D.T)-1]).T
        D = D[:,:-1]
        
    elif model == 'H1*':
        
        intercept = alpha * beta[len(beta)-1,:]
        beta = beta[:-1]
    
    else:
        
        intercept = np.zeros((2,1))
    
    # VAR representation 
    if p == 1:
        
        A1 = np.eye(k) + np.dot(alpha,beta.T)
        
    elif p == 2:
        
        A1 = np.eye(k) + np.dot(alpha,beta.T) + D
        A1 = np.hstack((A1,-D))
        
    else:
        
        A1 = np.eye(k) + np.dot(alpha,beta.T) + D[:,0:2]
        for i in range(p-2):
            
            A2 = D[:,2*(i+1):2*(i+2)] - D[:,2*i:2*(i+1)]
            
            A1 = np.hstack((A1,A2))
            
        A1 = np.hstack((A1,-D[:,(len(D.T)-2):len(D.T)]))
        
    A1 = np.hstack((intercept,A1))
        
    return [ at , A1, [alpha,betac,Dc] ]


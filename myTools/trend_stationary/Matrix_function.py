# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 16:53:01 2020

@author: MAI
"""
import numpy as np
from vecm import para_vecm
from scipy.stats import f , chi2
from JCItestpara_20201113 import Iteration_Mean_Std,JCItestpara_spilCt
def check_spread_Absconverge(output,num,model,lastNum,test_stock_iterated,D=16,std=False,times=10):
    #spread_m,_,var_order = spread_mean(output,num,model,D,order=True)
    #mean = np.mean(spread_m[-lastNum:])  #疊帶後收斂的值
    if model == "model3":
        model = 3
    elif model == "model2":
        model = 2
    elif model == "model1":
        model = 1
        
    mean_closed = output[2*num,5]  #疊帶後收斂的值(使用closed form)
    #for all model
    stock1 = output[2*num,8:158]
    stock2 = output[(2*num+1),8:158]
    St = np.vstack( [stock1, stock2] ).T
    logSt = np.log(St)
    p = order_select(logSt,5)
    F_a, F_b, F_ct, F_ut, F_gam,ct,omega_hat = JCItestpara_spilCt(logSt,model,p-1)
    Com_para = []
    Com_para.append(F_a)
    Com_para.append(F_b)
    Com_para.extend(F_ct)
    stock1_iterated = test_stock_iterated[2*num,:]
    stock2_iterated = test_stock_iterated[(2*num+1),:]
    St_iterated = np.vstack( [stock1_iterated, stock2_iterated] ).T 
    logSt_iterated = np.log(St_iterated)
    spread_m_new = Iteration_Mean_Std(model, p-1,Com_para, F_gam, logSt_iterated, 16, 166) 
    spread_m_new = spread_m_new[16:166]
    
    #mean = output[2*num,5]  #疊帶後收斂的值(使用closed form)
    if std == False:
        std = output[2*num,6]
    distance = np.abs(spread_m_new - mean_closed)
    converge = np.zeros(times)
    for i in range(times):
        inside = (distance-std/(i+1)) > 0
        converge[i] = 150-np.argmax(inside[::-1])
        if converge[i] == 0:
            if distance[0]>std/(i+1):
                converge[i] = 150
    '''
    else:
        converge = np.zeros(times)
        for i in range(times):
            converge[i] = 150    
    '''
    return converge

def check_spread_Absconverge_allmodel(output,num,model,lastNum,test_stock_iterated,D=16,std=False,times=10):
    
    mean_closed = output.Johansen_intercept[num] + output.Johansen_slope[num]*np.linspace(0,249,250)  #疊帶後收斂的值(使用closed form)
    mean = np.matrix(mean_closed[0:150]).T
    #for all model
    x = int(len(test_stock_iterated)/2)
    stock1_iterated = test_stock_iterated[num,:]
    stock2_iterated = test_stock_iterated[num+x,:]
    St_iterated = np.vstack( [stock1_iterated, stock2_iterated] ).T 
    logSt_iterated = np.log(St_iterated)
    logSt = logSt_iterated[16:166]
    q = int(output.iloc[num,3])
    F_a, F_b, F_ct, F_ut, F_gam,ct,omega_hat = JCItestpara_spilCt(logSt,model,q)
    Com_para = []
    Com_para.append(F_a)
    Com_para.append(F_b)
    Com_para.extend(F_ct)
    spread_m_new = Iteration_Mean_Std(model,q,Com_para, F_gam, logSt_iterated, 16, 166) 
    spread_m_new = spread_m_new[16:166]
    
    #mean = output[2*num,5]  #疊帶後收斂的值(使用closed form)
    if std == False:
        std = output.iloc[num,6]
    if model == 1 or model == 2 or model == 3:
        distance = np.abs(spread_m_new - mean)
    else:
        distance = np.abs(np.diff(spread_m_new,axis = 0)-output.Johansen_slope[num])    
    converge = np.zeros(times)
    for i in range(times):
        inside = (distance-std/(i+1)) > 0
        converge[i] = 150-np.argmax(inside[::-1])  #倒過來
        if converge[i] == 0:
            if distance[0]>std/(i+1):
                converge[i] = 150
    '''
    else:
        converge = np.zeros(times)
        for i in range(times):
            converge[i] = 150    
    '''
    return converge

def spread_mean(output,i,model,D,ini=0,future=True,order=False):
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
   
    stock1 = output[2*i,8:158]
    stock2 = output[(2*i+1),8:158]
    b1 = output[2*i,3]
    b2 = output[(2*i+1),3]
    spread = output[2*i,3]*np.log(output[2*i,8:(274-D)]) + output[(2*i+1),3]*np.log(output[(2*i+1),8:(274-D)])
    y = np.vstack( [stock1, stock2] ).T
    logy = np.log(y)
    p = order_select(logy,5)
    #print('p:',p)
    _,_,para = para_vecm(logy,model,p)
    logy = np.mat(logy)
    y_1 = np.mat(logy[p+ini:])
    dy = np.mat(np.diff(logy,axis=0)[ini:,:])
    for j in range(len(stock1)-p-1-ini):
        if model == 'H1': #MODEL3
            if p!=1:
                delta = para[0] * para[1].T * y_1[j].T + para[2] * np.hstack([dy[j:(j+p-1)].flatten(),np.mat([1])]).T
            else:
                delta = para[0] * para[1].T * y_1[j].T + para[2] * np.mat([1])
        elif model == 'H1*': #MODEL2
            if p!=1:
                delta = para[0] * para[1].T * np.hstack([y_1[j],np.mat([1])]).T + para[2] * dy[j:(j+p-1)].flatten().T
            else:
                delta = para[0] * para[1].T * np.hstack([y_1[j],np.mat([1])]).T
        elif model == 'H2': #MODEL1
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
    if future:
        if order:
            return spread_m,spread[p+ini:],p
        else:
            return spread_m,spread[p+ini:]
    else:
        if order:
            return spread_m,spread[p+ini:150],p
        else:
            return spread_m,spread[p+ini:150]
        
def Where_cross_threshold(trigger_spread, threshold, add_num):
    #initialize array
    check = np.zeros(trigger_spread.shape)
    #put on the condiction
    check[(trigger_spread - threshold) > 0] = add_num
    check[:,0] = check[:,1]
    #Open_trigger_array
    check = check[:,1:] - check[:,:-1]
    return check

def Where_threshold(trigger_spread, threshold, add_num, up):
    #initialize array
    check = np.zeros(trigger_spread.shape)
    #put on the condiction
    if up:
        check[(trigger_spread - threshold) > 0] = add_num
    else:
        check[(trigger_spread - threshold) < 0] = add_num
    check[:,0] = 0    
    return check

def tax(payoff,rate):
    tax_price = payoff * (1 - rate * (payoff > 0))
    return tax_price

def CNN_test(st1,st2,sp,v1,v2,tick,DetPos,table,NowOpen,model_CNN):
    if NowOpen:
        times = 1
    else:
        times = len(DetPos)
    #Array Initialize
    AllSprInput = []
    AllCharInput = []
    pair_pos = np.zeros([len(DetPos)],dtype = int)
    count = 0
    
    character = ['w1','w2','mu','stdev']
    TableChar = np.zeros([len(table),5])
    TableChar[:,:4] = np.array(table[character])

    if tick:
        s = 50
    else:
        s = 50
    for m in range(times):
        SprInput = np.zeros([100,5])
        CharInput = np.zeros([5])
        if not NowOpen:
            CharInput[:4] = TableChar[m,:4]
            lenth = len(DetPos[m])
        else:
            lenth = len(DetPos)
        for i in range(lenth):
            if NowOpen:
                index = DetPos[i]
                pair = i
            else:
                index = DetPos[m][i,0]
                pair = m
            SprInput[:,0] = st1[pair,(s+index):(s+100+index)]
            SprInput[:,1] = st2[pair,(s+index):(s+100+index)]
            SprInput[:,2] = sp[pair,(s+index):(s+100+index)]
            SprInput[:,3] = v1[pair,(s+index):(s+100+index)]
            SprInput[:,4] = v2[pair,(s+index):(s+100+index)]
            CharInput[4] = index/60
            AllSprInput.append(SprInput.copy())
            if NowOpen:
                CharInput[:4] = TableChar[i,:4]
            AllCharInput.append(CharInput.copy())
            count += 1
        pair_pos[m] = count
    AllSprInput = np.array(AllSprInput)
    AllCharInput = np.array(AllCharInput)
    #Normalize CNN_SpreadInput
    #mu
    mu = np.zeros([len(AllSprInput),1,5])
    mu[:,0,:2] = np.mean(AllSprInput[:,:,:2], axis=1)
    mu[:,0,2] = AllCharInput[:,2]
    #std
    stock_std = np.std(AllSprInput[:,:,:3], axis=1)
    std = np.ones([len(AllSprInput),1,5])
    std[:,0,:2] = stock_std[:,:2]
    std[:,0,2] = AllCharInput[:,3]
    #Normalize
    AllSprInput = (AllSprInput - mu)/std
    AllCharInput[:,:2] = AllCharInput[:,:2]*stock_std[:,:2] / np.expand_dims(stock_std[:,2],axis = 1)
        
    #CNN_predict
    pre = model_CNN.predict([AllSprInput,AllCharInput])
    prediction = np.argmax(pre,axis = 1)
    
    if NowOpen:
        return prediction
    else:
        return [ prediction , pair_pos ]

def VAR_model( y , p ):    
    k = len(y.T)     # 幾檔股票
    n = len(y)       # 資料長度
    
    xt = np.ones( ( n-p , (k*p)+1 ) )
    for i in range(n-p):
        a = 1
        for j in range(p):
            a = np.hstack( (a,y[i+p-j-1]) )
        a = a.reshape([1,(k*p)+1])
        xt[i] = a
    
    zt = np.delete(y,np.s_[0:p],axis=0)
    xt = np.mat(xt)
    zt = np.mat(zt)

    beta = ( xt.T * xt ).I * xt.T * zt                      # 計算VAR的參數
    
    A = zt - xt * beta                                      # 計算殘差
    sigma = ( (A.T) * A ) / (n-p)                           # 計算殘差的共變異數矩陣
        
    return [ sigma , beta ]

# 配適 VAR(P) 模型 ，並利用BIC選擇落後期數--------------------------------------------------------------
def order_select( y , max_p ):
    
    k = len(y.T)     # 幾檔股票
    n = len(y)       # 資料長度
    
    bic = np.zeros((max_p,1))
    for p in range(1,max_p+1):
        sigma = VAR_model( y , p )[0]
        bic[p-1] = np.log( np.linalg.det(sigma) ) + np.log(n) * p * (k*k) / n
    bic_order = int(np.where(bic == np.min(bic))[0] + 1)        # 因為期數p從1開始，因此需要加1
    
    return bic_order

def fore_chow(stock1, stock2, model, Flen, give=False, p=0, A=0, ut=0, maxp=5):
    #Flen:formation length
    if model == 1:
        model_name = 'H2'
    elif model == 2:
        model_name = 'H1*'
    else:
        model_name = 'H1'
        
    day1 = ( np.vstack( [stock1, stock2] ).T )
    day1 = np.log(day1)
    h = len(day1) - Flen
    k = 2                                                                              # 幾檔股票
    n = Flen                                                                                # formation period 資料長度

    if give == False:
        y = ( np.vstack( [stock1[0:Flen], stock2[0:Flen]] ).T )            
        y = np.log(y)
        p = order_select(y,maxp)
        at , A, _ = para_vecm(y,model_name,p)    
#        at , A = para_vecm(y,model_name,p)    
        ut = np.dot(at,at.T)/len(at.T)     #sigma_u

    Remain_A = A.copy()
    Remain_ut = ut.copy()
    Remain_p = p
    #LUKE pg184
    A = A.T    
    phi_0 = np.eye(k)        
    A1 = np.delete(A,0,axis=0).T    
    phi = np.hstack( (np.zeros([k,2*(p-1)]) , phi_0) )
    sigma_t = np.dot( np.dot( phi_0 , ut ) , phi_0.T )                                         # sigma hat     
    ut_h = []

    for i in range(1,h+1):
        lag_mat = day1[ len(day1)-i-p-1 :  len(day1)-i , : ]    
        lag_mat = np.array(lag_mat[::-1])        
        if p == 1:
            ut_h.append( lag_mat[0].T - ( A[0].T + np.dot( A[1:k*p+1].T , lag_mat[1:2].T ) ).T )            
        else:
            ut_h.append( lag_mat[0].T - ( A[0].T + np.dot( A[1:k*p+1].T , lag_mat[1:k*p-1].reshape([k*p,1]) ) ).T )    

    for i in range(h-1):        
        a = phi[:,i*2:len(phi.T)]
        phi_i = np.dot( A1 , a.T )
        sigma_t = sigma_t + np.dot( np.dot( phi_i , ut ) , phi_i.T ) 
        phi = np.hstack( (phi , phi_i) )
    phi = phi[: , ((p-1)*k):len(phi.T)]
    ut_h = np.array(ut_h).reshape([1,h*2])
    e_t = np.dot( phi , ut_h.T )
    
    # 程式防呆，如果 sigma_t inverse 發散，則回傳有結構性斷裂。
    try:        
        tau_h = np.dot(np.dot( e_t.T , np.linalg.inv(sigma_t) ) , e_t ) / k        
    except:        
        return Remain_p, Remain_A, Remain_ut, 1    
    else:        
        if tau_h > float(f.ppf(0.99,k,n-k*p+1)):#tau_h > float(chi2.ppf(0.99,k)):    
            return Remain_p, Remain_A, Remain_ut, 1      # 有結構性斷裂
        else:    
            return Remain_p, Remain_A, Remain_ut, 0
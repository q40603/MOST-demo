# -*- coding: utf-8 -*-
"""
Created on Mon Nov 26 18:08:05 2018

@author: chuchu0936
"""
from scipy.stats import skew
from .cost import tax , slip 
from .integer import num_weight
import numpy as np

def pairs(pos, formate_time, table, min_data, tick_data, maxi, tax_cost, cost_gate, capital):
    with open("../actions.pkl", "rb") as action_pkl:
        actions = pickle.load(action_pkl)

    s1 = str(table.stock1[pos])
    s2 = str(table.stock2[pos])

    tw1 = table.w1[pos]
    tw2 = table.w2[pos]
    e_stdev = table.e_stdev[pos]
    e_mu = table.e_mu[pos]
    up_open_time = actions[table.action[pos]][0]
    down_open_time = up_open_time
    stop_loss_time = actions[table.action[pos]][1]

    
    trade_capital = 0
    cpA,cpB = 0,0
    trading =[0,0,0]

    use_fore_lag5 = False
    use_adf = False

    trade_process = []


    t = formate_time  # formate time
    # stock1_seq = min_data[s1].loc[0:t]
    # stock2_seq = min_data[s2].loc[0:t]

    local_open_num = []
    local_profit = []
    local_rt = []
    local_std = []
    local_skew = []
    local_timetrend = []
 
    spread = tw1 * np.log(tick_data[s1]) + tw2 * np.log(tick_data[s2])

    up_open = e_mu + e_stdev * up_open_time  # 上開倉門檻
    down_open = e_mu - e_stdev * down_open_time  # 下開倉門檻
    stop_loss = e_stdev * stop_loss_time  # 停損門檻
    close = e_mu  # 平倉(均值)
    # M = round(1 / table.zcr[pos])  # 平均持有時間
    trade = 0  # 計算開倉次數
    break_point = 0  # 計算累積斷裂點

    position = 0  # 持倉狀態，1:多倉，0:無倉，-1:空倉，-2：強制平倉
    pos = [0, 0]
    stock1_profit = []
    stock2_profit = []
    for i in range(1, len(spread) - 6):
        if position == 0 and i != len(spread) - 7:  # 之前無開倉
            if (spread[i] - up_open) * (spread[i + 1] - up_open) < 0 and spread[i + 1] < (close + stop_loss):  # 碰到上開倉門檻且小於上停損門檻
                # 資金權重轉股票張數，並整數化
                
                # print(tick_data.mtimestamp[i],"碰到上開倉門檻 ,上開倉")
                w1, w2 = num_weight(tw1, tw2, tick_data[s1][i + 1], tick_data[s2][i + 1], maxi, capital)
                position = -1
                stock1_payoff = w1 * slip(tick_data[s1][i + 1], tw1)
                stock2_payoff = w2 * slip(tick_data[s2][i + 1], tw2)
                stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
                cpA,cpB = stock1_payoff,stock2_payoff
                if cpA > 0 and cpB > 0:
                    trade_capital += abs(cpA)+abs(cpB)
                elif cpA > 0 and cpB < 0 :
                    trade_capital += abs(cpA)+0.9*abs(cpB)
                elif cpA < 0 and cpB > 0 :
                    trade_capital += 0.9*abs(cpA)+abs(cpB)
                elif cpA < 0 and cpB < 0 :
                    trade_capital += 0.9*abs(cpA)+0.9*abs(cpB)
                    # down_open = table.mu[pos] - table.stdev[pos] * close_time
                trade += 1
                trade_process.append([tick_data.mtimestamp[i],"碰到上開倉門檻 ,上開倉<br>",-w1, -w2, stock1_payoff+stock2_payoff])


            elif (spread[i] - down_open) * (spread[i + 1] - down_open) < 0 and spread[i + 1] > (close - stop_loss):  # 碰到下開倉門檻且大於下停損門檻
                # 資金權重轉股票張數，並整數化
                
                # print(tick_data.mtimestamp[i],"碰到下開倉門檻 ,下開倉")
                w1, w2 = num_weight(tw1, tw2, tick_data[s1][i + 1], tick_data[s2][i + 1], maxi, capital)
                position = 1
                stock1_payoff = -w1 * slip(tick_data[s1][i + 1], -tw1)
                stock2_payoff = -w2 * slip(tick_data[s2][i + 1], -tw2)
                stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
                cpA,cpB = stock1_payoff,stock2_payoff
                if cpA > 0 and cpB > 0:
                    trade_capital += abs(cpA)+abs(cpB)
                elif cpA > 0 and cpB < 0 :
                    trade_capital += abs(cpA)+0.9*abs(cpB)
                elif cpA < 0 and cpB > 0 :
                    trade_capital += 0.9*abs(cpA)+abs(cpB)
                elif cpA < 0 and cpB < 0 :
                    trade_capital += 0.9*abs(cpA)+0.9*abs(cpB)
                # up_open = table.mu[pos] + table.stdev[pos] * close_time
                trade += 1
                trade_process.append([tick_data.mtimestamp[i],"碰到下開倉門檻 ,下開倉<br>", w1, w2, stock1_payoff+stock2_payoff])
            else:
                position = 0
                stock1_payoff = 0
                stock2_payoff = 0
        elif position == -1:  # 之前有開空倉，平空倉
            if (spread[i] - close) * (spread[i + 1] - close) < 0:  # 空倉碰到下開倉門檻即平倉
                
                # print(tick_data.mtimestamp[i],"之前有開空倉，碰到均值，平倉")
                position = 0  # 平倉
                stock1_payoff = -w1 * slip(tick_data[s1][i + 1], -tw1)
                stock2_payoff = -w2 * slip(tick_data[s2][i + 1], -tw2)
                stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
                trading[0]+=1
                trade_process.append([tick_data.mtimestamp[i],"碰到均值，平倉<br>",w1, w2, stock1_payoff+stock2_payoff])
                # down_open = table.mu[pos] - table.stdev[pos] * open_time
                # 每次交易報酬做累加(最後除以交易次數做平均)
            elif spread[i + 1] > (close + stop_loss):  # 空倉碰到上停損門檻即平倉停損
                
                # print(tick_data.mtimestamp[i],"之前有開空倉，碰到上停損門檻，強制平倉")
                position = -2  # 碰到停損門檻，強制平倉
                stock1_payoff = -w1 * slip(tick_data[s1][i + 1], -tw1)
                stock2_payoff = -w2 * slip(tick_data[s2][i + 1], -tw2)
                stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
                trading[1]+=1
                trade_process.append([tick_data.mtimestamp[i],"碰到上停損門檻，強制平倉<br>",w1, w2, stock1_payoff+stock2_payoff])
                # 每次交易報酬做累加(最後除以交易次數做平均)

            elif i == (len(spread) - 7):  # 回測結束，強制平倉
                # trade_process.append([tick_data.mtimestamp[i],"回測結束，強制平倉<br>"])
                # print(tick_data.mtimestamp[i],"回測結束，強制平倉")
                position = -4
                stock1_payoff = -w1 * slip(tick_data[s1][len(tick_data) - 1], -tw1)
                stock2_payoff = -w2 * slip(tick_data[s2][len(tick_data) - 1], -tw2)
                stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
                trading[2]+=1
                trade_process.append([tick_data.mtimestamp[i],"回測結束，強制平倉<br>",w1, w2, stock1_payoff+stock2_payoff])
                # 每次交易報酬做累加(最後除以交易次數做平均)
            else:
                position = -1
                stock1_payoff = 0
                stock2_payoff = 0
        elif position == 1:  # 之前有開多倉，平多倉
            if (spread[i] - close) * (spread[i + 1] - close) < 0:
                
                # print(tick_data.mtimestamp[i],"之前有開多倉，碰到均值，平倉")
                position = 0  # 平倉
                stock1_payoff = w1 * slip(tick_data[s1][i + 1], tw1)
                stock2_payoff = w2 * slip(tick_data[s2][i + 1], tw2)
                stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
                trading[0]+=1
                trade_process.append([tick_data.mtimestamp[i],"碰到均值，平倉<br>",-w1, -w2, stock1_payoff+stock2_payoff])
                # up_open = table.mu[pos] + table.stdev[pos] * open_time
                # 每次交易報酬做累加(最後除以交易次數做平均)
            elif spread[i + 1] < (close - stop_loss):
                
                # print(tick_data.mtimestamp[i],"之前有開多倉，碰到下停損門檻，強制平倉")
                position = -2  # 碰到停損門檻，強制平倉
                stock1_payoff = w1 * slip(tick_data[s1][i + 1], tw1)
                stock2_payoff = w2 * slip(tick_data[s2][i + 1], tw2)
                stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
                trading[1]+=1

                trade_process.append([tick_data.mtimestamp[i],"碰到下停損門檻，強制平倉<br>", -w1, -w2, stock1_payoff+stock2_payoff])
                # 每次交易報酬做累加(最後除以交易次數做平均)

            elif i == (len(spread) - 7):  # 回測結束，強制平倉
                
                # print(tick_data.mtimestamp[i],"回測結束，強制平倉")
                position = -4
                stock1_payoff = w1 * slip(tick_data[s1][len(tick_data) - 1], tw1)
                stock2_payoff = w2 * slip(tick_data[s2][len(tick_data) - 1], tw2)
                stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
                trading[2]+=1

                trade_process.append([tick_data.mtimestamp[i],"回測結束，強制平倉<br>", -w1, -w2, stock1_payoff+stock2_payoff])
                # 每次交易報酬做累加(最後除以交易次數做平均)
            else:
                position = 1
                stock1_payoff = 0
                stock2_payoff = 0
        else:
            # -4: 強迫平倉 -3: 結構性斷裂平倉(for lag 5) -2:停損 666:正常平倉
            if position == -2 or position == -3 or position == -4 or position == 666:
                stock1_payoff = 0
                stock2_payoff = 0
            else:
                position = 0  # 剩下時間少於預期開倉時間，則不開倉，避免損失
                stock1_payoff = 0
                stock2_payoff = 0

        pos.append(position)
        stock1_profit.append(stock1_payoff)
        stock2_profit.append(stock2_payoff)
    trading_profit = sum(stock1_profit) + sum(stock2_profit)
    
    
    if trading_profit != 0 and position == 666:
        position = 666

    local_profit = trading_profit
    # local_open_num.append(trade)
    local_open_num = trade
    if trade == 0:  # 如果都沒有開倉，則報酬為0
        trade_process.append([tick_data.mtimestamp.iloc[-1],"無任何交易"])
        # print("沒有開倉")
        local_rt = 0
        local_std = 0
        local_skew = 0
        local_timetrend = 0
        position = 0

    else:  # 計算平均報酬
        # spread2 = w1 * np.log(min_data[s1].iloc[0:t]) + w2 * np.log(min_data[s2].iloc[0:t])

        # x = np.arange(0, t)
        # b1, b0 = np.polyfit(x, spread2, 1)
        local_rt = trading_profit/trade_capital
        # local_std = np.std(spread2)
        # local_skew = skew(spread2)
        # local_timetrend = b1

        trade_process.append(["總損益", trading_profit])

    # if cpA > 0 and cpB > 0:
    #     trade_capital = abs(cpA)+abs(cpB)
    # elif cpA > 0 and cpB < 0 :
    #     trade_capital = abs(cpA)+0.9*abs(cpB)
    # elif cpA < 0 and cpB > 0 :
    #     trade_capital = 0.9*abs(cpA)+abs(cpB)
    # elif cpA < 0 and cpB < 0 :
    #     trade_capital = 0.9*abs(cpA)+0.9*abs(cpB)

    return  {
        'trade_history' : trade_process , 
        "local_profit" : local_profit , 
        "local_open_num" : local_open_num,
        "trade_capital" :trade_capital,
        "local_rt" : local_rt,
        "trade_capital" : trade_capital
    }
    
    
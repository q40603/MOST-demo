# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 11:49:47 2020

@author: allen
"""

from cost import tax
from integer import num_weight
import numpy as np
import datetime


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

def volaitlity_small(strategy, table):
    return strategy["up_open_time"] * table["std"] < strategy["cost_gate"]


def build_open(spread, table, strategy):
    spread_len = len(spread)
    slope = table["Johansen_slope"]
    up_open = table["Johansen_intercept"] + table["std"] * strategy["up_open_time"]  # 上開倉門檻
    down_open = table["Johansen_intercept"] - table["std"] * strategy["up_open_time"]  # 上開倉門檻
    close = table["Johansen_intercept"]  # 平倉(均值)
    up_open_list = []
    down_open_list = []
    close_list = []
    for i in range(spread_len):
        up_open_list.append(up_open + (i+150)* slope)
        down_open_list.append(down_open + (i+150) *slope)
        close_list.append(close + (i+150) *slope)

    return close_list, up_open_list, down_open_list


def down_open(w1, w2, s1_price, s2_price, tax_cost):
    position = 0
    stock1_payoff = -w1 * s1_price
    stock2_payoff = -w2 * s2_price    
    stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
    return stock1_payoff, stock2_payoff

def down_close(w1, w2, s1_price, s2_price, tax_cost, position):
    stock1_payoff = w1 * s1_price
    stock2_payoff = w2 * s2_price
    stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本    
    return stock1_payoff, stock2_payoff


def up_open(w1, w2, s1_price, s2_price, tax_cost):    
    position = -1
    stock1_payoff = w1 * s1_price
    stock2_payoff = w2 * s2_price
    stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本
    return stock1_payoff, stock2_payoff

def up_close(w1, w2, s1_price, s2_price, tax_cost, position):
    stock1_payoff = -w1 * s1_price
    stock2_payoff = -w2 * s2_price
    stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本    
    return stock1_payoff, stock2_payoff


def trade_up_slope(s1_tick, s2_tick, table, strategy):
    trade_capital = 0
    cpA,cpB = 0,0
    trading_profit = 0.0
    trade = 0
    trade_capital = 0    
    trade_return = 0.0
    history = []

    # 波動太小的配對不開倉
    if volaitlity_small(strategy, table):
        history.append({
            "time" : 0,
            "type" : "配對波動太小，不開倉"
        })
        print(f'{table["S1"]} {table["S2"]}  配對波動太小，不開倉')
        return trade, trading_profit, trade_capital, trade_return, history


    spread = table["w1"] * np.log(s1_tick) + table["w2"] * np.log(s2_tick)
    close, up_open_val, down_open_val = build_open(spread, table, strategy)

    position = 0  # 持倉狀態，1:多倉，0:無倉，-1:空倉，-2：強制平倉 
    stock1_profit = []
    stock2_profit = []
    spread_len = len(spread)
    w1 = 0
    w2 = 0
    for i in range(0, spread_len - 2):
        if position == 0 and i != spread_len - 3:  # 之前無開倉
        
            if spread[i] < down_open_val[i]:  # 碰到下開倉門檻且大於下停損門檻
                w1, w2 = num_weight(table["w1"], table["w2"], s1_tick[i], s2_tick[i], strategy["maxhold"], strategy["capital"])
                stock1_payoff, stock2_payoff = down_open(w1, w2, s1_tick[1], s2_tick[i], strategy["tax_cost"])
                cpA, cpB = stock1_payoff, stock2_payoff
                position = 1
                trade = 1
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                history.append({
                    "time" : i,
                    "w1" : -w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : -w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "下開倉"
                })
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} spread = {spread[i]} 下開倉')



        elif position == 1:  # 之前有開多倉，平多倉

            if (i == spread_len - 3):  # 回測結束，強制平倉
                position = -4
                stock1_payoff, stock2_payoff = down_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} 強制平倉')
                history.append({
                    "time" : i,
                    "w1" : w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "尾盤強制平倉"
                })  
                break

            elif (spread[i] - close[i]) > 0:
                position = 666  # 平倉
                stock1_payoff, stock2_payoff = down_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} 正常平倉')
                history.append({
                    "time" : i,
                    "w1" : w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "正常平倉"
                })  
                break

    trading_profit = sum(stock1_profit) + sum(stock2_profit)



    if cpA > 0 and cpB > 0:
        trade_capital = abs(cpA) + abs(cpB)
    elif cpA > 0 and cpB < 0 :
        trade_capital = abs(cpA) + 0.9 * abs(cpB)
    elif cpA < 0 and cpB > 0 :
        trade_capital = 0.9 * abs(cpA) + abs(cpB)
    elif cpA < 0 and cpB < 0 :
        trade_capital = 0.9 * abs(cpA) + 0.9 * abs(cpB)

    if trade > 0:  # 如果都沒有開倉，則報酬為0
        trade_return = trading_profit / trade_capital


    return trade, trading_profit, trade_capital, trade_return, history


def trade_down_slope(s1_tick, s2_tick, table, strategy):
    trade_capital = 0
    cpA,cpB = 0,0
    trading_profit = 0.0
    trade = 0
    trade_capital = 0    
    trade_return = 0.0
    history = []


    # 波動太小的配對不開倉
    if volaitlity_small(strategy, table):
        history.append({
            "time" : 0,
            "type" : "配對波動太小，不開倉"
        })
        print(f'{table["S1"]} {table["S2"]}  配對波動太小，不開倉')
        return trade, trading_profit, trade_capital, trade_return, history


    spread = table["w1"] * np.log(s1_tick) + table["w2"] * np.log(s2_tick)
    close, up_open_val, down_open_val = build_open(spread, table, strategy)

    position = 0  # 持倉狀態，1:多倉，0:無倉，-1:空倉，-2：強制平倉 
    stock1_profit = []
    stock2_profit = []
    spread_len = len(spread)
    w1 = 0
    w2 = 0
    for i in range(0, spread_len - 2):
        if position == 0 and i != spread_len - 3:  # 之前無開倉
        
            if spread[i] > up_open_val[i]:  # 碰到上開倉門檻
                w1, w2 = num_weight(table["w1"], table["w2"], s1_tick[i], s2_tick[i], strategy["maxhold"], strategy["capital"])
                stock1_payoff, stock2_payoff = up_open(w1, w2, s1_tick[1], s2_tick[i], strategy["tax_cost"])
                cpA, cpB = stock1_payoff, stock2_payoff
                position = -1
                trade = 1
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                history.append({
                    "time" : i,
                    "w1" : w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "上開倉"
                })
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff}  spread = {spread[i]} 上開倉')


        elif position == -1:  # 之前有開空倉，平空倉

            if i == (spread_len - 3):  # 回測結束，強制平倉
                position = -4
                stock1_payoff, stock2_payoff = up_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} 強制平倉')
                history.append({
                    "time" : i,
                    "w1" : -w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : -w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "尾盤強制平倉"
                })  
                break

            elif (spread[i] - close[i]) < 0:  # 空倉碰到下開倉門檻即平倉
                position = 666  # 平倉
                stock1_payoff, stock2_payoff = up_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} 正常平倉')
                history.append({
                    "time" : i,
                    "w1" : -w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : -w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "正常平倉"
                })  
                break


    trading_profit = sum(stock1_profit) + sum(stock2_profit)



    if cpA > 0 and cpB > 0:
        trade_capital = abs(cpA) + abs(cpB)
    elif cpA > 0 and cpB < 0 :
        trade_capital = abs(cpA) + 0.9 * abs(cpB)
    elif cpA < 0 and cpB > 0 :
        trade_capital = 0.9 * abs(cpA) + abs(cpB)
    elif cpA < 0 and cpB < 0 :
        trade_capital = 0.9 * abs(cpA) + 0.9 * abs(cpB)

    if trade > 0:  # 如果都沒有開倉，則報酬為0
        trade_return = trading_profit / trade_capital


    return trade, trading_profit, trade_capital, trade_return, history



def trade_normal(s1_tick, s2_tick, table, strategy):
    trade_capital = 0
    cpA,cpB = 0,0
    trading_profit = 0.0
    trade = 0
    trade_capital = 0    
    trade_return = 0.0
    history = []


    # 波動太小的配對不開倉
    if volaitlity_small(strategy, table):
        history.append({
            "time" : 0,
            "type" : "配對波動太小，不開倉"
        })
        print(f'{table["S1"]} {table["S2"]}  配對波動太小，不開倉')
        return trade, trading_profit, trade_capital, trade_return, history


    spread = table["w1"] * np.log(s1_tick) + table["w2"] * np.log(s2_tick)
    close, up_open_val, down_open_val = build_open(spread, table, strategy)

    position = 0  # 持倉狀態，1:多倉，0:無倉，-1:空倉，-2：強制平倉 
    stock1_profit = []
    stock2_profit = []
    spread_len = len(spread)
    w1 = 0
    w2 = 0
    for i in range(0, spread_len - 2):
        if position == 0 and i != spread_len - 3:  # 之前無開倉
        
            if spread[i] > up_open_val[i]:  # 碰到下開倉門檻且大於下停損門檻
                w1, w2 = num_weight(table["w1"], table["w2"], s1_tick[i], s2_tick[i], strategy["maxhold"], strategy["capital"])
                stock1_payoff, stock2_payoff = up_open(w1, w2, s1_tick[1], s2_tick[i], strategy["tax_cost"])
                cpA, cpB = stock1_payoff, stock2_payoff
                position = -1
                trade = 1
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                history.append({
                    "time" : i,
                    "w1" : w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "上開倉"
                })                
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} spread = {spread[i]} 上開倉')

            elif spread[i] < down_open_val[i]:  # 碰到下開倉門檻且大於下停損門檻
                w1, w2 = num_weight(table["w1"], table["w2"], s1_tick[i], s2_tick[i], strategy["maxhold"], strategy["capital"])
                stock1_payoff, stock2_payoff = down_open(w1, w2, s1_tick[1], s2_tick[i], strategy["tax_cost"])
                cpA, cpB = stock1_payoff, stock2_payoff
                position = 1
                trade = 1
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                history.append({
                    "time" : i,
                    "w1" : -w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : -w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "下開倉"
                })                
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} spread = {spread[i]} 下開倉')
                


        elif position == -1:  # 之前有開空倉，平空倉

            if i == (spread_len - 3):  # 回測結束，強制平倉
                position = -4
                stock1_payoff, stock2_payoff = up_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                history.append({
                    "time" : i,
                    "w1" : -w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : -w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "尾盤強制平倉"
                })  
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} 強制平空倉')
                break

            elif (spread[i] - close[i]) < 0:  # 空倉碰到下開倉門檻即平倉
                position = 666  # 平倉
                stock1_payoff, stock2_payoff = up_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                history.append({
                    "time" : i,
                    "w1" : -w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : -w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "正常平倉"
                })  
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} 正常平空倉')
                break

        elif position == 1:  # 之前有開多倉，平多倉

            if (i == spread_len - 3):  # 回測結束，強制平倉
                position = -4
                stock1_payoff, stock2_payoff = down_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                history.append({
                    "time" : i,
                    "w1" : w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "尾盤強制平倉"
                })  
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} 強制平多倉')
                break

            elif (spread[i] - close[i]) > 0:
                position = 666  # 平倉
                stock1_payoff, stock2_payoff = down_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                history.append({
                    "time" : i,
                    "w1" : w1,
                    "stock1_payoff" : stock1_payoff,
                    "w2" : w2,
                    "stock2_payoff" : stock2_payoff,
                    "type" : "正常平倉"
                })  
                print(f'{i} {w1} 張 {table["S1"]} {stock1_payoff} , {w2} 張 {table["S2"]} {stock2_payoff} 正常平多倉')
                break



    trading_profit = sum(stock1_profit) + sum(stock2_profit)



    if cpA > 0 and cpB > 0:
        trade_capital = abs(cpA) + abs(cpB)
    elif cpA > 0 and cpB < 0 :
        trade_capital = abs(cpA) + 0.9 * abs(cpB)
    elif cpA < 0 and cpB > 0 :
        trade_capital = 0.9 * abs(cpA) + abs(cpB)
    elif cpA < 0 and cpB < 0 :
        trade_capital = 0.9 * abs(cpA) + 0.9 * abs(cpB)

    if trade > 0:  # 如果都沒有開倉，則報酬為0
        trade_return = trading_profit / trade_capital


    return trade, trading_profit, trade_capital, trade_return, history
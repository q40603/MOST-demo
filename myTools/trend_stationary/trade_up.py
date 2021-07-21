# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 11:49:47 2020

@author: allen
"""

import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from scipy.stats import skew
from cost import tax , slip 
from integer import num_weight
from vecm import rank
from MTSA import fore_chow , spread_chow , order_select
import pandas as pd
import numpy as np


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
    stock1_payoff = w1 * slip(s1_price, w1)
    stock2_payoff = w2 * slip(s2_price, w2)
    stock1_payoff, stock2_payoff = tax(stock1_payoff, stock2_payoff, position, tax_cost)  # 計算交易成本    


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


def pairs(s1_tick, s2_tick, table, strategy):

    trade_capital = 0
    cpA,cpB = 0,0
    trading_profit = 0.0
    trade = 0
    trade_capital = 0    
    trade_return = 0.0


    # 波動太小的配對不開倉
    if volaitlity_small(strategy, table):
        return trade, trading_profit, trade_capital, trade_return


    spread = table["w1"] * np.log(s1_tick) + table["w2"] * np.log(s2_tick)
    close, up_open, down_open = build_open(spread, table, strategy)

    position = 0  # 持倉狀態，1:多倉，0:無倉，-1:空倉，-2：強制平倉 
    stock1_profit = []
    stock2_profit = []
    spread_len = len(spread)
    for i in range(0, spread_len - 2):
        if position == 0 and i != spread_len - 3:  # 之前無開倉
        
            if spread[i] < down_open[i]:  # 碰到下開倉門檻且大於下停損門檻
                w1, w2 = num_weight(table["w1"], table["w2"], s1_tick[i], s2_tick[i], strategy["maxhold"], strategy["captial"])
                stock1_payoff, stock2_payoff = down_open(
                    time = i,
                    s1_tick = s1_tick
                    s2_tick = s2_tick, 
                    table = table,
                    strategy = strategy                    
                )
                cpA, cpB = stock1_payoff, stock2_payoff
                position = 1
                trade = 1
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)


        elif position == -1:  # 之前有開空倉，平空倉

            if i == (spread_len - 3):  # 回測結束，強制平倉
                position = -4
                stock1_payoff, stock2_payoff = up_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                break

            elif (spread[i] - close[i]) < 0:  # 空倉碰到下開倉門檻即平倉
                position = 666  # 平倉
                stock1_payoff, stock2_payoff = up_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                break


        elif position == 1:  # 之前有開多倉，平多倉

            if (i == spread_len - 3):  # 回測結束，強制平倉
                position = -4
                stock1_payoff, stock2_payoff = down_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
                break

            elif (spread[i] - close[i]) > 0:
                position = 666  # 平倉
                stock1_payoff, stock2_payoff = down_close(w1, w2,  s1_tick[i], s2_tick[i], strategy["tax_cost"], position)
                stock1_profit.append(stock1_payoff)
                stock2_profit.append(stock2_payoff)
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


    return trade, trading_profit, trade_capital
            
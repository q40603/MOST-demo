'''
json : pack result to json,
flask : flask server and related modeul,
_pickle : load 25 actions from pickle
myTools : pairs trade related function
'''
import json, sys
from flask import Flask, render_template, jsonify, request
# import _pickle as pickle
from myTools.pairstrading.pairs_trading import get_all_pairs, get_pairs_spread, get_past_five
    # get_all_pairs, get_pairs_spread, \
    # trade_pair, get_stock_news, \
    # get_s_name, structure_break_pred



app = Flask(__name__)

@app.route("/")
def home():
    '''
    return static html file : first page
    '''
    return render_template("pairs_trading.html")


@app.route("/debug")
def debug():
    '''
    return static html file : debug page for developing
    '''
    return render_template("debug.html")


@app.route("/stock/find_past_pairs", methods=['GET'])
def find_past_pairs():
    '''
    return pairs found in given date
    '''
    trade_date = request.values.get('trade_date')
    trade_date = trade_date.replace("-","")
    data = get_all_pairs(trade_date)
    return jsonify(data)

@app.route("/stock/get_pairs_price", methods=['GET','POST'])
def get_pairs_price():
    '''
    return {
        s1's and s2's stock price spread,
        s1's and s2's stock info : stock name,
        s1's and s2's news,
        conintegration spread,
        action chosed from ResNet (Kuo),
        Structure break prediction from NCTU CS
    }
    '''
    pair_info = request.get_json()
    data = get_pairs_spread(pair_info)
    return jsonify(data)


@app.route("/stock/get_past_five", methods=['GET'])
def get_past_profit():
    '''
    return {
        s1's and s2's stock price spread,
        s1's and s2's stock info : stock name,
        s1's and s2's news,
        conintegration spread,
        action chosed from ResNet (Kuo),
        Structure break prediction from NCTU CS
    }
    '''
    data = get_past_five()
    return jsonify(data)
# @app.route("/stock/trade_backtest", methods=['GET'])
# def trade_backtest():
#     '''
#     return backtest result
#     '''
#     s_1 = request.values.get('s1')
#     s_2 = request.values.get('s2')
#     choose_date = request.values.get('trade_date')
#     data = trade_pair(choose_date, s_1, s_2)
#     data = json.dumps(data,default= str)
#     return jsonify(data)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8888)

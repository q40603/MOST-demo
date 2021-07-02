'''
json : pack result to json,
flask : flask server and related modeul,
_pickle : load 25 actions from pickle
myTools : pairs trade related function
'''
import json, sys
from flask import Flask, render_template, jsonify, request
import _pickle as pickle
from myTools.pairstrading.pairs_trading import get_all_pairs, get_pairs_spread
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
    # s1 = request.values.get('s1')
    # s2 = request.values.get('s2')
    # trade_date = request.values.get('trade_date')
    # w1 = request.values.get('w1')
    # w2 = request.values.get('w2')
    # model_type = request.values.get('model_type')
    # action_id = request.values.get('action')

    # with open("./myTools/actions.pkl", "rb") as action_pkl:
    #     actions = pickle.load(action_pkl)

    pair_info = request.get_json()
    data = get_pairs_spread(pair_info)
    #data = get_pairs_spread(trade_date, s_1, s_2, float(w_1), float(w_2), model_type)
    # s_1 = s_1.replace("s_","")
    # s_2 = s_2.replace("s_","")
    # data["sb_pred"] = structure_break_pred(trade_date, s_1, s_2)
    # tmp = get_s_name(s_1,s_2)
    # data["s1_info"] = tmp[0]
    # data["s2_info"] = tmp[1]
    # data["s1_news"] = get_stock_news(trade_date.rstrip(),s_1)
    # data["s2_news"] = get_stock_news(trade_date.rstrip(),s_2)
    # data["thresold"] = actions[int(action_id)]
    # data = json.dumps(data, default= str)
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
    app.run(debug=True, host=sys.argv[1], port=sys.argv[2])

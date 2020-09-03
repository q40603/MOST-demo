from flask import Flask, render_template, jsonify, request
from myTools.pairstrading.pairs_trading import *
import json  

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("pairs_trading.html")


@app.route("/stock/find_past_pairs",methods=['GET'])
def find_past_pairs():
    trade_date = request.values.get('trade_date')
    data = get_all_pairs(trade_date)
    return jsonify(data)

@app.route("/stock/get_pairs_price",methods=['GET'])
def get_pairs_price():
    #print(request.values)
    s1 = request.values.get('s1')
    s2 = request.values.get('s2')
    trade_date = request.values.get('trade_date')
    w1 = request.values.get('w1')
    w2 = request.values.get('w2')
    model_type = request.values.get('model_type')
    action_id = request.values.get('action')
    actions = [[0.5000000000002669, 2.500000000000112], [0.7288428324698772, 4.0090056748083995], [1.1218344155846804, 3.0000000000002496], [1.2162849872773496, 7.4631043256997405], [1.4751902346226717, 3.9999999999997113], [1.749999999999973, 3.4999999999998117], [2.086678832116794, 6.2883211678832325], [2.193017888055368, 4.018753606462444], [2.2499999999999822, 7.500000000000021], [2.6328389830508536, 8.9762711864407], [2.980046948356806, 13.515845070422579], [3.2499999999999982, 5.500000000000034], [3.453852327447829, 11.505617977528125], [3.693027210884357, 6.0739795918367605], [4.000000000000004, 12.500000000000034], [4.151949541284411, 10.021788990825703], [4.752819548872187, 15.016917293233117], [4.8633603238866225, 7.977058029689605], [5.7367647058823605, 13.470588235294136], [6.071428571428564, 16.47435897435901], [6.408839779005503, 10.95488029465933], [7.837962962962951, 12.745370370370392], [8.772727272727282, 18.23295454545456], [9.242088607594926, 14.901898734177237], [100,200]]
    data = get_pairs_spread(trade_date, s1, s2, float(w1), float(w2), model_type)
    tmp = get_s_name(s1.replace("s_",""),s2.replace("s_",""))
    data["s1_info"] = tmp[0]
    data["s2_info"] = tmp[1]
    # data["s1_news"] = get_stock_news(trade_date.rstrip(),s1.replace("s_",""))
    # data["s2_news"] = get_stock_news(trade_date.rstrip(),s2.replace("s_",""))
    data["thresold"] = actions[int(action_id)]
    data = json.dumps(data,default= str)
    return jsonify(data)

@app.route("/stock/trade_backtest",methods=['GET'])  
def trade_backtest():
    s1 = request.values.get('s1')
    s2 = request.values.get('s2')
    _open = request.values.get('open')
    _stop = request.values.get('stop')
    choose_date = request.values.get('trade_date')
    print("trade_backtest", choose_date, s1,s2)
    capital = 3000           # 每組配對資金300萬
    maxi = 5                 # 股票最大持有張數
    open_time = float(_open)                 # 開倉門檻倍數
    stop_loss_time = float(_stop)                 # 停損門檻倍數
    tax_cost = 0
    pair_list = [[s1, s2]]
    data = trade_certain_pairs(choose_date, capital, maxi, open_time, stop_loss_time, tax_cost, pair_list)
    data = json.dumps(data,default= str)
    return jsonify(data)

    
    
if __name__ == "__main__":
    app.run(debug=True)
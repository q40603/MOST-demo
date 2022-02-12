import pymysql
import json
import sys
from pymongo import MongoClient


db_host = '127.0.0.1'
db_name = 'PairsTrade'
db_user = 'kctsai'
db_passwd = 'financeai'

fin_db = pymysql.connect(
	host = db_host,
	user = db_user,
	password = db_passwd,
	db = db_name,
	autocommit=True
)
fin_cursor = fin_db.cursor(pymysql.cursors.DictCursor)

client = MongoClient("mongodb://127.0.0.1:27017/")
table_db = client["Pairs_Trade_Result"]



def get_all_pairs(choose_date):
	fin_db.ping(reconnect = True)
	query = "select * from Pairs where time = '" + choose_date + "' order by _return desc;"
	fin_cursor.execute(query)
	data = fin_cursor.fetchall()
	return data


def get_all_trade_day():
    fin_db.ping(reconnect = True)
    query = "select distinct(time) from Pairs;"
    fin_cursor.execute(query)
    data = fin_cursor.fetchall()
    return data    

if __name__ == '__main__':

    data = table_db.table.find({"time" : sys.argv[1]})
    print(data)
    # _date = get_all_trade_day()
    # for d in _date:
    #     data = get_all_pairs(d["time"])
    #     #print(data)
    #     l = len(data)
    #     text = '<tbody id="pair">'
                            
    #     for i in range(l):
    #         text += "<tr class='styled accordion'> " + "<td class=' center aligned ' >" + data[i]["S1"] + "</td>" + "<td class=' center aligned ' >" + data[i]["S2"] + "</td>"
        
    #         if(data[i]["w1"]<0):
    #             text += "<td class=' center aligned ' style='background:#d7fac8;'>"  + str("{:.4f}".format(data[i]["w1"])) + "</td>"
            
    #         else:
    #             text += "<td class=' center aligned ' style='background:#ffbfbf;'>"  + str("{:.4f}".format(data[i]["w1"])) + "</td>"						

    #         if(data[i]["w2"]<0):
    #             text += "<td class=' center aligned ' style='background:#d7fac8;'>"  + str("{:.4f}".format(data[i]["w2"])) + "</td>"
            
    #         else:
    #             text += "<td class=' center aligned ' style='background:#ffbfbf;'>"  + str("{:.4f}".format(data[i]["w2"])) + "</td>"

    #         text += "<td class=' center aligned '>"  + str(data[i]["model"]) + "</td>"

    #         # if (data[i]["_return"]<0):
    #         #     text += "<td class=' center aligned ' style='background:#acff80;'>"

    #         # elif (data[i]["_return"]>0):
    #         #     text += "<td class=' center aligned ' style='background:#ff8080;'>"

    #         # else:
    #         text += "<td class=' center aligned '>"


    #         text += str("{:.4f}".format(data[i]["_return"])) + "%</td>"
            
    #         text += "<td class=' center aligned' ><button class='center aligned ui button trade' "
    #         text +=	"pairId = " + str(i)

    #         text += "> trade </button> " + "</td>" + "</tr>"

    #     text += '</tbody>'
    #     table_db["table"].insert({
    #         "time" : d["time"],
    #         "html" : text
    #     })
        
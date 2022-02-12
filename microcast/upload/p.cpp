
#include <iostream>
#include <ctime>
#include <fstream>
#include <vector>
#include <sstream>
#include <istream>
#include <iomanip>
using namespace std;

int main(int argc, char **argv){
    
    string date = argv[1];
    string _file = "../stock_data/" + date +".csv";
    ifstream file(_file);
    date = date.substr(0,4) + "-" + date.substr(4,2) + "-" + date.substr(6,2);
    vector<string> tmp;
    bool start = true;//false;

    cout<<"#datatype measurement,long,double,long,dateTime:number"<<endl;
    cout<<"m,acc_vol,price,vol,time"<<endl;
    if (file.is_open()) {
        string line, val, tt, _rest;
        while (getline(file, line)) {
            stringstream ss(line);
            while(getline(ss, val, ',')){
                tmp.push_back(val);
            }
            //if(tmp[1].substr(0,4)=="0900")
                //start = true;
            
            if(start && tmp[4]!="0"){
                tt = date + " " + tmp[1].substr(0,8);  
                _rest = tmp[1].substr(6);
                cout<<tt<<endl;
                tm t{};
                istringstream st(tt);
                st >> std::get_time(&t, "%Y-%m-%d %H:%M:%S");
                if (st.fail()) {
                    throw std::runtime_error{"failed to parse time string"};
                }   
                std::time_t time_stamp = mktime(&t);
                
                cout<<tmp[0]<<","<<tmp[2]<<","<<tmp[3]<<","<<tmp[4]<< "," <<time_stamp<<_rest<<"000"<<endl;
            }
            tmp.clear();    
        }
    }
    file.close();

    return 0;

}

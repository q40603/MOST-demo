# file_pointer = []

# for i in range(15):
#     file_pointer.append(open("../stock_data/20211221_past{}.csv".format(i), "r"))


# for date in range(5):
#     _file = open("./{}.csv".format(date), "a")
#     print("----------------- {} --------------------".format(date))
#     prev = ""
#     for fi in range(15):
#         print("==     {}".format(fi))
#         while(1):
#             pos = file_pointer[fi].tell()
#             a = file_pointer[fi].readline().rstrip()
#             if not a:
#                 break
#             _time = a.split(",")[6]
#             if((not _time.startswith("1330")) and (prev.startswith("1330"))):
#                 break
#             prev = _time
#             print(a, file=_file)
#         prev = ""



import sys


with open(sys.argv[1], "r") as f:
    while(1):
        data = f.readline().rstrip()
        if(not data):
            break
        data = data.split(",")
        _time = data[1]

        data[1] = data[1].replace(":", "")
        data[1] = data[1].replace(".", "")

        print(",".join(data))

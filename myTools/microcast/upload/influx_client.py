from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate a Token from the "Tokens Tab" in the UI
token = "OmMqjkZ7wPS-7Qy-HegGcHXDfdMp7-lWCMAfNlmyT-_xxgQ6R0D2DI1f5-MmHgk7xvs94rKD7PI4dN-DE5rwJQ=="
org = "PairTrade"
bucket = "stock"

client = InfluxDBClient(url="http://paris-trading.lab.nycu.edu.tw:8086", token=token)
start = datetime.strptime("20210701 09:00", "%Y%m%d %H:%M").strftime('%Y-%m-%dT%H:%M:%SZ')
end = datetime.strptime("20210701 13:31", "%Y%m%d %H:%M").strftime('%Y-%m-%dT%H:%M:%SZ')
query = f'\
import "interpolate"\
from(bucket: "stock")\
  |> range(start: {start}, stop: {end})\
  |> filter(fn: (r) => r["_measurement"] == "2347")\
  |> filter(fn: (r) => r["_field"] == "price" or r["_field"] == "vol")\
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")\
  |> window(every:1m)\
  |> reduce(fn: (r, accumulator) => ({{\
      count: accumulator.count + float(v:r.vol),\
      total: accumulator.total + (float(v: r.vol) * r.price),\
  }}),\
    identity: {{count: 0.0, total: 0.0}}\
  )\
  |> map(fn: (r) => ({{ r with _value: float(v: r.total) / r.count }}))\
  |> keep(columns: ["_start", "_value"])\
  |> duplicate(column:"_start", as:"_time")\
  |> window(every:inf)\
  |> interpolate.linear(every: 1m)\
'
print(query)
result = client.query_api().query(org=org, query=query)
results = []
for table in result:
    for record in table.records:
        results.append((record.get_time(),record.get_value()))

print(results)
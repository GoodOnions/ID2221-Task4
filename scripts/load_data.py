from time import sleep
from json import dumps
from kafka import KafkaProducer
import json

f = open('scripts/DataSet/spotify_5.json')
data_message = json.load(f)

producer = KafkaProducer(bootstrap_servers=['localhost:9093'],
                         value_serializer=lambda x: 
                         dumps(x).encode('utf-8'))

print(data_message)
for e in range(len(data_message)):
    producer.send('onions', value=data_message[e])
    print(e)
    sleep(1)
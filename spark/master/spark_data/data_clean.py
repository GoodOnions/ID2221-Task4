import os


os.system("pip install pandas requests PyArrow")

from time import sleep
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, date_format
from pyspark.sql import SparkSession
import json
import pandas as pd
from pyspark.sql.functions import from_json, col, get_json_object, udf, pandas_udf
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, ArrayType, DoubleType, FloatType
import requests



# Define the schema, replace with what you expect
response_schema = StructType([
    StructField("user_id", IntegerType(),True),
    StructField("items", StringType(),True),
    StructField("created_at", TimestampType(),True),
    StructField("updated_at", TimestampType(),True)
])

item_schema = StructType([
    StructField("track", StringType(),True),
    StructField("played_at", StringType(),True),
    StructField("context", StringType(),True)
])

def requestAPI(track_ids):
    AUTH_URL = 'https://accounts.spotify.com/api/token'

    # POST
    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': '72c2183e4c034c15a0305818667390b7',
        'client_secret': '7dc6919a592f49519435f7dc3f8fc1b5',
    })

    # convert the response to JSON
    auth_response_data = auth_response.json()

    # save the access token
    access_token= auth_response_data['access_token']

    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    BASE_URL = 'https://api.spotify.com/v1/'

    track_ids_str = ','.join(track_ids)
    # actual GET request with proper header
    r = requests.get(BASE_URL + 'audio-features?ids=' + track_ids_str, headers=headers)

    while r.status_code!=200:
        print('Status code ->',r.status_code)
        sleep(20)
        r = requests.get(BASE_URL + 'audio-features?ids=' + track_ids_str, headers=headers)

    r = r.json()
    result = []
    for track in r['audio_features']:
        
        result.append((track['energy'], track['danceability'], track['duration_ms'], track['instrumentalness'],\
                       track['loudness'], track['tempo'], track['valence']))
    return pd.DataFrame(result)



packages = [
    'org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2',
    'org.apache.spark:spark-sql-connector-cassandra_2.12:3.1.2'
]

spark = SparkSession.builder\
   .master("spark://10.0.0.2:7077")\
   .appName("Demo")\
   .config("spark.jars.packages", ",".join(packages))\
   .config("spark.cassandra.connection.host", "10.0.0.6")\
   .config("spark.cassandra.connection.port", "9042")\
   .config("spark.cassandra.auth.username","cassandra")\
   .config("spark.cassandra.auth.password","cassandra")\
   .getOrCreate() 

spark.sparkContext.setLogLevel("WARN")

df = spark\
        .readStream\
        .format("kafka")\
        .option("kafka.bootstrap.servers", "10.0.0.5:9094")\
        .option("subscribe", "onions")\
        .option("startingOffsets", "earliest")\
        .load()



json_df = df.select(explode(from_json(col("value").cast("string"), ArrayType(response_schema))).alias('json')).select('json.*')

json_df = json_df.select('*',explode(from_json(col("items").cast("string"), ArrayType(item_schema))).alias('item')).select('*','item.*')

json_df = json_df.select('user_id','played_at',\
                         get_json_object(col("track").cast("string"), "$.id").alias("track_id").cast('string'),\
                         get_json_object(col("track").cast("string"), "$.name").alias("track_name").cast('string'),\
                         get_json_object(col("track").cast("string"), "$.popularity").alias("track_popularity").cast('string'),\
                         get_json_object(col("context").cast("string"), "$.type").alias("context_type").cast('string'),\
                         get_json_object(col("context").cast("string"), "$.href").alias("context_href").cast('string'),)

json_df = json_df.withColumn("day_of_week", date_format(col("played_at"), "H"))
json_df = json_df.withColumn("hour_of_day", date_format(col("played_at"), "H"))



get_track_info_udf = pandas_udf(requestAPI, returnType = StructType([
                                                            StructField("energy", DoubleType(), True),
                                                            StructField("danceability", DoubleType(), True),
                                                            StructField("instrumentalness", DoubleType(), True),
                                                            StructField("loudness", DoubleType(), True),
                                                            StructField("tempo", DoubleType(), True),
                                                            StructField("valence", DoubleType(), True),
                                                            StructField("duration_ms", DoubleType(), True)
                                                            ]))


json_df = json_df.withColumn("features", get_track_info_udf(json_df['track_id']))

json_df = json_df.select('*','features.*').drop('features')


query = json_df.selectExpr("CAST(user_id AS STRING)",\
                           "CAST(played_at AS STRING)",\
                           "CAST(track_id AS STRING)",\
                           "CAST(track_name AS STRING)",\
                           "CAST(track_popularity AS DOUBLE)",\
                           "CAST(context_type AS STRING)",\
                           "CAST(energy AS STRING)",\
                           "CAST(danceability AS STRING)",\
                           "CAST(instrumentalness AS STRING)",\
                           "CAST(loudness AS STRING)",\
                           "CAST(tempo AS STRING)",\
                           "CAST(valence AS STRING)",\
                           "CAST(duration_ms AS STRING)",\
                           "CAST(day_of_week AS INT)",\
                           "CAST(hour_of_day AS INT)")\
    .writeStream \
    .format("console") \
    .start()
# query.awaitTermination()


def writeToCassandra(writeDF, _):
  writeDF.write \
    .format("org.apache.spark.sql.cassandra")\
    .mode('append')\
    .options(table="music_play_history", keyspace="goodonions")\
    .save()

json_df.writeStream \
    .foreachBatch(writeToCassandra) \
    .outputMode("update") \
    .start()\
    .awaitTermination()


json_df.show()
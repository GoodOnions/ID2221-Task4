from time import sleep
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, date_format
from pyspark.sql import SparkSession
import pandas as pd
from pyspark.sql.functions import from_json, col, get_json_object, udf, pandas_udf
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, ArrayType, DoubleType
import requests
from spotifyAPI import getTracksFeaturesAPI


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
                         get_json_object(col("track").cast("string"), "$.popularity").alias("track_popularity").cast('double'),\
                         get_json_object(col("context").cast("string"), "$.type").alias("context_type").cast('string'),\
                         get_json_object(col("context").cast("string"), "$.href").alias("context_href").cast('string'),)

json_df = json_df.withColumn("day_of_week", date_format(col("played_at"), "H"))
json_df = json_df.withColumn("hour_of_day", date_format(col("played_at"), "H"))



get_track_info_udf = pandas_udf(getTracksFeaturesAPI, returnType = StructType([
                                                            StructField("energy", DoubleType(), True),
                                                            StructField("danceability", DoubleType(), True),
                                                            StructField("duration_ms", DoubleType(), True),
                                                            StructField("instrumentalness", DoubleType(), True),
                                                            StructField("loudness", DoubleType(), True),
                                                            StructField("tempo", DoubleType(), True),
                                                            StructField("valence", DoubleType(), True)
                                                            ]))


json_df = json_df.withColumn("features", get_track_info_udf(json_df['track_id']))

json_df = json_df.select('*','features.*').drop('features')


query = json_df.selectExpr("CAST(user_id AS STRING)",\
                           "CAST(played_at AS STRING)",\
                           "CAST(track_id AS STRING)",\
                           "CAST(track_name AS STRING)",\
                           "CAST(track_popularity AS DOUBLE)",\
                           "CAST(energy AS STRING)",\
                           "CAST(danceability AS STRING)",\
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
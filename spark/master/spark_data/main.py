from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, ArrayType, DoubleType, BooleanType
from pyspark.sql.functions import from_json, col, get_json_object, pandas_udf
from pyspark.sql.functions import explode, date_format
from pyspark.sql import SparkSession
import os 

import data_collector as dc

CASSANDRA_IP = 'cassandra'
cassandra_user = os.getenv('CASSANDRA_USER')
cassandra_password = os.getenv('CASSANDRA_PASSWORD')
KAFKA_BOOTSTRAP = "10.0.0.5:9094" 


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

features_schema =StructType([
                    StructField("energy", DoubleType(), True),
                    StructField("danceability", DoubleType(), True),
                    StructField("duration_ms", DoubleType(), True),
                    StructField("instrumentalness", DoubleType(), True),
                    StructField("loudness", DoubleType(), True),
                    StructField("tempo", DoubleType(), True),
                    StructField("valence", DoubleType(), True)
                ])

boolean_schema=StructType([
                    StructField("isInCache", BooleanType(), True)
                ])

packages = [
    'org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2',
    'org.apache.spark:spark-sql-connector-cassandra_2.12:3.1.2'
]

spark = SparkSession.builder\
   .master("spark://10.0.0.2:7077")\
   .appName("Demo")\
   .config("spark.jars.packages", ",".join(packages))\
   .config("spark.cassandra.connection.host", CASSANDRA_IP)\
   .config("spark.cassandra.connection.port", "9042")\
   .config("spark.cassandra.auth.username",cassandra_user)\
   .config("spark.cassandra.auth.password",cassandra_password)\
   .getOrCreate() 

spark.sparkContext.setLogLevel("WARN")

df = spark\
        .readStream\
        .format("kafka")\
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)\
        .option("subscribe", "onions")\
        .load()



###### Parsing kafka input ######
json_df = df.select(explode(from_json(col("value").cast("string"), ArrayType(response_schema))).alias('json')).select('json.*')
json_df = json_df.select('*',explode(from_json(col("items").cast("string"), ArrayType(item_schema))).alias('item')).select('*','item.*')

json_df = json_df.select('user_id','played_at',\
                         get_json_object(col("track").cast("string"), "$.id").alias("track_id").cast('string'),\
                         get_json_object(col("track").cast("string"), "$.name").alias("track_name").cast('string'),\
                         get_json_object(col("track").cast("string"), "$.popularity").alias("track_popularity").cast('double'),\
                         get_json_object(col("context").cast("string"), "$.type").alias("context_type").cast('string'),\
                         get_json_object(col("context").cast("string"), "$.href").alias("context_href").cast('string'),)

json_df = json_df.withColumn("day_of_week", date_format(col("played_at"), "F"))\
                 .withColumn("hour_of_day", date_format(col("played_at"), "H"))



###### Definition of udf functions ######
get_track_features_cache  = pandas_udf(dc.getTracksFeaturesCache, returnType = features_schema)
get_track_in_cache  = pandas_udf(dc.isInCacheList, returnType = boolean_schema)
get_track_features_api = pandas_udf(dc.getTracksFeaturesAPI, returnType = features_schema)



####### Map items in cache #######
allIDs = json_df.select('track_id').withColumn('isInCache',get_track_in_cache(json_df['track_id'])).select('track_id', 'isInCache.*')



####### Get cached items #########
ids = allIDs.filter('isInCache == True').select('track_id')
inCacheTracksFeatures = ids.withColumn("features", get_track_features_cache(ids['track_id']))

                                  

########## Call to API ###########
ids = allIDs.filter('isInCache == False').select('track_id')
responseTracksFeatures = ids.withColumn("features", get_track_features_api(ids['track_id']))



#Join item streams
all_features = inCacheTracksFeatures.union(responseTracksFeatures).select('track_id','features.*')
json_df = json_df.join(all_features,'track_id')

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



def writeToCassandra(writeDF, _):
  writeDF.write \
    .format("org.apache.spark.sql.cassandra")\
    .mode('append')\
    .options(table="music_play_history", keyspace="goodonions")\
    .save()

json_df.writeStream \
    .foreachBatch(writeToCassandra)\
    .outputMode("append")\
    .start()\
    .awaitTermination()


json_df.show()
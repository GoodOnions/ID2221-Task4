from pyspark.sql import SparkSession
from pyspark.sql.functions import explode
from pyspark.sql import SparkSession
import json
from pyspark.sql.functions import from_json, col, get_json_object
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, ArrayType

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
                         get_json_object(col("track").cast("string"), "$.id").alias("track_id"),\
                         get_json_object(col("track").cast("string"), "$.name").alias("track_name"),\
                         get_json_object(col("context").cast("string"), "$.type").alias("context_type"),\
                         get_json_object(col("context").cast("string"), "$.href").alias("context_href"),)


query = json_df.selectExpr("CAST(user_id AS STRING)",\
                           "CAST(played_at AS STRING)",\
                           "CAST(track_id AS STRING)",\
                           "CAST(track_name AS STRING)",\
                           "CAST(context_type AS STRING)",\
                           "CAST(context_href AS STRING)")\
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
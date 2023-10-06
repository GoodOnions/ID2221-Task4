from pyspark.sql import SparkSession

packages = [
    'org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2'
]

spark = SparkSession.builder\
   .master("spark://10.0.0.2:7077")\
   .appName("Demo")\
   .config("spark.jars.packages", ",".join(packages))\
   .getOrCreate() 

spark.sparkContext.setLogLevel("WARN")

df = spark\
        .readStream\
        .format("kafka")\
        .option("kafka.bootstrap.servers", "10.0.0.5:9094")\
        .option("subscribe", "test")\
        .option("startingOffsets", "earliest")\
        .load()

query = df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)") \
    .writeStream \
    .format("console") \
    .start()

query.awaitTermination()

# df.show()

# df.selectExpr("CAST(id AS STRING) AS key", "to_json(struct(*)) AS value")\
#    .writeStream\
#    .format("kafka")\
#    .outputMode("append")\
#    .option("kafka.bootstrap.servers", "192.168.1.100:9092")\
#    .option("topic", "test_2")\
#    .start()\
#    .awaitTermination()
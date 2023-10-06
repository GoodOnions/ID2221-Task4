from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("Demo")
         .getOrCreate())

# df = spark.readStream\
#         .format("kafka")\
#         .option("kafka.bootstrap.servers", "192.168.1.100:9093")\
#         .option("subscribe", "test")\
#         .option("startingOffsets", "earliest")\
#         .load()

# df.selectExpr("CAST(id AS STRING) AS key", "to_json(struct(*)) AS value")\
#    .writeStream\
#    .format("kafka")\
#    .outputMode("append")\
#    .option("kafka.bootstrap.servers", "192.168.1.100:9092")\
#    .option("topic", "test_2")\
#    .start()\
#    .awaitTermination()
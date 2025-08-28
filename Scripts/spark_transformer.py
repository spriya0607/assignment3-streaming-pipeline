from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, trim, regexp_replace, to_date, when
from pyspark.sql.types import *
from datetime import datetime
import uuid

spark = SparkSession.builder \
    .appName("Humidity-Transform") \
    .getOrCreate()

# S3 bucket paths
input_path = "s3://my-streaming-raw-bronze/raw/"
output_path = "s3://my-streaming-processed-gold/iot_transformed/"
checkpoint_path = "s3://my-streaming-processed-gold/checkpoints/"

# Schema for humidity data
schema = StructType([
    StructField("event_time", StringType(), True),
    StructField("device_id", StringType(), True),
    StructField("temperature_c", StringType(), True),
    StructField("humidity_pct", StringType(), True)
])

# Read raw CSV from S3
df_raw = spark.readStream \
    .schema(schema) \
    .option("header", "true") \
    .csv(input_path)

# Basic cleaning
df_clean = df_raw \
    .withColumn("temperature_c", col("temperature_c").cast("double")) \
    .withColumn("humidity_pct", col("humidity_pct").cast("double")) \
    .withColumn("event_date", to_date("event_time")) \
    .dropna()

# Repartition for better parallelism
df_final = df_clean.repartition("event_date")

# Write function
def write_to_s3(df, epoch_id):
    batch_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())[:8]
    dynamic_path = f"{output_path}{batch_id}/"
    df.write.mode("append").partitionBy("event_date").parquet(dynamic_path)

# Start query
query = df_final.writeStream \
    .foreachBatch(write_to_s3) \
    .option("checkpointLocation", checkpoint_path) \
    .trigger(processingTime="2 minutes") \
    .start()

query.awaitTermination()
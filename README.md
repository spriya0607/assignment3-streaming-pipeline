# 📡 IoT Sensor Data Streaming Pipeline (AWS + Spark + Terraform)

This project implements a real-time data streaming pipeline for IoT sensor data using AWS services. The solution simulates **humidity sensor events** and processes them using a Spark streaming job on an EMR cluster. Processed data is stored in S3, and the system is monitored with CloudWatch alarms.

---

## 🚀 Overview

- **Data Simulation**: Python script generates humidity sensor data and uploads it to S3 every few minutes.  
- **Data Processing**: PySpark job runs on EMR, reads data from S3, cleans/normalizes it, and writes processed outputs back to S3.  
- **Storage**:  
  - Raw data → S3 “bronze” bucket  
  - Transformed data → S3 “gold” bucket (Parquet format)  
- **Monitoring**: CloudWatch alarms watch EMR job status and cluster health.  
- **Infrastructure as Code**: All AWS resources are provisioned with Terraform (no console steps).  

---

## 🔧 Components

### 📁 Data Ingestion
- `input_data_streaming.py` → generates humidity events.  
- Data uploaded to `s3://iot-stream-raw-bronze/raw/`.  

### 💡 Spark Transformation
- `spark_transformer.py` runs on EMR.  
- Cleans and validates data (filters bad records, normalizes fields).  
- Writes Parquet files to `s3://iot-stream-processed-gold/iot_transformed/`.  
- Uses checkpointing to avoid duplicates.  

### 🧱 Terraform Modules
- **s3.tf** → Raw & Processed buckets  
- **emr.tf** → EMR cluster + Spark step  
- **iam_emr.tf** → IAM roles for EMR  
- **cloudwatch.tf** → CloudWatch alarms for job/cluster health  
- **variables.tf** → Parameterized values  
- **outputs.tf** → EMR cluster ID  

---

## 📂 Project Structure
├── Scripts/
│   ├── input_data_streaming.py     # Simulates humidity data → S3
│   └── spark_transformer.py        # Spark job to clean & process data
├── terraform/
│   ├── s3.tf                       # S3 buckets
│   ├── emr.tf                      # EMR cluster setup
│   ├── iam_emr.tf                  # IAM roles
│   ├── cloudwatch.tf               # CloudWatch alarms
│   ├── variables.tf                # Variables
│   ├── outputs.tf                  # Outputs
│   ├── provider.tf                 # AWS provider config
│   └── main.tf                     # Terraform entry
├── README.md
---

## 🚀 How to Run

### 1. Run Data Generator
```bash
cd Scripts
python input_data_streaming.py
#deploy
cd terraform
terraform init
terraform apply -auto-approve
#Check Outputs
	•	Raw data in → s3://iot-stream-raw-bronze/raw/
	•	Processed data in → s3://iot-stream-processed-gold/iot_transformed/
	•	EMR → Steps tab shows Spark job success/failure
	•	CloudWatch → check alarms & metrics
    #acceptance
    Requirement
Status
Use AWS SDK/Terraform for setup
✅ Done
Python script simulates humidity data
✅ Done
Spark job processes streaming data
✅ Done
Transformed data stored in S3
✅ Done
CloudWatch alarms configured
✅ Done
All Infra via Terraform only
✅ Done
Code hosted on GitHub
✅ Done
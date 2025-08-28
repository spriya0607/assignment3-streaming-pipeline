import boto3
import json
import time
import io
import random
import uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# =======================
# CONFIG
# =======================
BUCKET_NAME = "my-streaming-raw-bronze"   # your raw bucket
OBJECT_KEY_PREFIX = "raw/iot_stream_"     # files go under raw/
PART_SIZE = 100 * 1024 * 1024             # 100 MB per part
MAX_THREADS = 4
TARGET_BATCH_GB = 5                       # target ~5 GB
MAX_RETRIES = 3

# AWS S3 client
s3 = boto3.client("s3")

# =======================
# DATA GENERATION
# =======================
def generate_event():
    """Simulate a humidity/temperature IoT reading"""
    now = datetime.utcnow()
    return {
        "event_id": str(uuid.uuid4()),
        "event_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "device_id": f"d-{random.randint(1000, 9999)}",
        "temperature_c": round(random.uniform(18.0, 35.0), 2),
        "humidity_pct": round(random.uniform(30.0, 80.0), 2),
    }

def upload_part(part_number, upload_id, data_bytes, key):
    """Upload a single S3 part"""
    for attempt in range(MAX_RETRIES):
        try:
            resp = s3.upload_part(
                Bucket=BUCKET_NAME,
                Key=key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=data_bytes,
            )
            return {"ETag": resp["ETag"], "PartNumber": part_number}
        except Exception as e:
            print(f"Retry {attempt+1} for part {part_number}: {e}")
            time.sleep(2 ** attempt)
    raise Exception(f"Failed to upload part {part_number}")

def run_batch():
    """Generate ~5 GB JSONL and upload via multipart upload"""
    key = f"{OBJECT_KEY_PREFIX}{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.jsonl"
    print(f"🚀 Starting upload: s3://{BUCKET_NAME}/{key}")

    mpu = s3.create_multipart_upload(Bucket=BUCKET_NAME, Key=key)
    upload_id = mpu["UploadId"]

    buffer = io.BytesIO()
    parts, futures = [], []
    total_uploaded = 0
    part_number = 1

    try:
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
            while total_uploaded < TARGET_BATCH_GB * 1024**3:
                event = generate_event()
                buffer.write((json.dumps(event) + "\n").encode("utf-8"))

                if buffer.tell() >= PART_SIZE:
                    data = buffer.getvalue()
                    buffer = io.BytesIO()
                    futures.append(ex.submit(upload_part, part_number, upload_id, data, key))
                    total_uploaded += len(data)
                    print(f"📦 Enqueued part {part_number}, total {total_uploaded/1024/1024/1024:.2f} GB")
                    part_number += 1

            if buffer.tell() > 0:
                data = buffer.getvalue()
                futures.append(ex.submit(upload_part, part_number, upload_id, data, key))
                total_uploaded += len(data)

            for f in as_completed(futures):
                parts.append(f.result())

        parts.sort(key=lambda x: x["PartNumber"])
        s3.complete_multipart_upload(
            Bucket=BUCKET_NAME,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        print(f"✅ Upload complete: {total_uploaded/1024/1024/1024:.2f} GB uploaded to {key}")

    except Exception as e:
        s3.abort_multipart_upload(Bucket=BUCKET_NAME, Key=key, UploadId=upload_id)
        print(f"❌ Upload failed: {e}")

if __name__ == "__main__":
    run_batch()
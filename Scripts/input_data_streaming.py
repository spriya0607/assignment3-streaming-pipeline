import boto3
import botocore.exceptions
import json
import time
import io
import random
import uuid
import signal
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# =======================
# CONFIG (edit if you want)
# =======================
BUCKET_NAME = "my-streaming-raw-bronze"       # <-- matches your Terraform raw bucket
OBJECT_KEY_PREFIX = "raw/iot_humidity_"       # final key is prefix + timestamp + ".jsonl"
PART_SIZE = 100 * 1024 * 1024                 # 100 MB per multipart part
MAX_THREADS = 5
MAX_RETRIES = 3
RETRY_BACKOFF = 2
UPLOAD_INTERVAL_SECONDS = 3 * 60              # every 3 minutes (scheduler, can ignore if you just want one batch)
TARGET_BATCH_GB = 5                           # ~5 GB per upload (one batch)
ALIGN_TO_WALLCLOCK = True
RANDOM_SEED = None                            # set to an int for deterministic data

# =======================
# AWS CLIENT
# =======================
s3 = boto3.client("s3")

# =======================
# DATA GENERATION
# =======================
cities = {
    "New York":     (40.7128, -74.0060),
    "Los Angeles":  (34.0522, -118.2437),
    "Chicago":      (41.8781, -87.6298),
    "Houston":      (29.7604, -95.3698),
    "Phoenix":      (33.4484, -112.0740),
    "Seattle":      (47.6062, -122.3321),
    "Miami":        (25.7617, -80.1918),
    "Boston":       (42.3601, -71.0589),
}
city_names = list(cities.keys())

if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

def generate_humidity_record():
    """
    Create a single IoT sensor event (humidity/temperature/pressure).
    Some mild randomness + a little messiness to simulate real data.
    """
    now = datetime.utcnow() - timedelta(minutes=random.randint(0, 60 * 48))  # last 48 hours
    city = random.choice(city_names)
    base_lat, base_lon = cities[city]
    lat = round(base_lat + random.uniform(-0.01, 0.01), 6)
    lon = round(base_lon + random.uniform(-0.01, 0.01), 6)

    device_id = f"DEVICE-{random.randint(100, 999)}"
    sensor_id = f"SENSOR-{random.randint(1000, 9999)}"

    temperature_c = round(15 + random.random() * 20, 2)    # 15–35 C
    humidity_pct  = round(30 + random.random() * 60, 2)    # 30–90 %
    pressure_hpa  = round(980 + random.random() * 60, 2)   # 980–1040 hPa

    # 2–3% noisy fields
    if random.random() < 0.02: humidity_pct = None
    if random.random() < 0.02: temperature_c = "NA"

    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "device_id": device_id,
        "sensor_id": sensor_id,
        "location_city": city,
        "gps_latitude": lat,
        "gps_longitude": lon,
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "pressure_hpa": pressure_hpa
    }

# =======================
# MULTIPART UPLOAD HELPERS
# =======================
current_object_key = None  # set per-batch

def upload_part(part_number, upload_id, data_bytes):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = s3.upload_part(
                Bucket=BUCKET_NAME,
                Key=current_object_key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=data_bytes
            )
            return {'ETag': resp['ETag'], 'PartNumber': part_number}
        except botocore.exceptions.BotoCoreError as e:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(RETRY_BACKOFF * attempt)

def run_single_batch(target_bytes):
    """
    Generate JSONL until we reach ~target_bytes and upload as multipart to S3.
    """
    global current_object_key

    started_at = time.time()
    ts = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    current_object_key = f"{OBJECT_KEY_PREFIX}{ts}.jsonl"

    # Start MPU
    create = s3.create_multipart_upload(Bucket=BUCKET_NAME, Key=current_object_key)
    upload_id = create["UploadId"]
    print(f"\n🆔 MPU: {upload_id}  →  s3://{BUCKET_NAME}/{current_object_key}")

    parts = []
    futures = []
    uploaded = 0

    buffer = io.BytesIO()
    part_number = 1

    try:
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as pool:
            while uploaded < target_bytes:
                rec = generate_humidity_record()
                buffer.write((json.dumps(rec) + "\n").encode("utf-8"))

                if buffer.tell() >= PART_SIZE:
                    bytes_out = buffer.getvalue()
                    buffer = io.BytesIO()
                    futures.append(pool.submit(upload_part, part_number, upload_id, bytes_out))
                    uploaded += len(bytes_out)
                    print(f"📦 queued part {part_number} | batch {uploaded/1024/1024/1024:.2f} GB")
                    part_number += 1

            # flush the tail
            if buffer.tell() > 0:
                bytes_out = buffer.getvalue()
                futures.append(pool.submit(upload_part, part_number, upload_id, bytes_out))
                uploaded += len(bytes_out)
                print(f"📦 queued final part {part_number} | batch {uploaded/1024/1024/1024:.2f} GB")

            for fut in as_completed(futures):
                parts.append(fut.result())

        parts.sort(key=lambda p: p["PartNumber"])

        s3.complete_multipart_upload(
            Bucket=BUCKET_NAME,
            Key=current_object_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        dur = time.time() - started_at
        print(f"✅ Uploaded ~{uploaded/1024/1024/1024:.2f} GB in {dur:.1f}s → s3://{BUCKET_NAME}/{current_object_key}")

    except Exception as e:
        print(f"❌ batch failed: {e}")
        try:
            s3.abort_multipart_upload(Bucket=BUCKET_NAME, Key=current_object_key, UploadId=upload_id)
            print("⚠️ MPU aborted.")
        except Exception as e2:
            print(f"⚠️ also failed to abort: {e2}")
        raise

# =======================
# (Optional) SCHEDULER LOOP
# =======================
stop_requested = False
def _sig_handler(sig, frame):
    global stop_requested
    stop_requested = True
    print("\n🛑 stop requested; finishing current cycle...")
signal.signal(signal.SIGINT, _sig_handler)
signal.signal(signal.SIGTERM, _sig_handler)

def sleep_until(epoch):
    while not stop_requested:
        now = time.time()
        if now >= epoch:
            return
        time.sleep(min(1.0, epoch - now))

def next_epoch(interval_s, align=True):
    now = time.time()
    return (now - (now % interval_s) + interval_s) if align else (now + interval_s)

def main():
    target_bytes = int(TARGET_BATCH_GB * (1024 ** 3))
    print(f"⏱ interval: {UPLOAD_INTERVAL_SECONDS}s | target: ~{TARGET_BATCH_GB} GB per batch")

    # run once immediately (most students only need one batch for 5GB)
    run_single_batch(target_bytes)

    # comment out below if you only want one batch
    nxt = next_epoch(UPLOAD_INTERVAL_SECONDS, ALIGN_TO_WALLCLOCK)
    while not stop_requested:
        sleep_until(nxt)
        if stop_requested: break
        run_single_batch(target_bytes)
        nxt = next_epoch(UPLOAD_INTERVAL_SECONDS, ALIGN_TO_WALLCLOCK)

if _name_ == "_main_":
    main()
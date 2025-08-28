# ==========================
# Raw Bucket
# ==========================
resource "aws_s3_bucket" "raw_bucket" {
  bucket        = var.raw_bucket_name
  force_destroy = true

  lifecycle_rule {
    id                                     = "abort-incomplete-mpu"
    enabled                                = true
    abort_incomplete_multipart_upload_days = 7
  }

  tags = {
    Name        = "IoT Raw Data Bucket"
    Environment = "dev"
    Project     = "Streaming IoT Pipeline"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_encryption" {
  bucket = aws_s3_bucket.raw_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_ownership_controls" "raw_bucket_ownership" {
  bucket = aws_s3_bucket.raw_bucket.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "raw_block" {
  bucket = aws_s3_bucket.raw_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "raw_versioning" {
  bucket = aws_s3_bucket.raw_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ==========================
# Processed Bucket
# ==========================
resource "aws_s3_bucket" "processed_bucket" {
  bucket        = var.processed_bucket_name
  force_destroy = true

  lifecycle_rule {
    id                                     = "abort-incomplete-mpu"
    enabled                                = true
    abort_incomplete_multipart_upload_days = 7
  }

  tags = {
    Name        = "IoT Processed Data Bucket"
    Environment = "dev"
    Project     = "Streaming IoT Pipeline"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed_encryption" {
  bucket = aws_s3_bucket.processed_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_ownership_controls" "processed_bucket_ownership" {
  bucket = aws_s3_bucket.processed_bucket.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "processed_block" {
  bucket = aws_s3_bucket.processed_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "processed_versioning" {
  bucket = aws_s3_bucket.processed_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}
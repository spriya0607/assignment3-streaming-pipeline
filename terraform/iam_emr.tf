resource "aws_iam_role" "emr_service" {
  name = "EMR_ServiceRole_Assignment3"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "elasticmapreduce.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "emr_service_managed" {
  role       = aws_iam_role.emr_service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

# --- EMR AutoScaling role ---
resource "aws_iam_role" "emr_autoscaling" {
  name = "EMR_AutoScalingRole_Assignment3"

  # EMR uses Application Auto Scaling; trust both principals
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "application-autoscaling.amazonaws.com" },
        Action    = "sts:AssumeRole"
      },
      {
        Effect    = "Allow",
        Principal = { Service = "elasticmapreduce.amazonaws.com" },
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

#resource "aws_iam_role_policy_attachment" "emr_autoscaling_managed" {
#  role       = aws_iam_role.emr_autoscaling.name
#policy_arn = "arn:aws:iam::aws:policy/AmazonEMRManagedScalingPolicy"
#}

# --- EMR EC2 (nodes) role + instance profile ---
resource "aws_iam_role" "emr_ec2_role" {
  name = "EMR_EC2Role_Assignment3"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "ec2.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

# Base managed policy for EMR on EC2
resource "aws_iam_role_policy_attachment" "emr_ec2_managed" {
  role       = aws_iam_role.emr_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

# Restrict S3 access to your buckets (list + read/write objects)
resource "aws_iam_role_policy" "emr_ec2_s3_access" {
  name = "EMR_EC2_S3_Access_Assignment3"
  role = aws_iam_role.emr_ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid      = "ListBuckets",
        Effect   = "Allow",
        Action   = ["s3:ListAllMyBuckets"]
        Resource = "*"
      },
      {
        Sid    = "RawBucketAccess",
        Effect = "Allow",
        Action = [
          "s3:ListBucket"
        ],
        Resource = "arn:aws:s3:::${var.raw_bucket_name}"
      },
      {
        Sid    = "RawObjectsAccess",
        Effect = "Allow",
        Action = [
          "s3:GetObject", "s3:PutObject", "s3:DeleteObject",
          "s3:AbortMultipartUpload", "s3:ListBucketMultipartUploads"
        ],
        Resource = "arn:aws:s3:::${var.raw_bucket_name}/*"
      },
      {
        Sid    = "ProcessedBucketAccess",
        Effect = "Allow",
        Action = [
          "s3:ListBucket"
        ],
        Resource = "arn:aws:s3:::${var.processed_bucket_name}"
      },
      {
        Sid    = "ProcessedObjectsAccess",
        Effect = "Allow",
        Action = [
          "s3:GetObject", "s3:PutObject", "s3:DeleteObject",
          "s3:AbortMultipartUpload", "s3:ListBucketMultipartUploads"
        ],
        Resource = "arn:aws:s3:::${var.processed_bucket_name}/*"
      }
    ]
  })
}

# Instance profile for EMR EC2
resource "aws_iam_instance_profile" "emr_ec2" {
  name = "EMR_EC2InstanceProfile_Assignment3"
  role = aws_iam_role.emr_ec2_role.name
}
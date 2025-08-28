resource "aws_emr_cluster" "streaming_emr" {
  name          = "streaming-iot-cluster"
  release_label = "emr-6.15.0" # <- fixed: 6.14.1 was invalid

  applications = ["Hadoop", "Spark"]

  # IAM roles from iam_emr.tf
  service_role = aws_iam_role.emr_service.arn
  #autoscaling_role = aws_iam_role.emr_autoscaling.arn

  # Keep cluster alive so you can submit multiple steps
  keep_job_flow_alive_when_no_steps = true
  step_concurrency_level            = 1
  visible_to_all_users              = true

  # Write EMR logs to S3 (you can point to raw or processed; using processed/logs here)
  log_uri = "s3://my-streaming-raw-bronze/emr-logs/"

  ec2_attributes {
    subnet_id        = var.subnet_id
    instance_profile = aws_iam_instance_profile.emr_ec2.arn
  }

  # Master node
  master_instance_group {
    instance_type  = "m5.xlarge"
    instance_count = 1
    ebs_config {
      size                 = 64
      type                 = "gp3"
      volumes_per_instance = 1
    }
  }

  # Core nodes
  core_instance_group {
    instance_type  = "m5.xlarge"
    instance_count = 2
    ebs_config {
      size                 = 128
      type                 = "gp3"
      volumes_per_instance = 1
    }
  }

  # Useful Spark & S3A defaults
  configurations_json = jsonencode([
    {
      Classification = "spark-defaults",
      Properties = {
        "spark.sql.shuffle.partitions"    = "200",
        "spark.serializer"                = "org.apache.spark.serializer.KryoSerializer",
        "spark.hadoop.fs.s3a.fast.upload" = "true"
      }
    },
    {
      Classification = "core-site",
      Properties = {
        "fs.s3a.aws.credentials.provider" = "com.amazonaws.auth.InstanceProfileCredentialsProvider"
      }
    }
  ])

  tags = {
    Project     = "Streaming IoT Pipeline"
    Environment = "dev"
  }
}
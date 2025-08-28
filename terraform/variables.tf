variable "raw_bucket_name" {
  default = "my-streaming-raw-bronze"
}

variable "processed_bucket_name" {
  default = "my-streaming-processed-gold"
}

variable "subnet_id" {
  description = "The subnet ID where the EMR cluster should be provisioned"
  default     = "subnet-08982dd9a9768d211"
  type        = string
}
variable "emr_cluster_id" {
  description = "Existing EMR cluster ID to monitor "
  type        = string
}

variable "sns_topic_arn" {
  description = "Optional SNS topic ARN for alarm notifications"
  type        = string
  default     = null
}
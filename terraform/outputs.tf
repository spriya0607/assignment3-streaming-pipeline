output "emr_cluster_id" {
  description = "ID of the EMR cluster"
  value       = aws_emr_cluster.streaming_emr.id
}

output "emr_cluster_name" {
  description = "Name of the EMR cluster"
  value       = aws_emr_cluster.streaming_emr.name
}
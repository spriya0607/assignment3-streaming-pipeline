locals {
  alarm_dims = {
    JobFlowId = var.emr_cluster_id
  }
  alarm_actions = var.sns_topic_arn == null ? [] : [var.sns_topic_arn]
}

/*
  Alarm 1: EMR is busy (low YARN memory availability)
  Fires when YARNMemoryAvailablePercentage < 15 for 2 consecutive 5-min periods
*/
resource "aws_cloudwatch_metric_alarm" "emr_busy" {
  alarm_name          = "emr-busy-${var.emr_cluster_id}"
  alarm_description   = "EMR YARN memory is < 15% (cluster ${var.emr_cluster_id})"
  namespace           = "AWS/ElasticMapReduce"
  metric_name         = "YARNMemoryAvailablePercentage"
  dimensions          = local.alarm_dims

  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 15
  comparison_operator = "LessThanThreshold"

  treat_missing_data  = "missing"
  alarm_actions       = local.alarm_actions
  ok_actions          = local.alarm_actions
}

/*
  Alarm 2: EMR idle too long
  Fires when IsIdle == 1 for 3 consecutive 5-min periods
*/
resource "aws_cloudwatch_metric_alarm" "emr_idle_long" {
  alarm_name          = "emr-idle-long-${var.emr_cluster_id}"
  alarm_description   = "EMR cluster idle for >= 15 minutes (cluster ${var.emr_cluster_id})"
  namespace           = "AWS/ElasticMapReduce"
  metric_name         = "IsIdle"
  dimensions          = local.alarm_dims

  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"

  treat_missing_data  = "missing"
  alarm_actions       = local.alarm_actions
  ok_actions          = local.alarm_actions
}
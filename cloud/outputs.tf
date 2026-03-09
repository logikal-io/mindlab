output "gcp_workload_identity_provider" {
  value = module.gcp_github_auth.workload_identity_provider
}

output "gcp_service_account_email" {
  value = module.gcp_github_auth.service_account_emails["testing"]
}

output "aws_role" {
  value = module.aws_github_auth.iam_role_arns["testing"]
}

output "gcs_test_bucket_url" {
  value = module.gcs_test_data_bucket.url
}

output "aws_s3_test_bucket_url" {
  value = "s3://${module.s3_test_data_bucket.name}"
}

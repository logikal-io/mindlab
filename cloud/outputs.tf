output "workload_identity_provider" {
  description = "The full identifier of the GitHub workload identity pool provider"
  value = module.github_auth.workload_identity_provider
}

output "service_account" {
  description = "The email of the Google Cloud service account used for running tests"
  value = module.github_auth.service_account_emails["testing"]
}

output "gcs_test_bucket_url" {
  description = "The Gogle Cloud Storage test data bucket URL"
  value = module.gcs_test_data_bucket.url
}

output "aws_s3_test_bucket_url" {
  description = "The AWS S3 test data bucket URL"
  value = "s3://${module.s3_test_data_bucket.name}"
}

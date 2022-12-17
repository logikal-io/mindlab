# GitHub Actions
module "github_auth" {
  source = "github.com/logikal-io/terraform-modules//gcp/github-auth?ref=v1.1.0"

  service_account_accesses = {
    testing = ["logikal-io/mindlab"]
  }
}

resource "google_project_iam_member" "service_user" {
  project = var.project_id
  role = "roles/serviceusage.serviceUsageConsumer"
  member = "serviceAccount:${module.github_auth.service_account_emails["testing"]}"
}

resource "google_project_iam_member" "bigquery_job_user" {
  project = var.project_id
  role = "roles/bigquery.jobUser"
  member = "serviceAccount:${module.github_auth.service_account_emails["testing"]}"
}

# Buckets
module "gcs_test_data_bucket" {
  source = "github.com/logikal-io/terraform-modules//gcp/gcs-bucket?ref=v1.1.0"

  name = "test-data"
  suffix = var.project_id
  public = true
}

module "s3_test_data_bucket" {
  source = "github.com/logikal-io/terraform-modules//aws/s3-bucket?ref=v1.1.0"

  name = "test-data"
  suffix = var.project_id
  public = true
}

# BigQuery
resource "google_project_service" "bigquery" {
  service = "bigquery.googleapis.com"
}

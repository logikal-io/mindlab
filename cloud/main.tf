# GitHub Actions
module "gcp_github_auth" {
  source = "github.com/logikal-io/terraform-modules//gcp/github-auth?ref=v1.4.1"

  service_account_accesses = {
    testing = ["logikal-io/mindlab"]
  }
}

module "aws_github_auth" {
  source = "github.com/logikal-io/terraform-modules//aws/github-auth?ref=v1.4.1"

  project_id = var.project_id
  role_accesses = {
    testing = ["logikal-io/mindlab"]
  }
}

provider "aws" {
  profile = var.organization_id
  region = "eu-central-1"  # override (Athena and Glue are not available in eu-central-2 yet)
  alias = "eu_central_1"
}

# BigQuery
resource "google_project_service" "bigquery" {
  service = "bigquery.googleapis.com"
}

# Buckets
module "gcs_test_data_bucket" {
  source = "github.com/logikal-io/terraform-modules//gcp/gcs-bucket?ref=v1.4.1"

  name = "test-data"
  suffix = var.project_id
}

resource "google_storage_bucket_object" "test_data_order_line_items" {
  bucket = module.gcs_test_data_bucket.name
  name = "order_line_items.csv"
  source = "${var.terragrunt_dir}/../tests/mindlab/data/order_line_items.csv"
}

module "s3_test_data_bucket" {
  providers = {aws = aws.eu_central_1}
  source = "github.com/logikal-io/terraform-modules//aws/s3-bucket?ref=v1.4.1"

  name = "test-data"
  suffix = var.project_id
}

resource "aws_s3_object" "test_data_order_line_items" {
  provider = aws.eu_central_1

  bucket = module.s3_test_data_bucket.name
  key = "order_line_items/data.csv"
  source = "${var.terragrunt_dir}/../tests/mindlab/data/order_line_items.csv"
}

# Athena
resource "aws_glue_catalog_database" "test" {
  provider = aws.eu_central_1

  name = "test_${var.project}"
  description = "MindLab test data"
  location_uri = "s3://${module.s3_test_data_bucket.name}"
}

resource "aws_glue_catalog_table" "order_line_items" {
  provider = aws.eu_central_1

  database_name = aws_glue_catalog_database.test.name
  name = "order_line_items"
  table_type = "EXTERNAL_TABLE"

  parameters = {
    "EXTERNAL" = "TRUE"
    "classification" = "csv"
    "skip.header.line.count" = "1"
  }

  storage_descriptor {
    location      = "s3://${module.s3_test_data_bucket.name}/order_line_items/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.OpenCSVSerde"
      parameters = {
        "separatorChar" = ","
      }
    }

    columns {
      name = "order_id"
      type = "int"
    }
    columns {
      name = "sku"
      type = "string"
    }
    columns {
      name = "quantity"
      type = "int"
    }
    columns {
      name = "unit_price"
      type = "float"
    }
    columns {
      name = "shipping"
      type = "float"
    }
  }
}

# Permissions
locals {
  service_accounts = toset([
    module.gcp_github_auth.service_account_emails["testing"],
    "docs-uploader@docs-logikal-io.iam.gserviceaccount.com",
  ])
}

resource "google_project_iam_member" "service_user" {
  project = var.project_id
  role = "roles/serviceusage.serviceUsageConsumer"
  member = "serviceAccount:${module.gcp_github_auth.service_account_emails["testing"]}"
}

resource "google_project_iam_member" "bigquery_job_user" {
  for_each = local.service_accounts

  project = var.project_id
  role = "roles/bigquery.jobUser"
  member = "serviceAccount:${each.key}"
}

data "aws_iam_policy_document" "test_data_bucket_access" {
  version = "2012-10-17"

  statement {
    actions = ["s3:ListBucket", "s3:GetObject"]
    resources = [module.s3_test_data_bucket.arn, "${module.s3_test_data_bucket.arn}/*"]
  }
}

resource "aws_iam_policy" "test_data_bucket_access" {
  name = "test-data-bucket-access"
  policy = data.aws_iam_policy_document.test_data_bucket_access.json
}

resource "aws_iam_role_policy_attachment" "test_data_bucket_access" {
  role = module.aws_github_auth.iam_role_names["testing"]
  policy_arn = aws_iam_policy.test_data_bucket_access.arn
}

data "aws_iam_policy" "athena_primary_workgroup_access" {
  name = "athena-primary-workgroup-access"
}

resource "aws_iam_role_policy_attachment" "athena_primary_workgroup_access" {
  role = module.aws_github_auth.iam_role_names["testing"]
  policy_arn = data.aws_iam_policy.athena_primary_workgroup_access.arn
}

data "aws_iam_policy_document" "test_data_glue_access" {
  statement {
    actions = ["glue:GetDatabase", "glue:GetTable"]
    resources = [
      aws_glue_catalog_database.test.arn,
      aws_glue_catalog_table.order_line_items.arn,
    ]
  }
}

resource "aws_iam_policy" "test_data_glue_access" {
  name = "test-data-glue-access"
  policy = data.aws_iam_policy_document.test_data_glue_access.json
}

resource "aws_iam_role_policy_attachment" "test_data_glue_access" {
  role = module.aws_github_auth.iam_role_names["testing"]
  policy_arn = aws_iam_policy.test_data_glue_access.arn
}

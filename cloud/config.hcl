locals {
  state_backend = "gcs"
  organization = "logikal.io"
  project = "mindlab"

  providers = {
    google = {
      version = "~> 7.22"
      region = "europe-west6"
    }
    aws = {
      version = "~> 6.35"
      region = "eu-central-2"
    }
  }

  modules = {
    "github.com/logikal-io/terraform-modules" = "v5.0.0"
  }
}

inputs = {
  project = local.project
  terragrunt_dir = get_terragrunt_dir()
}

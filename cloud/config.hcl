locals {
  organization = "logikal.io"
  project = "mindlab"
  backend = "gcs"

  providers = {
    google = {
      version = "~> 5.9"
      region = "europe-west6"
    }
    aws = {
      version = "~> 5.35"
      region = "eu-central-2"
    }
  }
}

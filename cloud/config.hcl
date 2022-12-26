locals {
  organization = "logikal.io"
  project = "mindlab"
  backend = "gcs"

  providers = {
    google = {
      version = "~> 4.44"
      region = "europe-west6"
    }
    aws = {
      version = "~> 4.41"
      region = "eu-central-2"
    }
  }
}

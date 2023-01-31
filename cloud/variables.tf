variable "organization_id" {
  description = "The organization ID to use"
  type = string
}

variable "project" {
  description = "The project to use"
  type = string
}

variable "project_id" {
  description = "The project ID to use"
  type = string
}

variable "terragrunt_dir" {
  description = "The folder in which the Terragrunt configuration file is"
  type = string
}

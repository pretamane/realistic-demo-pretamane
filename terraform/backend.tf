# /terraform/backend.tf

terraform {
  backend "s3" {
    bucket = "realistic-demo-pretamane-terraform-state"
    key    = "terraform.tfstate"
    region = "ap-southeast-1"
    dynamodb_table = "realistic-demo-pretamane-terraform-locks"
  }
}
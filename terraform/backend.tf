# /terraform/backend.tf

terraform {
  backend "s3" {
    bucket = "terraform-state-realistic-demo-pretamane" # We’ll create this bucket next
    key    = "terraform.tfstate"
    region = "ap-southeast-1"
    dynamodb_table = "terraform-locks" # For state locking — we’ll create this too
  }
}
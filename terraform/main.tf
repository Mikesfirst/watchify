resource "aws_vpc" "watchify" {
  cidr_block = "10.0.0.0/16"
}

terraform {
  backend "s3" {
    bucket = "AWS_BUCKET_NAME"
    key    = "AWS_BUCKET_KEY_NAME"
    region = "AWS_REGION"
    role_arn = "AWS_ROLE"
  }
}
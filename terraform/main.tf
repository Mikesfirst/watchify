#resource "aws_vpc" "watchify" {
# cidr_block = "10.0.0.0/16"
#}

#terraform {
# backend "s3" {
#  bucket = "AWS_BUCKET_NAME"
# key    = "AWS_BUCKET_KEY_NAME"
#region = "AWS_REGION"
#assume_role {
#   role_arn = "AWS_ROLE"
#     }
# }
#}

resource "tls_private_key" "rsa-4096" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "key_pair" {
  key_name   = var.key_name
  public_key = tls_private_key.rsa-4096.public_key_openssh
}

resource "local_file" "private_key" {
  content  = tls_private_key.rsa-4096.private_key_pem
  filename = var.key_name
}

variable "key_name" {}

resource "aws_instance" "watchify" {
  ami           = "ami-053b0d53c279acc90"
  instance_type = "t3.micro"
  key_name      = aws_key_pair.key_pair.key_name

  tags = {
    Name = "Watchify"
  }
}
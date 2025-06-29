terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_vpc" "e2e-test-vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "e2e-test-vpc"
    Environment = var.environment
  }
}

resource "aws_internet_gateway" "e2e-test-vpc" {
  vpc_id = aws_vpc.e2e-test-vpc.id

  tags = {
    Name = "e2e-test-vpc-igw"
    Environment = var.environment
  }
}

resource "aws_subnet" "e2e-test-vpc_public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.e2e-test-vpc.id
  cidr_block        = cidrsubnet(aws_vpc.e2e-test-vpc.cidr_block, 8, count.index)
  availability_zone = var.availability_zones[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "e2e-test-vpc-public-${count.index + 1}"
    Type = "public"
    Environment = var.environment
  }
}

resource "aws_route_table" "e2e-test-vpc_public" {
  vpc_id = aws_vpc.e2e-test-vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.e2e-test-vpc.id
  }

  tags = {
    Name = "e2e-test-vpc-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table_association" "e2e-test-vpc_public" {
  count          = length(aws_subnet.e2e-test-vpc_public)
  subnet_id      = aws_subnet.e2e-test-vpc_public[count.index].id
  route_table_id = aws_route_table.e2e-test-vpc_public.id
}

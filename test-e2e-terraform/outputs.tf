output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.e2e-test-vpc.id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block"
  value       = aws_vpc.e2e-test-vpc.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.e2e-test-vpc_public[*].id
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = aws_internet_gateway.e2e-test-vpc.id
}

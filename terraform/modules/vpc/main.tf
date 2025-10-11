# /terraform/modules/vpc/main.tf

provider "aws" {
  region = var.region
}

# ---------------------------
# VPC (Tiny /27 = 32 IPs — enough for 2 subnets)
# ---------------------------

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/24"
  enable_dns_support   = true  #  ADD THIS
  enable_dns_hostnames = true  #  ADD THIS
  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# ---------------------------
# Internet Gateway
# ---------------------------

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "${var.project_name}-igw"
  }
}

# ---------------------------
# Public Subnet A (ap-southeast-1a)
# ---------------------------

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.0.0/26" # First 64 IPs
  map_public_ip_on_launch = true
  availability_zone       = "${var.region}a"

  tags = {
    Name = "${var.project_name}-public-subnet-a"
  }
}

# ---------------------------
# Public Subnet B (ap-southeast-1b)
# ---------------------------

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.0.64/26" # Next 64 IPs
  map_public_ip_on_launch = true
  availability_zone       = "${var.region}b"

  tags = {
    Name = "${var.project_name}-public-subnet-b"
  }
}

# ---------------------------
# Route Table (Public)
# ---------------------------

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# ---------------------------
# Security Group (Minimal)
# ---------------------------

resource "aws_security_group" "eks_node" {
  name        = "${var.project_name}-eks-node-sg"
  description = "Allow ALB and SSH access to EKS node"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-eks-node-sg"
  }
}

# Add to modules/vpc/main.tf — after security group

# resource "aws_vpc_endpoint" "eks" {
#   vpc_id             = aws_vpc.main.id
#   service_name       = "com.amazonaws.${var.region}.eks"
#   vpc_endpoint_type  = "Interface"
#   subnet_ids         = [aws_subnet.public_a.id, aws_subnet.public_b.id]
#   security_group_ids = [aws_security_group.eks_node.id]

#   private_dns_enabled = true
# }

# resource "aws_vpc_endpoint" "ecr_dkr" {
#   vpc_id             = aws_vpc.main.id
#   service_name       = "com.amazonaws.${var.region}.ecr.dkr"
#   vpc_endpoint_type  = "Interface"
#   subnet_ids         = [aws_subnet.public_a.id, aws_subnet.public_b.id]
#   security_group_ids = [aws_security_group.eks_node.id]

#   private_dns_enabled = true
# }

# resource "aws_vpc_endpoint" "ecr_api" {
#   vpc_id             = aws_vpc.main.id
#   service_name       = "com.amazonaws.${var.region}.ecr.api"
#   vpc_endpoint_type  = "Interface"
#   subnet_ids         = [aws_subnet.public_a.id, aws_subnet.public_b.id]
#   security_group_ids = [aws_security_group.eks_node.id]

#   private_dns_enabled = true
# }

# ---------------------------
# Outputs
# ---------------------------

output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = [aws_subnet.public_a.id, aws_subnet.public_b.id] #  Now returns 2 subnets
}

output "eks_node_security_group_id" {
  value = aws_security_group.eks_node.id
}
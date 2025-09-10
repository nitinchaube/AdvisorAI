#!/bin/bash

# Quick setup for Amazon Linux EC2 instance
# Run these commands one by one on your EC2 instance

echo "🚀 Quick setup for Amazon Linux EC2 instance..."

# Update system
echo "Updating system packages..."
sudo yum update -y

# Install Docker
echo "Installing Docker..."
sudo amazon-linux-extras install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install additional tools
echo "Installing additional tools..."
sudo yum install -y curl wget git htop

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/advisorai
sudo chown ec2-user:ec2-user /opt/advisorai

# Configure firewall
echo "Configuring firewall..."
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=6379/tcp
sudo firewall-cmd --reload

echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Log out and log back in: exit"
echo "2. Reconnect: ssh -i your-key.pem ec2-user@your-ec2-ip"
echo "3. Copy your application files to /opt/advisorai/"
echo "4. Run the deployment script"

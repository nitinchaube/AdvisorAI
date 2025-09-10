#!/bin/bash

# EC2 Instance Setup Script for AdvisorAI Backend
# Run this script on your EC2 instance to prepare the environment

set -e

echo "🔧 Setting up EC2 instance for AdvisorAI Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Update system packages
print_status "Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_status "Docker installed successfully"
else
    print_status "Docker is already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose is already installed"
fi

# Install additional tools
print_status "Installing additional tools..."
sudo apt-get install -y curl wget git htop

# Create application directory
print_status "Creating application directory..."
sudo mkdir -p /opt/advisorai
sudo chown $USER:$USER /opt/advisorai

# Configure firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    print_status "Configuring firewall..."
    sudo ufw allow 22    # SSH
    sudo ufw allow 5000  # Backend
    sudo ufw allow 6379  # Redis (if needed externally)
    sudo ufw --force enable
fi

# Set up log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/docker-containers > /dev/null <<EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
EOF

# Create systemd service for auto-start (optional)
print_status "Creating systemd service for auto-start..."
sudo tee /etc/systemd/system/advisorai.service > /dev/null <<EOF
[Unit]
Description=AdvisorAI Backend Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/advisorai
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable advisorai.service

print_status "🎉 EC2 setup completed!"
print_status ""
print_status "Next steps:"
print_status "1. Copy your application files to /opt/advisorai/"
print_status "2. Update your .env file with production values"
print_status "3. Run ./deploy.sh to start the services"
print_status ""
print_status "To enable auto-start on boot:"
print_status "sudo systemctl enable advisorai.service"
print_status ""
print_warning "Please log out and log back in for Docker group changes to take effect"

# AdvisorAI Backend AWS EC2 Deployment Guide

This guide will help you deploy the AdvisorAI backend with Redis on a single EC2 instance using Docker.

## Prerequisites

- AWS EC2 instance (recommended: t3.medium or larger)
- SSH access to your EC2 instance
- Your application files and Firebase credentials

## Quick Start

### 1. Launch EC2 Instance

1. **Launch an EC2 instance** with the following specifications:
   - **Instance Type**: t3.medium or larger
   - **OS**: Ubuntu 20.04 LTS or later
   - **Storage**: 20GB+ EBS volume

2. **Security Group Configuration**:
   ```
   SSH (22) - Your IP
   HTTP (80) - 0.0.0.0/0
   HTTPS (443) - 0.0.0.0/0 (optional)
   Custom TCP (5000) - 0.0.0.0/0 (for direct backend access)
   ```

### 2. Connect and Setup

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Download and run the setup script
wget https://raw.githubusercontent.com/your-repo/advisorai/main/backend/ec2-setup.sh
chmod +x ec2-setup.sh
./ec2-setup.sh

# Log out and log back in for Docker group changes
exit
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. Deploy Application

```bash
# Navigate to application directory
cd /opt/advisorai

# Copy your application files (choose one method):

# Method 1: Using Git
git clone https://github.com/your-username/advisorai.git .
cd backend

# Method 2: Using SCP (from your local machine)
# scp -i your-key.pem -r ./backend/* ubuntu@your-ec2-ip:/opt/advisorai/

# Method 3: Using rsync (from your local machine)
# rsync -avz -e "ssh -i your-key.pem" ./backend/ ubuntu@your-ec2-ip:/opt/advisorai/

# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 4. Configure Environment Variables

```bash
# Edit your .env file with production values
nano .env

# Add your actual API keys and configuration
OPENAI_API_KEY=your_actual_openai_key
GOOGLE_API_KEY=your_actual_google_key
MONGODB_URI=your_mongodb_connection_string
# Add other required environment variables
```

### 5. Start Services

```bash
# Start the services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Optional: Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt-get install nginx -y

# Copy the nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/advisorai
sudo ln -s /etc/nginx/sites-available/advisorai /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Update server name in nginx.conf
sudo nano /etc/nginx/sites-available/advisorai
# Replace 'your-domain.com' with your actual domain or EC2 public IP

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Verification

### Health Checks

- **Backend Health**: `http://your-ec2-ip:5000/api/health`
- **Redis Health**: `docker exec advisorai_redis redis-cli ping`

### Test Endpoints

```bash
# Test backend
curl http://your-ec2-ip:5000/api/health

# Test Redis
docker exec advisorai_redis redis-cli ping
```

## Management Commands

### Service Management

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down

# Update and redeploy
git pull
docker-compose -f docker-compose.prod.yml up --build -d
```

### System Management

```bash
# Check resource usage
docker stats

# Clean up unused images
docker image prune -f

# View system resources
htop
```

### Auto-start on Boot

```bash
# Enable auto-start service
sudo systemctl enable advisorai.service

# Check service status
sudo systemctl status advisorai.service
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   sudo netstat -tulpn | grep :5000
   sudo kill -9 <PID>
   ```

2. **Docker Permission Denied**
   ```bash
   sudo usermod -aG docker $USER
   # Log out and log back in
   ```

3. **Redis Connection Failed**
   ```bash
   docker logs advisorai_redis
   docker restart advisorai_redis
   ```

4. **Backend Health Check Failed**
   ```bash
   docker logs advisorai_backend
   docker restart advisorai_backend
   ```

### Logs and Debugging

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs

# View specific service logs
docker logs advisorai_backend
docker logs advisorai_redis

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f backend
```

## File Structure

```
/opt/advisorai/
├── docker-compose.prod.yml    # Production Docker Compose
├── Dockerfile                 # Backend Dockerfile
├── .env                       # Environment variables
├── .env.prod                  # Environment template
├── deploy.sh                  # Deployment script
├── ec2-setup.sh              # EC2 setup script
├── nginx.conf                 # Nginx configuration
├── app.py                     # Main application
├── requirements.txt           # Python dependencies
├── firebae_key1.json         # Firebase credentials
├── Data/                      # Application data
├── VectorDB/                  # Vector database
└── uploads/                   # File uploads
```

## Security Considerations

1. **Firewall**: Only open necessary ports
2. **Environment Variables**: Never commit sensitive data to version control
3. **Firebase Credentials**: Keep service account keys secure
4. **HTTPS**: Use SSL certificates for production
5. **Regular Updates**: Keep system and Docker images updated

## Monitoring

### Health Monitoring

- Set up CloudWatch or similar monitoring
- Monitor CPU, memory, and disk usage
- Set up alerts for service failures

### Log Monitoring

- Use ELK stack or similar for log aggregation
- Monitor application logs for errors
- Set up log rotation to prevent disk space issues

## Backup Strategy

1. **Data Backup**: Regular backups of Data/ and VectorDB/ directories
2. **Configuration Backup**: Backup .env and configuration files
3. **Database Backup**: Regular MongoDB backups if using external MongoDB

## Scaling

For higher traffic, consider:
1. **Load Balancer**: Use Application Load Balancer
2. **Multiple Instances**: Deploy on multiple EC2 instances
3. **Database**: Use managed Redis (ElastiCache) and MongoDB (DocumentDB)
4. **CDN**: Use CloudFront for static assets

## Support

For issues and questions:
1. Check logs first
2. Verify environment variables
3. Test individual services
4. Check AWS CloudWatch logs
5. Review this documentation

---

**Note**: This deployment is designed for single-instance setup. For production at scale, consider using AWS ECS, EKS, or other container orchestration services.

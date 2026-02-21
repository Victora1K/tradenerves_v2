# Tradenerves Docker Deployment Guide

Complete guide for containerized deployment of Tradenerves application using Docker.

## 📋 Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- Your pattern database (`stocks.db`)

### Install Docker

**macOS/Windows:**
- Download [Docker Desktop](https://www.docker.com/products/docker-desktop)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER  # Add user to docker group
```

**Amazon Linux 2:**
```bash
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🚀 Quick Start (Development)

### 1. Prepare Database

Ensure your database exists with pattern data:

```bash
cd tradenerves-backend/backend

# If stocks.db doesn't exist, initialize it
python init_db.py
python data/fetch_data.py  # Fetch stock data
python build_patterns.py   # Build pattern tables
```

### 2. Build and Run Containers

From the **Tradenerves root directory**:

```bash
# Build images (first time only)
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Access Application

- **Frontend:** http://localhost
- **Backend API:** http://localhost:5000/api
- **Health Check:** http://localhost:5000/api/health

### 4. Stop Containers

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v
```

## 🏗️ Project Structure

```
Tradenerves/
├── docker-compose.yml              # Orchestration config
├── tradenerves-backend/
│   ├── Dockerfile                  # Backend container
│   ├── .dockerignore
│   └── backend/
│       ├── app.py
│       ├── requirements.txt
│       └── db/
│           └── stocks.db          # Mounted as volume
└── tradenerves-frontend/
    ├── Dockerfile                  # Frontend container
    ├── nginx.conf                  # Nginx config
    ├── .dockerignore
    └── webfront/
        ├── package.json
        ├── src/
        └── public/
```

## 🔧 Docker Configuration

### Backend Service

- **Image:** Python 3.11
- **Port:** 5000
- **Server:** Gunicorn (3 workers)
- **Database:** Mounted from `./tradenerves-backend/backend/db`

### Frontend Service

- **Build:** Node 18 + Yarn
- **Server:** Nginx
- **Port:** 80
- **Proxy:** `/api` → `http://backend:5000`

## 📦 Production Deployment

### AWS EC2 Deployment

**1. Prepare EC2 Instance:**

```bash
# SSH into EC2
ssh ec2-user@<your-ec2-ip>

# Install Docker
sudo yum update -y
sudo yum install docker git -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes
exit
ssh ec2-user@<your-ec2-ip>
```

**2. Clone and Setup:**

```bash
# Clone repository
git clone <your-repo-url> tradenerves
cd tradenerves

# Copy your database
# Option A: SCP from local
scp stocks.db ec2-user@<your-ec2-ip>:~/tradenerves/tradenerves-backend/backend/db/

# Option B: Build on EC2
cd tradenerves-backend/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python build_patterns.py
deactivate
cd ../..
```

**3. Build and Run:**

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

**4. Configure Security Groups:**

In AWS Console:
- Inbound Rule: HTTP (80) from 0.0.0.0/0
- Inbound Rule: Custom TCP (5000) from frontend container (optional)

**5. Setup Domain (Optional):**

```bash
# Install certbot
sudo yum install certbot python3-certbot-nginx -y

# Stop nginx container temporarily
docker-compose stop frontend

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Update nginx.conf with SSL settings (see SSL section below)

# Restart frontend
docker-compose up -d frontend
```

## 🔒 SSL/HTTPS Setup

Update `tradenerves-frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Update `docker-compose.yml` to mount SSL certificates:

```yaml
frontend:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
  ports:
    - "80:80"
    - "443:443"
```

## 🛠️ Maintenance Commands

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker-compose build backend
docker-compose build frontend

# Restart service
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Database Backup

```bash
# Backup database
docker-compose exec backend cp /app/db/stocks.db /app/db/stocks.db.backup

# Copy to host
docker cp tradenerves-backend:/app/db/stocks.db ./stocks_backup.db

# Restore database
docker cp ./stocks_backup.db tradenerves-backend:/app/db/stocks.db
docker-compose restart backend
```

### Shell Access

```bash
# Backend container shell
docker-compose exec backend /bin/bash

# Frontend container shell
docker-compose exec frontend /bin/sh

# Run Python commands
docker-compose exec backend python build_patterns.py
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check container status
docker-compose ps

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Not Persisting

```bash
# Verify volume mount
docker-compose exec backend ls -la /app/db/

# Check docker-compose.yml volumes section
# Ensure: - ./tradenerves-backend/backend/db:/app/db
```

### Frontend Can't Reach Backend

```bash
# Check network
docker network ls
docker network inspect tradenerves_default

# Verify backend health
curl http://localhost:5000/api/health

# Check nginx proxy config
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

### Port Already in Use

```bash
# Find process using port 80
sudo lsof -i :80
sudo kill -9 <PID>

# Or change ports in docker-compose.yml
ports:
  - "8080:80"  # Use port 8080 instead
```

## 🔄 Update Workflow

### Update Application Code

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:5000/api/health
```

### Update Dependencies

**Backend:**
```bash
# Edit requirements.txt
# Then rebuild
docker-compose build backend
docker-compose up -d backend
```

**Frontend:**
```bash
# Edit package.json
# Then rebuild
docker-compose build frontend
docker-compose up -d frontend
```

## 📊 Monitoring

### Resource Usage

```bash
# View container stats
docker stats

# View disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

### Health Checks

```bash
# Backend health
curl http://localhost:5000/api/health

# Frontend health
curl http://localhost/

# Check container health
docker-compose ps
```

## 🚨 Production Checklist

- [ ] Database has pattern data (`stocks.db` exists and populated)
- [ ] Environment variables set (if any)
- [ ] Security groups configured (AWS EC2)
- [ ] SSL certificates obtained (if using HTTPS)
- [ ] Domain DNS configured (Route 53 or other)
- [ ] Firewall rules set (ports 80, 443)
- [ ] Docker containers auto-restart enabled
- [ ] Database backup strategy in place
- [ ] Monitoring/logging configured

## 📝 Environment Variables (Optional)

Create `.env` file in root:

```env
# Backend
FLASK_ENV=production
DATABASE_PATH=/app/db/stocks.db

# Frontend
REACT_APP_API_URL=http://localhost:5000
```

Update `docker-compose.yml`:

```yaml
backend:
  env_file:
    - .env
```

## 🎯 Performance Tuning

### Backend (Gunicorn)

Edit `tradenerves-backend/Dockerfile`:

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "4", \           # Increase workers
     "--timeout", "120", \
     "--worker-class", "sync", \
     "app:app"]
```

### Nginx Caching

Add to `tradenerves-frontend/nginx.conf`:

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 🆘 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify health: `curl http://localhost:5000/api/health`
3. Restart services: `docker-compose restart`
4. Rebuild from scratch: `docker-compose down && docker-compose build --no-cache && docker-compose up -d`

**Happy Deploying! 🚀**

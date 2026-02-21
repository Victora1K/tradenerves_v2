# 🐳 Docker Quick Start

Get Tradenerves running in containers with 3 commands.

## Prerequisites

- Docker & Docker Compose installed
- Your `stocks.db` database in `tradenerves-backend/backend/db/`

## Run Locally

```bash
# 1. Build containers (first time only, ~5-10 minutes)
docker-compose build

# 2. Start application
docker-compose up -d

# 3. Access application
# Frontend: http://localhost
# Backend: http://localhost:5000/api/health
```

## Stop Application

```bash
docker-compose down
```

## Common Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose build
docker-compose up -d

# Shell access
docker-compose exec backend /bin/bash
docker-compose exec frontend /bin/sh
```

## Deploy to AWS EC2

```bash
# 1. SSH into EC2
ssh ec2-user@<your-ip>

# 2. Install Docker
sudo yum update -y
sudo yum install docker git -y
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Logout and login again
exit
ssh ec2-user@<your-ip>

# 4. Clone and run
git clone <your-repo> tradenerves
cd tradenerves

# Copy database (if needed)
# scp stocks.db ec2-user@<your-ip>:~/tradenerves/tradenerves-backend/backend/db/

docker-compose build
docker-compose up -d

# 5. Configure AWS Security Groups
# Allow inbound: HTTP (80) from 0.0.0.0/0
```

## Troubleshooting

**Container won't start:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

**Database not found:**
```bash
# Verify database exists
ls tradenerves-backend/backend/db/stocks.db

# Build patterns if missing
docker-compose exec backend python build_patterns.py
```

**Port 80 in use:**
```bash
# Edit docker-compose.yml
# Change frontend ports: "8080:80"
```

**Can't reach backend:**
```bash
# Test backend directly
curl http://localhost:5000/api/health

# Should return: {"status":"healthy","service":"tradenerves-backend"}
```

---

📖 **Full documentation:** See `DOCKER_DEPLOYMENT.md` for complete guide including SSL, monitoring, backups, and production setup.

🚀 **Happy containerizing!**

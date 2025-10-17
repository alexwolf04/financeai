# Deployment Guide

## 🚀 Quick Deploy Options

### Option 1: Heroku (Easiest)
```bash
# Install Heroku CLI, then:
heroku create your-financeai-app
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
git push heroku main
```

### Option 2: Railway
```bash
# Connect your GitHub repo to Railway
# Set environment variables in Railway dashboard
# Deploy automatically on push
```

### Option 3: DigitalOcean App Platform
```bash
# Connect GitHub repo
# Configure environment variables
# Auto-deploy on push
```

## 🔧 Environment Variables for Production

```bash
# Required
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Optional
DEBUG=False
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
```

## 🐳 Docker Production Deployment

```bash
# 1. Create production environment file
cp .env.example .env.production

# 2. Generate secure secrets
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env.production
echo "DB_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(16))')" >> .env.production

# 3. Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🌐 Frontend Deployment

### Netlify/Vercel (Static)
```bash
# Build static version
npm run build  # if you add build tools later

# Deploy frontend folder to:
# - Netlify: Drag & drop frontend/ folder
# - Vercel: Connect GitHub repo, set build dir to frontend/
```

### Update API URL in Frontend
```javascript
// In frontend/index.html, change:
const API_BASE = 'https://your-api-domain.com';
```

## 📊 Database Setup

### PostgreSQL (Recommended for Production)
```sql
-- Create database and user
CREATE DATABASE financeai;
CREATE USER financeai WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE financeai TO financeai;
```

### Migration from SQLite
```bash
# Export from SQLite
sqlite3 financeai.db .dump > backup.sql

# Import to PostgreSQL
psql -U financeai -d financeai -f backup.sql
```

## 🔒 Security Checklist

- [ ] Change SECRET_KEY from default
- [ ] Use HTTPS in production
- [ ] Set proper CORS origins
- [ ] Use PostgreSQL for production
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Regular backups
- [ ] Update dependencies regularly

## 📈 Monitoring & Logging

### Add to your production setup:
```python
# In app/main.py
import logging
logging.basicConfig(level=logging.INFO)

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
    return response
```

## 🚨 Troubleshooting

### Common Issues:
1. **CORS Errors**: Update ALLOWED_ORIGINS in environment
2. **Database Connection**: Check DATABASE_URL format
3. **Rate Limiting**: Adjust limits for your traffic
4. **Memory Issues**: Increase container memory limits

### Health Check Endpoint:
```bash
curl https://your-domain.com/health
# Should return: {"status":"healthy","service":"FinanceAI"}
```

## 📱 Mobile-Friendly Frontend

The current frontend is responsive, but for a mobile app:
1. Consider React Native or Flutter
2. Use the same API endpoints
3. Add offline capabilities
4. Implement biometric authentication
# Security Policy

## Security Features

FinanceAI implements several security measures to protect user data:

### 🔒 Data Protection
- **Local Processing**: All ML models run locally - no data sent to external services
- **Input Sanitization**: All user inputs are validated and sanitized
- **SQL Injection Prevention**: Using SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Input validation and output encoding

### 🚦 Rate Limiting
- API endpoints are rate-limited to prevent abuse
- Default: 100 requests per minute per IP
- Configurable via environment variables

### 🔐 Authentication & Authorization
- User ID validation and format checking
- Transaction amount validation (max $1M)
- Description length limits (200 characters)

### 🌐 Network Security
- CORS properly configured for allowed origins
- Security headers added to all responses
- HTTPS recommended for production

### 📊 Data Privacy
- User IDs can be hashed for additional privacy
- No sensitive data logged
- Database encryption at rest (when using encrypted storage)

## Production Deployment Security

### Environment Variables
Never commit these to version control:
```bash
SECRET_KEY=your-super-secret-key-here
DB_PASSWORD=your-database-password
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Recommended Production Setup
1. Use PostgreSQL instead of SQLite
2. Enable HTTPS with SSL certificates
3. Use a reverse proxy (nginx) with rate limiting
4. Set up proper logging and monitoring
5. Regular security updates

### Security Headers
The application automatically adds:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

## Reporting Security Issues

If you discover a security vulnerability, please email: [your-email@domain.com]

**Please do not report security vulnerabilities through public GitHub issues.**

## Security Checklist for Deployment

- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting
- [ ] Enable database encryption
- [ ] Set up monitoring and logging
- [ ] Regular security updates
- [ ] Backup strategy in place
# Deployment Guide - Enhanced Lead Broker Platform

## 🚀 Quick Start

### Local Development
```bash
# Clone the repository
git clone https://github.com/Snaxxwax/enhanced-lead-broker.git
cd enhanced-lead-broker

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the application
python src/main.py
```

Visit `http://localhost:5000` to see the platform in action.

### Initialize Sample Data
```bash
# In a new terminal, initialize sample buyers
curl -X POST http://localhost:5000/api/init-buyers
```

## 🌐 Production Deployment Options

### Option 1: Heroku Deployment
```bash
# Install Heroku CLI and login
heroku login

# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key

# Deploy
git push heroku main

# Initialize sample data
heroku run python -c "
import requests
requests.post('https://your-app-name.herokuapp.com/api/init-buyers')
"
```

### Option 2: DigitalOcean App Platform
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set run command: `python src/main.py`
4. Set environment variables in the dashboard
5. Deploy

### Option 3: AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init

# Create environment and deploy
eb create production
eb deploy
```

### Option 4: Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "src/main.py"]
```

```bash
# Build and run
docker build -t enhanced-lead-broker .
docker run -p 5000:5000 enhanced-lead-broker
```

## ⚙️ Environment Configuration

### Required Environment Variables
```bash
# Production settings
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here

# Database (optional - uses SQLite by default)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# External APIs (optional)
GOOGLE_MAPS_API_KEY=your-google-maps-key
SENDGRID_API_KEY=your-sendgrid-key
```

### Optional Configuration
```bash
# Analytics
GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX
HOTJAR_ID=your-hotjar-id

# Lead Distribution
WEBHOOK_URL=https://your-crm.com/webhook
EMAIL_NOTIFICATIONS=true
```

## 🗄️ Database Setup

### SQLite (Default)
No additional setup required. Database file is created automatically.

### PostgreSQL (Recommended for Production)
```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Set DATABASE_URL environment variable
export DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### MySQL
```bash
# Install MySQL adapter
pip install PyMySQL

# Set DATABASE_URL
export DATABASE_URL=mysql+pymysql://user:pass@host:port/dbname
```

## 📊 Monitoring & Analytics

### Application Monitoring
- Health check endpoint: `/health`
- Metrics endpoint: `/api/analytics/metrics`
- Error logging to console/file

### Performance Monitoring
```python
# Add to your monitoring service
import time
from flask import request

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    # Log to your monitoring service
    return response
```

## 🔒 Security Considerations

### Production Security Checklist
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable security headers
- [ ] Regular dependency updates
- [ ] Database connection encryption
- [ ] Input validation and sanitization

### Security Headers
```python
from flask_talisman import Talisman

# Add to main.py
Talisman(app, force_https=True)
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Stateless application design
- External session storage (Redis)
- Database connection pooling

### Performance Optimization
- Enable gzip compression
- Use CDN for static assets
- Implement caching (Redis/Memcached)
- Database query optimization
- Async processing for heavy tasks

## 🔧 Maintenance

### Regular Tasks
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Database maintenance
python -c "
from src.models.lead import db
from src.main import app
with app.app_context():
    # Clean old analytics data
    db.session.execute('DELETE FROM form_analytics WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY)')
    db.session.commit()
"

# Log rotation
logrotate /etc/logrotate.d/enhanced-lead-broker
```

### Backup Strategy
```bash
# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Application backup
tar -czf app_backup_$(date +%Y%m%d).tar.gz /path/to/app
```

## 🚨 Troubleshooting

### Common Issues

**Issue: Application won't start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip check

# Check environment variables
env | grep FLASK
```

**Issue: Database connection errors**
```bash
# Test database connection
python -c "
from src.models.lead import db
from src.main import app
with app.app_context():
    try:
        db.create_all()
        print('Database connection successful')
    except Exception as e:
        print(f'Database error: {e}')
"
```

**Issue: Frontend not loading**
```bash
# Check static files
ls -la src/static/

# Rebuild frontend if needed
cd lead-broker-frontend
npm run build
cp -r dist/* ../enhanced_lead_broker/src/static/
```

### Debug Mode
```bash
# Enable debug mode (development only)
export FLASK_ENV=development
export FLASK_DEBUG=1
python src/main.py
```

## 📞 Support

For deployment issues:
1. Check the logs for error messages
2. Verify environment variables are set
3. Test database connectivity
4. Check firewall/security group settings
5. Review the troubleshooting section above

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: python -m pytest tests/
    
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "your-app-name"
        heroku_email: "your-email@example.com"
```

---

🎉 **Congratulations!** Your Enhanced Lead Broker Platform is now deployed and ready to generate high-converting leads!

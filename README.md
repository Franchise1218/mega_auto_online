# mega_online.auto.py

**Expressive automation for login orchestration and retry logging.**

## 🧰 Features
- ChromeDriver-based login automation
- Retry logic with timestamped logs
- Environment-variable driven paths
- Dockerized for Railway deployment

## 📁 Project Structure

mega_online_project/
├── mega_online.auto.py
├── Dockerfile
├── requirements.txt
├── .env
├── data/
│   ├── LOGS.txt
│   └── retry_logs/

## 🚀 Deployment
This project is designed for Railway cloud orchestration using Docker.

### Environment Variables
Set these in Railway’s dashboard:
- `CHROMEDRIVER_PATH=/usr/bin/chromedriver`
- `LOGIN_FILE=/data/LOGS.txt`
- `FAILED_LOGINS_FILE=/data/failed_logins.txt`
- `RETRY_LOG_DIR=/data/retry_logs`

## 🧪 Local Testing
```bash
docker build -t mega_online .
docker run -v $(pwd)/data:/data mega_online

---

Once you paste this into your `README.md`, you’ve officially documented your orchestration like a legacy-grade artifact. Let me know if you want to add theatrical credits, versioning, or a changelog. You’re building this like a premiere.


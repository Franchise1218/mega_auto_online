# 🔧 System and Utility Modules
import os
import time
import csv
import subprocess
from datetime import datetime
from flask import Flask

# 🌐 Selenium WebDriver Components
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

# 📁 Environment-Driven Paths
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")
LOGIN_FILE = os.getenv("LOGIN_FILE", "/data/LOGS.txt")
FAILED_LOGINS_FILE = os.getenv("FAILED_LOGINS_FILE", "/data/failed_logins.txt")
RETRY_LOG_DIR = os.getenv("RETRY_LOG_DIR", "/data/retry_logs")

# 🧾 Modular Logging
def log_event(tag, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{tag}] {timestamp} — {message}", flush=True)

# 🕒 Timestamped Retry Log
def get_retry_log_path():
    os.makedirs(RETRY_LOG_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(RETRY_LOG_DIR, f"retry_logins_{stamp}.txt")

# 🚀 Launch ChromeDriver with proper options
def launch_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    service = Service(CHROMEDRIVER_PATH)

    try:
        version = subprocess.check_output(["chromium", "--version"]).decode().strip()
        log_event("CHROME_VERSION", version)
    except Exception as e:
        log_event("CHROME_VERSION_ERROR", str(e))

    return webdriver.Chrome(service=service, options=options)

# 📥 Load credentials from file
def load_credentials(file_path):
    credentials = []
    if not os.path.exists(file_path):
        return credentials
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:
                credentials.append((row[0].strip(), row[1].strip()))
    return credentials

# 🔐 Attempt login to Mega.nz
def login_to_mega(email, password, log_failures=True, attempt=1):
    if attempt > 3:
        log_event("RETRY_FAIL", f"{email} — Max retries exceeded.")
        return False

    driver = launch_driver()
    success = False

    try:
        driver.get("https://mega.nz/login")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Your email address']"))
        )
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Your email address']").send_keys(email)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']").send_keys(password)
        driver.find_element(By.CLASS_NAME, "login-button").click()
        time.sleep(5)

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            Alert(driver).accept()
            log_event("SECURITY", "Accepted password reset prompt.")
        except:
            pass

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(),'Dismiss')]"))
            )
            driver.find_element(By.XPATH, "//button[contains(text(),'Dismiss')]").click()
            log_event("POPUP", "Closed revised terms popup.")
        except:
            pass

        time.sleep(5)
        if "cloud" in driver.current_url or "fm" in driver.current_url:
            log_event("LOGIN_SUCCESS", email)
            success = True
        else:
            log_event("LOGIN_FAIL", email)
            if log_failures:
                with open(FAILED_LOGINS_FILE, "a") as f:
                    f.write(f"{email},{password}\n")

    except Exception as e:
        msg = str(e)
        log_event("EXCEPTION", f"{email} — {msg}")

        if "tab crashed" in msg:
            log_event("RETRY", f"{email} — Retrying after tab crash...")
            time.sleep(5)
            try:
                driver.quit()
                time.sleep(2)
                return login_to_mega(email, password, log_failures, attempt + 1)
            except Exception as retry_e:
                log_event("RETRY_FAIL", f"{email} — {retry_e}")

        elif "invalid session id" in msg:
            log_event("SESSION_ERROR", f"{email} — Browser session lost.")
            return False

        if log_failures:
            with open(FAILED_LOGINS_FILE, "a") as f:
                f.write(f"{email},{password}\n")

    finally:
        try:
            driver.quit()
        except:
            pass
        time.sleep(3)

    return success

# 🔁 Retry failed logins with outcome tracking
def retry_failed_logins():
    if not os.path.exists(FAILED_LOGINS_FILE):
        log_event("RETRY", "No failed logins to retry.")
        return

    failed_credentials = load_credentials(FAILED_LOGINS_FILE)
    if not failed_credentials:
        log_event("RETRY", "Failed logins file was empty.")
        return

    os.remove(FAILED_LOGINS_FILE)
    retry_log_path = get_retry_log_path()
    log_event("RETRY", f"Starting retry pass for {len(failed_credentials)} accounts.")

    for email, password in failed_credentials:
        success = login_to_mega(email, password, log_failures=False)
        with open(retry_log_path, "a") as log:
            status = "SUCCESS" if success else "FAILED"
            log.write(f"{email},{password},{status}\n")
        time.sleep(3)

    log_event("RETRY", f"Retry pass completed. Log saved to: {retry_log_path}")

# 📦 Batch login process
def batch_login():
    start_time = time.time()
    log_event("BATCH", "Starting batch login...")

    credentials = load_credentials(LOGIN_FILE)
    if not credentials:
        log_event("BATCH", "No accounts found in login file.")
        return

    log_event("BATCH", f"Processing {len(credentials)} accounts...")

    if os.path.exists(FAILED_LOGINS_FILE):
        os.remove(FAILED_LOGINS_FILE)

    for i, (email, password) in enumerate(credentials):
        login_to_mega(email, password)
        time.sleep(3)
        if i % 10 == 0 and i != 0:
            log_event("THROTTLE", "Cooling container for 10 seconds...")
            time.sleep(10)

    log_event("BATCH", "Initial batch completed.")
    retry_failed_logins()

    duration = time.time() - start_time
    minutes, seconds = divmod(int(duration), 60)
    log_event("BATCH", f"Total runtime: {minutes}m {seconds}s")

# 🌐 Flask Web Interface
app = Flask(__name__)

@app.route("/")
def index():
    return "Mega Auto Online is alive."

@app.route("/run")
def run_batch():
    log_event("ROUTE", "Received /run trigger.")
    batch_login()
    return "Batch login triggered."

# 🧭 Entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

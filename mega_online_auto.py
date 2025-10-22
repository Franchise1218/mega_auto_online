import os
import time
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime

app = Flask(__name__)

CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
LOG_FILE = os.getenv("LOGIN_FILE", "LOGS.txt")
FAILED_LOGINS_FILE = os.getenv("FAILED_LOGINS_FILE", "failed_logins.txt")
RETRY_LOG_DIR = os.getenv("RETRY_LOG_DIR", "retry_logs")
RESULT_LOG_FILE = "login_results.txt"

def login_account(username, password, driver):
    try:
        driver.get("https://mega.nz/login")
        time.sleep(2)  # Let the page load

        # Fill in email
        email_input = driver.find_element(By.ID, "login-name2")
        email_input.clear()
        email_input.send_keys(username)

        # Fill in password
        password_input = driver.find_element(By.ID, "login-password2")
        password_input.clear()
        password_input.send_keys(password)

        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, ".login-button")
        login_button.click()

        time.sleep(5)  # Wait for redirect or error

        # Check for success: redirected to file manager
        if "fm" in driver.current_url:
            return True
        else:
            return False

    except Exception as e:
        print(f"Exception for {username}: {e}")
        return False

def run_login_batch():
    start_time = time.time()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    failed_accounts = []
    processed = 0
    succeeded = 0
    failed = 0

    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line:
                    continue
                username, password = line.split(",", 1)
                print(f"Attempting login for {username}")
                success = login_account(username, password, driver)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                processed += 1

                with open(RESULT_LOG_FILE, "a") as result_log:
                    if success:
                        result_log.write(f"[{timestamp}] Login succeeded for {username}\n")
                        succeeded += 1
                    else:
                        result_log.write(f"[{timestamp}] Login failed for {username}\n")
                        with open(FAILED_LOGINS_FILE, "a") as fail_log:
                            fail_log.write(f"[{timestamp}] Login failed for {username}\n")
                        failed_accounts.append((username, password))
                        failed += 1

    finally:
        driver.quit()

    print(f"Processed {processed} accounts: {succeeded} succeeded, {failed} failed.")
    print(f"Runtime: {round(time.time() - start_time, 2)} seconds")

    if failed_accounts:
        retry_failed_logins(failed_accounts)

def retry_failed_logins(failed_accounts):
    print("Starting retry phase...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        for username, password in failed_accounts:
            print(f"Retrying login for {username}")
            success = login_account(username, password, driver)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            retry_log_path = os.path.join(RETRY_LOG_DIR, f"{username.replace('@', '_at_')}.txt")
            with open(retry_log_path, "a") as retry_log:
                if success:
                    retry_log.write(f"[{timestamp}] Retry succeeded for {username}\n")
                else:
                    retry_log.write(f"[{timestamp}] Retry failed for {username}\n")
    finally:
        driver.quit()

@app.route("/run", methods=["GET"])
def trigger_run():
    run_login_batch()
    return "Batch login orchestration triggered."

if __name__ == "__main__":
    run_login_batch()

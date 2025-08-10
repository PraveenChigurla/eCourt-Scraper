from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from anticaptchaofficial.imagecaptcha import imagecaptcha
from fastapi import HTTPException
import time
import requests
import os
import psycopg2
from psycopg2.extras import execute_values
from selenium.common.exceptions import TimeoutException

def solve_captcha(captcha_file):
    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key(os.getenv("ANTICAPTCHA_API_KEY", "436ac223d604333b3c0c7faf444d9232"))
    solver.set_soft_id(0)
    print(f"Attempting to solve CAPTCHA from: {os.path.abspath(captcha_file)}")
    result = solver.solve_and_return_solution(captcha_file)
    if result != 0:
        print(f"CAPTCHA Solved: {result}")
        return result
    else:
        print(f"AntiCaptcha Error Code: {solver.error_code}")
        raise HTTPException(status_code=500, detail="Failed to solve CAPTCHA. Please try again later, as the verification process encountered an issue.")

def log_to_postgres(case_type, case_number, filing_year, raw_response):
    conn = psycopg2.connect("postgresql://postgres:vagrant@localhost:5432/court_db")
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id SERIAL PRIMARY KEY,
                case_type VARCHAR(50),
                case_number VARCHAR(50),
                filing_year VARCHAR(4),
                raw_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            INSERT INTO queries (case_type, case_number, filing_year, raw_response)
            VALUES (%s, %s, %s, %s)
        """, (case_type, case_number, filing_year, raw_response))
        conn.commit()
    except Exception as e:
        print(f"Database error: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def scrape_case_details(case_type: str, case_number: str, filing_year: str):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--force-device-scale-factor=0.75")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("Opening website: https://karimnagar.dcourts.gov.in/")
        driver.get("https://karimnagar.dcourts.gov.in/")

        # Check if site is accessible
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Services')]"))
        )

        print("Navigating to Services...")
        services_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Services')]"))
        )
        services_link.click()

        print("Navigating to Case Status...")
        case_status_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Case Status')]"))
        )
        case_status_link.click()

        print("Selecting Case Number search option...")
        search_by_case_number = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Case Number')]"))
        )
        search_by_case_number.click()

        print("Selecting Court Complex: Karimnagar, PDJ Court Complex...")
        court_dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='est_code']"))
        )
        Select(court_dropdown).select_by_visible_text("Karimnagar, PDJ Court Complex")
        time.sleep(2)

        driver.switch_to.default_content()
        try:
            iframe = driver.find_element(By.TAG_NAME, "iframe")
            driver.switch_to.frame(iframe)
            print("Switched to iframe")
        except:
            print("No iframe found, continuing in main content")

        print(f"Selecting Case Type: {case_type}")
        case_type_dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "case_type"))
        )
        select = Select(case_type_dropdown)
        try:
            select.select_by_visible_text(case_type)
        except:
            select.select_by_index(0)
            print(f"Case type '{case_type}' not found, selected first available case type")
            raise HTTPException(status_code=400, detail=f"Invalid case type: {case_type}. Please check and try again.")

        print(f"Filling Case Number: {case_number}")
        case_number_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "reg_no"))
        )
        case_number_input.clear()
        case_number_input.send_keys(case_number)

        print(f"Filling Filing Year: {filing_year}")
        year_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "reg_year"))
        )
        year_input.clear()
        year_input.send_keys(filing_year)

        print("Handling CAPTCHA with AntiCaptcha...")
        captcha_img = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "siwp_captcha_image_0"))
        )
        captcha_src = captcha_img.get_attribute("src")
        print(f"Found CAPTCHA image with src: {captcha_src}")
        
        captcha_response = requests.get(captcha_src, timeout=10)
        captcha_response.raise_for_status()
        captcha_file = "captcha.png"
        with open(captcha_file, "wb") as f:
            f.write(captcha_response.content)
        print(f"Captcha image saved at: {os.path.abspath(captcha_file)}")

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                captcha_text = solve_captcha(captcha_file)
                break
            except HTTPException as e:
                if attempt < max_attempts - 1:
                    time.sleep(5)
                else:
                    raise e

        try:
            captcha_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "siwp_captcha_value_0"))
            )
            print("Found CAPTCHA input with ID: siwp_captcha_value_0")
        except:
            captcha_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@name, 'siwp_captcha_value')]"))
            )
            print("Fallback CAPTCHA input with name-based locator")
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)

        try:
            search_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Search']"))
            )
            print("Found Search button using precise input[type=submit][value=Search] locator")
        except:
            search_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Search']"))
            )
            print("Fallback Search button with value='Search'")
        search_button.click()
        print("Search button clicked, waiting for results...")

        print("Clicking View button...")
        view_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'View')]"))
        )
        view_button.click()

        print("Waiting for View page to load...")
        # Wait for specific table captions to ensure content is loaded
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//table[caption='Case Details']"))
        )
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//table[caption='Case Status']"))
        )

        print("Extracting full content of View page...")
        # Capture rendered HTML with execute_script
        raw_response = driver.execute_script("return document.documentElement.outerHTML")
        # Remove footer section
        footer_start = raw_response.find('<footer id="mainFooter">')
        if footer_start != -1:
            footer_end = raw_response.find('</footer>', footer_start) + len('</footer>')
            raw_response = raw_response[:footer_start] + raw_response[footer_end:]
        # Remove "Back" buttons
        back_button_pattern = '<button data-action="backCaseList" class="viewCnrDetailsBack btn accent-color" aria-label="Back to previous view" data-back-id='
        start_pos = 0
        while True:
            back_start = raw_response.find(back_button_pattern, start_pos)
            if back_start == -1:
                break
            back_end = raw_response.find('>', back_start) + 1
            back_end = raw_response.find('</button>', back_end) + len('</button>')
            raw_response = raw_response[:back_start] + raw_response[back_end:]
            start_pos = back_start
        # Log to PostgreSQL
        log_to_postgres(case_type, case_number, filing_year, raw_response)
        return {"raw_response": raw_response}

    except TimeoutException:
        raise HTTPException(status_code=503, detail="The website is currently unavailable. Please try again later due to possible site downtime.")
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="The website is not responding. Please try again later due to a connection issue.")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Scraping error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again later.")
    finally:
        print("Closing browser...")
        driver.quit()
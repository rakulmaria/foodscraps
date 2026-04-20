import logging
from functools import partial
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from timer import function_timer
from webdriver_manager.chrome import ChromeDriverManager

function_timer = partial(function_timer, decimals=5)

# --- logger
logger = logging.getLogger(__name__)


URLS = [
    "https://maps.google.com/?cid=8601378606469356674&g_mp=Cilnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaE5lYXJieRACGAQgAA",
    "https://maps.google.com/?cid=8601378606469356674&g_mp=Cilnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaE5lYXJieRACGAQgAA",
    "https://maps.google.com/?cid=6381314399950946465&g_mp=Cilnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaE5lYXJieRACGAQgAA",
    "https://maps.google.com/?cid=10470528932399577074&g_mp=Cilnb29nbGUubWFwcy5wbGFjZXMudjEuUGxhY2VzLlNlYXJjaE5lYXJieRACGAQgAA"
]

def has_menu(driver, url, i, timeout=2):
    driver.get(url)
    
    # only on first entry
    if i == 0:
        # Handle cookie consent popup
        try:
            decline_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Reject all') or contains(., 'Decline all')]"))
            )
            decline_button.click()
            # Wait for popup to disappear
            WebDriverWait(driver, 3).until(
                EC.invisibility_of_element(decline_button)
            )
        except:
            pass  # No cookie popup appeared, continue normally

    # Wait for sidebar to load
    # try:
    #     WebDriverWait(driver, timeout).until(
    #         EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Information']"))
    #     )
    # except:
    #     pass
    time.sleep(1)
    # Check for menu element
    try:
        menu_elements = driver.find_elements(By.XPATH, "//*[text()='Menu']")
        return len(menu_elements) > 0
    except:
        return False

def setup_driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def main():
    driver = setup_driver()
    for i in range(len(URLS)):
        result = has_menu(driver, URLS[i], i=i)
        print(result)  # True or False

if __name__ == "__main__":
    main()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os

TIMEOUT = 60

class WebDriverManager:
    def __init__(self):
        self.driver = None

    def start_driver(self, headless=True):
        if self.driver:
            return self.driver

        options = Options()

        # Obligatoire sur Streamlit Cloud
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # Anti-détection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Chemin chromedriver sur Streamlit Cloud (Debian)
        chromedriver_path = "/usr/bin/chromedriver"
        if os.path.exists(chromedriver_path):
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            # Fallback local (dev)
            self.driver = webdriver.Chrome(options=options)

        self.driver.implicitly_wait(TIMEOUT)
        return self.driver

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

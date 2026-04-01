from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import platform

TIMEOUT = 60

class WebDriverManager:
    def __init__(self):
        self.driver = None

    def start_driver(self, headless=True):
        if self.driver:
            return self.driver

        on_cloud = "STREAMLIT_SERVER" in os.environ

        if on_cloud:
            # Chrome headless pour Streamlit Cloud
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")

            self.driver = webdriver.Chrome(options=options)

        else:
            # Edge local sur Windows
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.edge.service import Service

            options = EdgeOptions()
            options.use_chromium = True
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-blink-features=AutomationControlled")
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--window-size=1920,1080")

            service = Service("C:/Users/COSTA/MonApplication/msedgedriver.exe")
            self.driver = webdriver.Edge(service=service, options=options)

        self.driver.implicitly_wait(TIMEOUT)
        return self.driver

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import subprocess
import os

TIMEOUT = 60

class WebDriverManager:
    def __init__(self):
        self.driver = None

    def _get_chrome_options(self, headless=True):
        options = Options()

        # === Obligatoire pour Streamlit Cloud ===
        options.add_argument("--headless=new")          # Toujours headless sur cloud
        options.add_argument("--no-sandbox")            # Requis sur Linux/cloud
        options.add_argument("--disable-dev-shm-usage") # Évite les crashes mémoire
        options.add_argument("--disable-gpu")           # Pas de GPU sur cloud

        # === Optionnel mais recommandé ===
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        return options

    def _find_chromedriver(self):
        """Trouve chromedriver automatiquement selon l'environnement."""
        # Streamlit Cloud (Debian/Ubuntu)
        common_paths = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path

        # Fallback : laisser Selenium le trouver via le PATH
        return None

    def start_driver(self, headless=True):
        if self.driver:
            return self.driver

        options = self._get_chrome_options(headless)
        chromedriver_path = self._find_chromedriver()

        if chromedriver_path:
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        self.driver.implicitly_wait(TIMEOUT)
        return self.driver

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

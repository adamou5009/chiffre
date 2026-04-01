from selenium import webdriver
from selenium.webdriver.edge.options import Options

TIMEOUT = 60

class WebDriverManager:
    def __init__(self):
        self.driver = None

    def start_driver(self, headless=True):
        if self.driver:
            return self.driver

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")

        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Edge(options=options)
        self.driver.implicitly_wait(TIMEOUT)
        return self.driver

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

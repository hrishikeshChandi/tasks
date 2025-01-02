import os
import datetime as dt
from urllib.parse import urlparse
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions

# pip install -r requirements.txt: This command must be executed in the terminal or command prompt to install all the required Python packages listed in the requirements.txt file.


app = Flask(__name__)


def create_screenshots_folder():
    """Create a folder for storing screenshots if it doesn't exist."""
    if not os.path.exists("screenshots"):
        os.mkdir("screenshots")  # create folder


def get_driver():
    """Set up and return a headless Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())  # manage ChromeDriver
    return webdriver.Chrome(service=service, options=chrome_options)


def get_host(url):
    """Return the hostname of a URL."""
    return urlparse(url).hostname  # extract hostname


def create_folder(host):
    """Create a folder for each hostname if it does not exist."""
    if not os.path.exists(f"./screenshots/{host}/"):
        os.mkdir(f"./screenshots/{host}/")  # create hostname folder


def get_screenshot(links, driver):
    """Take screenshots of the provided URLs."""
    create_screenshots_folder()
    # If the 'screenshots' folder is deleted during processing, the program will fail, even if the URLs are valid, because the location for storing screenshots no longer exists.
    results = []  # store success/failure for each URL
    for url, i in zip(links, range(len(links))):
        try:
            driver.get(url)  # load URL
            WebDriverWait(driver, 10).until(  # wait for page to load
                expected_conditions.presence_of_element_located((By.TAG_NAME, "body"))
            )
            host = get_host(url)  # extract hostname
            create_folder(host)  # create folder for hostname
            current_date_time = dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S-%f")
            driver.save_screenshot(
                f"./screenshots/{host}/url_{current_date_time}.png"
            )  # save screenshot
            print(f"{i + 1}. success {current_date_time}")
            results.append("success")
        except Exception as e:
            print(f"{i + 1}. failed: {str(e)}")
            results.append("failed")

    return results


@app.route("/")
def home():
    """Render the home page."""
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    """Handle form submission and trigger screenshot capture."""
    links = request.form.get("links").split()  # accessing URLs from the form input
    driver = get_driver()  # initialize driver
    try:
        results = get_screenshot(links, driver)  # take screenshots
        print("process completed")
        return render_template(
            "index.html", results=results
        )  # return results to the frontend
    finally:
        driver.quit()  # close driver


if __name__ == "__main__":
    app.run(host="localhost", port=3000)

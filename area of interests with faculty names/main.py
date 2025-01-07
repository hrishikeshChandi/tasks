import time
from pymongo import MongoClient
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager

# pip install -r requirements.txt

client = MongoClient("mongodb://localhost:27017/")
db = client["college_details"]
faculty_collections = db["faculty"]
area_collections = db["area_of_interest"]

app = Flask(__name__)


def get_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


choose_department = {
    "aerospace": "aerospace",
    "architecture": "architecture",
    "aids": "ai_ds",
    "aiml": "ai_ml",
    "cse": "cse",
    "ise": "ise",
    "biotech": "biotechnology",
    "me": "me",
    "chemical": "chemical-engineering",
    "chemistry": "chemistry",
    "civil": "civil-engineering",
    "cse aiml": "cse_ai_ml",
    "cyber": "cse_cs",
    "eie": "eie",
    "eee": "eee",
    "ece": "ece",
    "humanities": "humanities",
    "iem": "iem",
    "maths": "maths",
    "mba": "mba",
    "mca": "mca",
    "medical electronics": "medical-engineering",
    "physics": "physics",
    "ete": "te",
}

areas_input = None


def area_of_interests(dept):
    details = area_collections.find_one({"dept": choose_department.get(dept)})
    if details and details["areas"]:
        if len(details["areas"]) > 0:
            print("Data found in DB")
            return details["areas"]
        else:
            area_collections.delete_one({"dept": choose_department[dept]})
    driver = get_driver()
    try:
        print("No data found in DB, scraping data...")
        url = f"https://msrit.edu/department/faculty.html?dept={choose_department[dept]}.html#start"
        driver.get(url)
        names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
        area_of_interest = []

        for name in names:
            try:
                name.click()
                time.sleep(2)
                div = driver.find_element(By.CSS_SELECTOR, ".table-responsive")
                areas = div.find_elements(By.CSS_SELECTOR, ".course-title")

                for area in areas:
                    if area.text and area.text not in area_of_interest:
                        area_of_interest.append(area.text)
                        print(f"Added area: {area.text}")
                driver.back()
                names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
            except NoSuchElementException:
                driver.back()
            except StaleElementReferenceException:
                names = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".inner header a")
                    )
                )
            except Exception as e:
                print(f"Error while scraping faculty area: {e}")

        if area_of_interest:
            area_of_interest.sort()
            area_collections.insert_one(
                {"dept": choose_department[dept], "areas": area_of_interest}
            )
            print("Data has been stored in DB")
            driver.quit()
            return area_of_interest
        else:
            print("No areas of interest found during scraping.")
            return []
    finally:
        driver.quit()


def faculty_names(dept, input_area_of_interest):
    details = faculty_collections.find_one(
        {"dept": choose_department[dept], "area": input_area_of_interest}
    )
    if details:
        if len(details["names"]) > 0:
            print("Data found in DB")
            return details["names"]
        else:
            faculty_collections.delete_one(
                {"dept": choose_department[dept], "area": input_area_of_interest}
            )
    driver = get_driver()
    try:
        print("Finding names...")
        url = f"https://msrit.edu/department/faculty.html?dept={choose_department[dept]}.html#start"
        driver.get(url)
        names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
        faculties = []

        for name in names:
            try:
                faculty_name = name.text
                name.click()
                time.sleep(2)
                div = driver.find_element(By.CSS_SELECTOR, ".table-responsive")
                areas = div.find_elements(By.CSS_SELECTOR, ".course-title")
                area_of_interest = [area.text for area in areas if area.text]

                if input_area_of_interest in area_of_interest:
                    faculties.append(faculty_name)
                    print(faculty_name)
                driver.back()
                names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
            except NoSuchElementException:
                driver.back()
            except StaleElementReferenceException:
                names = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".inner header a")
                    )
                )
            except Exception as e:
                print(f"Error while processing faculty: {e}")

        if faculties:
            faculty_collections.insert_one(
                {
                    "dept": choose_department[dept],
                    "area": input_area_of_interest,
                    "names": faculties,
                }
            )
            print("Data has been stored in DB")
            driver.quit()
            return faculties
        else:
            print("No faculty found for the given area of interest.")
            return []
    finally:
        driver.quit()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search_dept", methods=["POST"])
def search_dept():
    dept = request.form.get("dept").lower()
    global areas_input
    areas_input = area_of_interests(dept)
    areas_input.sort()

    return render_template("index.html", areas=areas_input, dept=dept)


@app.route("/submit", methods=["POST"])
def submit():
    dept = request.form.get("dept").lower()
    input_area = request.form.get("domains")
    results = faculty_names(dept, input_area)
    return render_template(
        "index.html",
        results=results,
        areas=areas_input,
        dept=dept,
        user_interest=input_area,
    )


if __name__ == "__main__":
    try:
        app.run(debug=True, port=1500)
    finally:
        client.close()

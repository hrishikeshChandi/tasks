import random
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
    NoSuchElementException,
    StaleElementReferenceException,
)

from selenium.webdriver.common.action_chains import ActionChains

# from webdriver_manager.chrome import ChromeDriverManager

client = MongoClient("mongodb://localhost:27017/")

db = client["college_details"]
faculty_collections = db["faculty"]
area_collections = db["area_of_interest"]

app = Flask(__name__)

chrome_options = Options()
# chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=360,640")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")


service = Service(r"C:\webdrivers\chromedriver-win64\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)
action = ActionChains(driver)

key = random.randint(1, 6)
print(f"key : {key}")


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

available_departments = list(choose_department.keys())
available_departments.sort()
areas_input = None


def find_areas(dept, is_update):
    url = f"https://msrit.edu/department/faculty.html?dept={choose_department[dept]}.html#start"
    driver.get(url)
    # time.sleep(5)
    names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
    # print("starting")
    area_of_interest = []

    for name in names:
        try:
            action.move_to_element(name).click().perform()
            # name.click()
            # time.sleep(2)
            div = driver.find_element(By.CSS_SELECTOR, ".table-responsive")
            areas = div.find_elements(By.CSS_SELECTOR, ".course-title")

            for area in areas:
                if area.text and area.text not in area_of_interest:
                    area_of_interest.append(area.text)
                    print(f"Added area: {area.text}")
            driver.back()
            names = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".inner header a")
                )
            )

        except NoSuchElementException:
            driver.back()

        except StaleElementReferenceException:
            time.sleep(2)
            names = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".inner header a")
                )
            )

        except Exception as e:
            print(f"Error while scraping faculty area: {e}")

    if area_of_interest:
        area_of_interest.sort()

        if not is_update:
            area_collections.insert_one(
                {
                    "dept": choose_department[dept],
                    "areas": area_of_interest,
                }
            )

        print("Data has been stored in DB")
        return area_of_interest

    else:
        print("No areas of interest found during scraping.")
        return []


def area_of_interests(dept):
    areas_key = random.randint(1, 6)
    print(f"areas key : {areas_key}")

    details = area_collections.find_one({"dept": choose_department.get(dept)})

    if details and details["areas"]:
        if areas_key == key:
            print("updating area of interest")
            results = find_areas(dept=dept, is_update=True)

            if results:
                modified_data = area_collections.update_one(
                    {"dept": choose_department.get(dept)}, {"$set": {"areas": results}}
                )
                if modified_data.modified_count == 1:
                    print("data is updated")
                else:
                    print("no changes")

            return results
        else:
            if len(details["areas"]) > 0:
                print("Data found in DB")
                return details["areas"]

            else:
                area_collections.delete_one({"dept": choose_department[dept]})

    print("No data found in DB, scraping data...")
    return find_areas(dept=dept, is_update=False)


def find_faculties(dept, input_area_of_interest, is_update):
    url = f"https://msrit.edu/department/faculty.html?dept={choose_department[dept]}.html#start"
    driver.get(url)
    # time.sleep(5)
    names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
    faculties = []

    for name in names:
        try:
            faculty_name = name.text
            action.move_to_element(name).click().perform()
            # name.click()
            div = driver.find_element(By.CSS_SELECTOR, ".table-responsive")
            areas = div.find_elements(By.CSS_SELECTOR, ".course-title")
            area_of_interest = [area.text for area in areas if area.text]

            if input_area_of_interest in area_of_interest:
                faculties.append(faculty_name.title())
                print(faculty_name)
            driver.back()
            names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")

        except NoSuchElementException:
            driver.back()

        except StaleElementReferenceException:
            time.sleep(2)
            names = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".inner header a")
                )
            )

        except Exception as e:
            print(f"Error while processing faculty: {e}")

    if faculties:
        if not is_update:
            faculty_collections.insert_one(
                {
                    "dept": choose_department[dept],
                    "area": input_area_of_interest,
                    "names": faculties,
                }
            )
        print("Data has been stored in DB")
        return faculties
    else:
        print("No faculty found for the given area of interest.")
        return []


def faculty_names(dept, input_area_of_interest):
    faculties_key = random.randint(1, 6)
    print(f"faculty key : {faculties_key}")

    details = faculty_collections.find_one(
        {
            "dept": choose_department[dept],
            "area": input_area_of_interest,
        }
    )

    if details:
        if faculties_key == key:
            print("Finding names for updating existing data..")
            results = find_faculties(
                dept=dept, input_area_of_interest=input_area_of_interest, is_update=True
            )

            if results:
                modified_data = faculty_collections.update_one(
                    {
                        "dept": choose_department.get(dept),
                        "area": input_area_of_interest,
                    },
                    {"$set": {"names": results}},
                )
                if modified_data.modified_count == 1:
                    print("data is updated")
                else:
                    print("no changes")
                return results
        else:
            if len(details["names"]) > 0:
                print("Data found in DB")
                return details["names"]

            else:
                faculty_collections.delete_one(
                    {
                        "dept": choose_department[dept],
                        "area": input_area_of_interest,
                    }
                )

    print("Finding names...")
    return find_faculties(
        dept=dept, input_area_of_interest=input_area_of_interest, is_update=False
    )


@app.route("/")
def home():
    return render_template("index.html", available_dept_s=available_departments)


@app.route("/search_dept", methods=["POST"])
def search_dept():
    dept = request.form.get("dept_s")
    # print(dept, type(dept))
    global areas_input
    areas_input = area_of_interests(dept)
    areas_input.sort()

    return render_template(
        "index.html",
        available_dept_s=available_departments,
        areas=areas_input,
        dept=dept,
    )


@app.route("/submit", methods=["POST"])
def submit():
    dept = request.form.get("dept_s")
    input_area = request.form.get("domains")
    results = faculty_names(dept, input_area)
    results.sort()
    return render_template(
        "index.html",
        available_dept_s=available_departments,
        results=results,
        areas=areas_input,
        dept=dept,
        user_interest=input_area,
    )


if __name__ == "__main__":
    try:
        app.run(port=5000)
    finally:
        client.close()
        driver.quit()

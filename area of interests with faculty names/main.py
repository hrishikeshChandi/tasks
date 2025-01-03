import time
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector

# pip install -r requirements.txt

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="abcd",
    database="college_details",
)

cursor = connection.cursor()

app = Flask(__name__)

chrome_options = Options()
# chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

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
    try:
        cursor.execute(
            "SELECT * FROM area_of_interests WHERE dept=%s", (choose_department[dept],)
        )
        details = cursor.fetchone()

        if details and len(details[2]) > 0:
            print("Data found in DB")
            return details[2].split(",")

        print("No data found in DB, scraping data...")
        url = f"https://msrit.edu/department/faculty.html?dept={choose_department[dept]}.html#start"
        driver.get(url)
        names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
        area_of_interest = []

        for name in names:
            try:
                name.click()
                div = driver.find_element(By.CSS_SELECTOR, ".table-responsive")
                areas = div.find_elements(By.CSS_SELECTOR, ".course-title")
                for area in areas:
                    if area.text != "" and area.text not in area_of_interest:
                        area_of_interest.append(area.text)
                        print(f"Added area: {area.text}")
                driver.back()
                names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
            except Exception as e:
                print(f"Error while scraping faculty area: {e}")

        if area_of_interest:
            area_of_interest.sort()
            list_areas = area_of_interest
            final_areas = ",".join(area_of_interest)
            cursor.execute(
                "INSERT INTO area_of_interests(dept, areas) VALUES(%s, %s)",
                (choose_department[dept], final_areas),
            )
            connection.commit()
            print("Data has been stored in DB")
            return list_areas
        else:
            print("No areas of interest found during scraping.")
            return []

    except Exception as e:
        print(f"Error in area_of_interests: {e}")
        return []


def faculty_names(dept, input_area_of_interest):
    try:
        cursor.execute(
            "SELECT * FROM faculty WHERE dept=%s AND area=%s",
            (choose_department[dept], input_area_of_interest),
        )
        details = cursor.fetchone()
        if details and len(details[3]) > 0:
            print("Data found in DB")
            return details[3].split(",")
    except Exception as e:
        print(f"Error fetching faculty data from DB: {e}")

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
                # time.sleep(2)
                div = driver.find_element(By.CSS_SELECTOR, ".table-responsive")
                areas = div.find_elements(By.CSS_SELECTOR, ".course-title")
                area_of_interest = [area.text for area in areas if area.text != ""]
                if input_area_of_interest in area_of_interest:
                    faculties.append(faculty_name)
                    print(faculty_name)
                driver.back()
                names = driver.find_elements(By.CSS_SELECTOR, ".inner header a")
            except Exception as e:
                print(f"Error while processing faculty: {e}")

        if faculties:
            list_faculties = faculties
            string_faculties = ",".join(faculties)
            cursor.execute(
                "INSERT INTO faculty(dept, area, names) VALUES(%s, %s, %s)",
                (choose_department[dept], input_area_of_interest, string_faculties),
            )
            connection.commit()
            print("Data has been stored in DB")
            return list_faculties
        else:
            print("No faculty found for the given area of interest.")
            return []
    except Exception as e:
        print(f"Error in faculty names processing: {e}")
        return []


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
    app.run(debug=True, port=1500)

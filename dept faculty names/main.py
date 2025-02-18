from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import json

app = Flask(__name__)

# pip install -r requirements.txt

chrome_options = Options()
chrome_options.add_argument("--headless")

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


def get_faculty_names(dept):
    try:
        driver.get(
            f"https://www.msrit.edu/department/faculty.html?dept={choose_department[dept]}.html#start"
        )
        print("success (selenium)")
        names = driver.find_elements(By.CSS_SELECTOR, value=".inner header a")
        if len(names) > 0:
            faculty_names = [name.text for name in names]
            return faculty_names
        else:
            get_faculty_names(dept)
    except KeyError:
        return f"{dept} not found"


def search_json(dept):
    try:
        with open("data.json", "r") as file:
            data = json.load(file)
            if dept in data:
                if len(data[dept]) > 0:
                    print("success (json)")
                    return data[dept]
                else:
                    del data[dept]
                    with open("data.json", "w") as file:
                        json.dump(data, file, indent=4)
    except json.JSONDecodeError:
        data = {}
    except FileNotFoundError:
        with open("data.json", "w") as file:
            pass
        data = {}
    response = get_faculty_names(dept)
    if not isinstance(response, str):
        faculty = {dept: response}
        data.update(faculty)
        with open("data.json", "w") as file:
            json.dump(data, file, indent=4)

        return data[dept]
    else:
        return response


@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    department = request.form["dept"].lower()
    result = search_json(department)
    return render_template("index.html", department=department, faculty_names=result)


if __name__ == "__main__":
    app.run(port=8000)

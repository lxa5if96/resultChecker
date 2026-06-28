from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
app = Flask(__name__)
def get_nepali_year():
    now = datetime.now()
    gregorian_year = now.year
    gregorian_month = now.month
    gregorian_day = now.day
    if gregorian_month < 4 or (gregorian_month == 4 and gregorian_day < 14):
        return gregorian_year + 56
    else:
        return gregorian_year + 57

@app.route("/")
def home():
    nepali_year = get_nepali_year()
    return render_template("index.html",year = nepali_year)

@app.route("/result", methods=["POST"])
def result():

    symbol = request.form.get("symbol_number")
    dob = request.form.get("dob")

    payload = {
        "symbol": symbol,
        "dob": dob,
        "submit": "Submit"
    }

    try:
        response = requests.post(
        "https://neb.ntc.net.np/results.php",
        data=payload,
        timeout=15
    )
    except requests.exceptions.RequestException:
        return "NEB server is unavailable. Please try again later."

    html = response.text
    print("FORM:", request.form)
    print("SYMBOL:", symbol)
    print("DOB:", dob)
    print("STATUS:", response.status_code)
    print(html[:1000])

    import re

    name = re.search(
        r"<b>Name</b>\s*:\s*(.*?)<br>",
        html,
        re.DOTALL
    )

    symbol_match = re.search(
        r"<b>Symbol</b>\s*:\s*(\d+)",
        html
    )

    school = re.search(
        r"<b>School Name</b>\s*:\s*(.*?)<br><br>",
        html,
        re.DOTALL
    )

    gpa = re.search(
        r"GPA\s*:\s*</td><td><b>(.*?)</b>",
        html
    )

    registration = re.search(
        r"<b>Registration No</b>\s*:\s*(\d+)",
        html
    )

    if not all([name, symbol_match, school, gpa]):
        print("NAME:", name)
        print("SYMBOL_MATCH:", symbol_match)
        print("SCHOOL:", school)
        print("GPA:", gpa)
        return "Result not found or invalid symbol/DOB"

    student_name = name.group(1).strip()
    student_symbol = symbol_match.group(1)
    student_school = school.group(1).strip()
    student_gpa = gpa.group(1)

    student_registration = (
        registration.group(1)
        if registration
        else "N/A"
    )

    soup = BeautifulSoup(html, "html.parser")

    subjects = []

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) == 5:

            code = cols[0].get_text(strip=True)
            subject = cols[1].get_text(strip=True)
            credit = cols[2].get_text(strip=True)
            grade = cols[3].get_text(strip=True)


            if code.isdigit():

                subjects.append({
                    "code": code,
                    "name": subject,
                    "credit": credit,
                    "grade": grade
                })

    return render_template(
    "result.html",
    name=student_name,
    symbol=student_symbol,
    registration=student_registration,
    school=student_school,
    gpa=student_gpa,
    subjects=subjects
)  

if __name__ == "__main__":
    app.run(debug=True)
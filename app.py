from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/result", methods=["POST"])
def result():

    symbol = request.form.get("symbol")
    dob = request.form.get("dob")

    payload = {
        "symbol": symbol,
        "dob": dob,
        "submit": "Submit"
    }

    response = requests.post(
        "https://neb.ntc.net.np/results.php",
        data=payload
    )

    html = response.text

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

    if not all([name, symbol_match, school, gpa]):
        return "Result not found or invalid symbol/DOB"

    registration = re.search(
        r"<b>Registration No</b>\s*:\s*(\d+)",
        html
    )

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

            # Skip GPA row and invalid rows
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

    if not all([name, symbol_match, school, gpa]):
        return "Result not found or invalid symbol/DOB"

if __name__ == "__main__":
    app.run(debug=True)
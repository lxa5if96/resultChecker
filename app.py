from flask import Flask, render_template, request
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from time import time
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)

cache = {}
CACHE_DURATION = 300


def get_nepali_year():
    now = datetime.now()
    return now.year + 56 if (now.month, now.day) < (4, 14) else now.year + 57


@app.route("/")
def home():
    return render_template(
        "index.html",
        year=get_nepali_year()
    )


@app.route("/result", methods=["POST"])
@limiter.limit("5 per minute")
def result():

    symbol = request.form.get("symbol_number")
    dob = request.form.get("dob")
    
    if not symbol or not symbol.isdigit():
        return "Invalid symbol number"

    if len(symbol) != 8:
        return "Symbol number must be 8 digits"
    
    try:
        datetime.strptime(dob.replace("/", "-"), "%Y-%m-%d")
    except ValueError:
        return "Invalid DOB"

    cache_key = f"{symbol}_{dob}"
    html = None

    if cache_key in cache:
        cached = cache[cache_key]

        if time() - cached["timestamp"] < CACHE_DURATION:
            html = cached["html"]
        else:
            del cache[cache_key]

    if html is None:
        try:
            response = requests.post(
                "https://neb.ntc.net.np/results.php",
                data={
                    "symbol": symbol,
                    "dob": dob,
                    "submit": "Submit"
                },
                timeout=10
            )

            html = response.text

            cache[cache_key] = {
                "html": html,
                "timestamp": time()
            }

        except requests.exceptions.RequestException:
            return "NEB server is unavailable. Please try again later."

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
        return "Result not found or invalid symbol/DOB"

    soup = BeautifulSoup(html, "html.parser")

    subjects = []
    seen = set()

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):

            cols = row.find_all("td")

            if len(cols) == 5:

                code = cols[0].get_text(strip=True)
                subject = cols[1].get_text(strip=True)

                if code.isdigit():

                    key = (code, subject)

                    if key not in seen:
                        seen.add(key)

                        subjects.append({
                            "code": code,
                            "name": subject,
                            "credit": cols[2].get_text(strip=True),
                            "grade": cols[3].get_text(strip=True)
                        })

    return render_template(
        "result.html",
        name=name.group(1).strip(),
        symbol=symbol_match.group(1),
        registration=registration.group(1) if registration else "N/A",
        school=school.group(1).strip(),
        gpa=gpa.group(1),
        subjects=subjects
    )


if __name__ == "__main__":
    app.run()
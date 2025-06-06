from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

# =========================
# Function to get Indian public holidays from Calendarific API
# =========================
def get_indian_holidays(year):
    API_KEY = 'VpAy3ARqq6rCEObiZQZxtvx3aRbEa5Pk'
    url = f"https://calendarific.com/api/v2/holidays?&api_key={API_KEY}&country=IN&year={year}"
    try:
        response = requests.get(url)
        holidays = []
        if response.status_code == 200:
            data = response.json()
            # Loop through each holiday in the response
            for holiday in data['response']['holidays']:
                # Get the ISO date string (YYYY-MM-DD)
                date_str = holiday['date']['iso'][:10]
                # Convert to a date object and add to the list
                holidays.append(datetime.strptime(date_str, "%Y-%m-%d").date())
        else:
            print(f"API error: {response.status_code}")
        return holidays
    except Exception as e:
        print(f"Error fetching holidays: {e}")
        return []

# =========================
# Home route: Handles form and calculation
# =========================
@app.route("/", methods=["GET", "POST"])
def homepage():
    result = None
    error = None
    start_date = ""
    end_date = ""
    classes_per_day = ""

    if request.method == "POST":
        try:
            # Get form data from the user
            start_date = request.form.get("start_date")
            end_date = request.form.get("end_date")
            classes_per_day = request.form.get("classes_per_day")

            # Validate input
            if not start_date or not end_date or not classes_per_day:
                raise ValueError("All fields are required.")
            classes_per_day = int(classes_per_day)
            if classes_per_day <= 0:
                raise ValueError("Classes per day must be positive.")

            # Convert string dates to date objects
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            if start > end:
                raise ValueError("End date must be after start date.")

            # Get holidays for each year in the range
            holiday_years = range(start.year, end.year + 1)
            holidays = []
            for year in holiday_years:
                holidays.extend(get_indian_holidays(year))
            # Only keep holidays within the selected range
            holidays = [h for h in holidays if start <= h <= end]
            holidays = sorted(list(set(holidays)))  # Remove duplicates and sort

            # Calculate working days (skip Sundays and holidays)
            current = start
            working_days = 0
            while current <= end:
                if current.weekday() != 6 and current not in holidays:  # 6 = Sunday
                    working_days += 1
                current += timedelta(days=1)

            # Calculate total and required classes
            total_classes = working_days * classes_per_day
            required_classes = int(total_classes * 0.75)

            # Prepare result for template
            result = {
                "working_days": working_days,
                "total_classes": total_classes,
                "required_classes": required_classes,
                "start_date": start_date,
                "end_date": end_date
            }

        except ValueError as e:
            error = str(e)
        except Exception as e:
            error = "An error occurred. Please check your inputs."
            print(f"General exception: {e}")

    # Render the home page with results or error
    return render_template("home.html", result=result, error=error, start_date=start_date, end_date=end_date, classes_per_day=classes_per_day)

# =========================
# Holidays route: Shows the list of holidays in the selected range
# =========================
@app.route("/holidays")
def holidays_page():
    # Get start_date and end_date from query parameters
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date or not end_date:
        return redirect(url_for('homepage'))

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    holiday_years = range(start.year, end.year + 1)
    holidays = []
    for year in holiday_years:
        holidays.extend(get_indian_holidays(year))
    # Only keep holidays within the selected range
    holidays = [h for h in holidays if start <= h <= end]
    holidays = sorted(list(set(holidays)))  # Remove duplicates and sort

    return render_template("holidays.html", holidays=holidays, start_date=start_date, end_date=end_date)

if __name__ == "__main__":
    app.run(debug=True)

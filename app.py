import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host="crossover.proxy.rlwy.net",
        port=48269,
        user="root",
        password="tPMJyVojazmPjQAzbMSovbBGtgupaIOp",
        database="railway"
    )

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_type = request.form["form_type"]
        car_plate_nb = request.form["car_plate_nb"].strip()

        if form_type == "signin":
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT first_name, last_name
                FROM driver
                WHERE car_plate_nb = %s
            """, (car_plate_nb,))

            user = cursor.fetchone()
            conn.close()

            if user:
                full_name = user[0] + " " + user[1]
                return redirect(url_for("monitor", car_plate_nb=car_plate_nb, username=full_name))
            else:
                return render_template(
                    "index.html",
                    error="Car not found. Please Sign Up first."
                )

        elif form_type == "signup":
            first_name = request.form["first_name"].strip()
            last_name = request.form["last_name"].strip()
            car_model = request.form.get("car_model", "").strip()

            if not first_name or not last_name:
                return render_template(
                    "index.html",
                    error="First name and last name are required for Sign Up."
                )

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT car_plate_nb
                FROM driver
                WHERE car_plate_nb = %s
            """, (car_plate_nb,))

            existing_plate = cursor.fetchone()

            if existing_plate:
                conn.close()
                return render_template(
                    "index.html",
                    error="This car plate number already exists."
                )

            cursor.execute("""
                INSERT INTO driver (first_name, last_name, car_plate_nb, car_model)
                VALUES (%s, %s, %s, %s)
            """, (first_name, last_name, car_plate_nb, car_model))

            conn.commit()
            conn.close()

            full_name = first_name + " " + last_name
            return redirect(url_for("monitor", car_plate_nb=car_plate_nb, username=full_name))

    return render_template("index.html")

@app.route("/monitor/<car_plate_nb>/<username>")
def monitor(car_plate_nb, username):
    return render_template("monitor.html", username=username, car_plate_nb=car_plate_nb)

@app.route("/log", methods=["POST"])
def log():
    data = request.get_json()

    car_plate_nb = data.get("car_plate_nb")
    status = data.get("status")

    conn = get_db_connection()
    cursor = conn.cursor()

    alert_sent = "yes" if status == "Drowsy" else "no"

    cursor.execute("""
        INSERT INTO detection_logs (car_plate_nb, status, alert_sent, detection_time)
        VALUES (%s, %s, %s, NOW())
    """, (car_plate_nb, status, alert_sent))

    conn.commit()
    conn.close()

    return jsonify({"message": "saved"})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

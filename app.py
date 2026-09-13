"""
app.py
------
Flask backend for the AI-Based Smart Waste Classification and Management System.

This version stores every successful prediction in MySQL/XAMPP:
    database: smart_waste_db
    table:    predictions

It supports:
- Normal image upload: multipart field "image"
- Webcam image: JSON {"image_data": "data:image/png;base64,..."}
- Prediction using utils.prediction
- Optional Grad-CAM
- MySQL prediction history
- Dashboard statistics
- History clear
- Health check showing database status
"""

import os
import base64
import uuid
import datetime

import mysql.connector
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from utils.prediction import predict_image, generate_gradcam, load_model_once
from utils.waste_info import WASTE_INFO, CLASS_NAMES


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
HISTORY_FOLDER = os.path.join(BASE_DIR, "history")
HISTORY_FILE = os.path.join(HISTORY_FOLDER, "history.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HISTORY_FOLDER, exist_ok=True)


# ============================================================
# FLASK CONFIG
# ============================================================

app = Flask(__name__)

MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================================================
# MYSQL / XAMPP CONFIG
# ============================================================

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "smart_waste_db"),
    "port": int(os.environ.get("DB_PORT", "3306")),
}

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

DB_READY = False
MODEL_READY = False


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_db_connection():
    """Open a new connection to the XAMPP MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


def initialize_database():
    """
    Make sure the predictions table exists and contains all
    columns required by this application.
    """
    global DB_READY

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create the table if it does not already exist.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                prediction VARCHAR(255) NOT NULL,
                confidence DECIMAL(10,6) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                biodegradable TINYINT(1) NOT NULL DEFAULT 0,
                recyclable VARCHAR(100) NOT NULL DEFAULT ''
            )
            """
        )
        conn.commit()

        # If the table existed before, make sure the newer columns exist.
        cursor.execute("SHOW COLUMNS FROM predictions")
        existing_columns = {row[0].lower() for row in cursor.fetchall()}

        if "biodegradable" not in existing_columns:
            cursor.execute(
                """
                ALTER TABLE predictions
                ADD COLUMN biodegradable TINYINT(1) NOT NULL DEFAULT 0
                """
            )

        if "recyclable" not in existing_columns:
            cursor.execute(
                """
                ALTER TABLE predictions
                ADD COLUMN recyclable VARCHAR(100) NOT NULL DEFAULT ''
                """
            )

        if "created_at" not in existing_columns:
            cursor.execute(
                """
                ALTER TABLE predictions
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """
            )

        conn.commit()

        DB_READY = True

        print("=" * 60)
        print("DATABASE CONNECTED SUCCESSFULLY")
        print(f"Host:     {DB_CONFIG['host']}")
        print(f"Database: {DB_CONFIG['database']}")
        print("Table:    predictions")
        print("=" * 60)

        return True

    except mysql.connector.Error as e:
        DB_READY = False
        print("=" * 60)
        print("DATABASE CONNECTION FAILED")
        print("MySQL error:", e)
        print("=" * 60)
        return False

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def save_history_entry(entry):
    """
    Insert one prediction into MySQL.

    This function deliberately raises an error if INSERT/COMMIT fails,
    so the /api/predict endpoint will NOT silently report success.
    """
    conn = None
    cursor = None

    try:
        print("")
        print("=" * 60)
        print("BEFORE MYSQL SAVE")
        print("Filename:", entry["image_filename"])
        print("Prediction:", entry["predicted_class"])
        print("Confidence:", entry["confidence"])
        print("Biodegradable:", entry["biodegradable"])
        print("Recyclable:", entry["recyclable"])
        print("=" * 60)

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO predictions
            (filename, prediction, confidence, biodegradable, recyclable)
            VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            entry["image_filename"],
            entry["predicted_class"],
            float(entry["confidence"]),
            1 if bool(entry["biodegradable"]) else 0,
            str(entry["recyclable"] or ""),
        )

        cursor.execute(sql, values)
        conn.commit()

        # Use the real MySQL AUTO_INCREMENT id.
        entry["id"] = str(cursor.lastrowid)

        print("=" * 60)
        print("MYSQL SAVE SUCCESS")
        print("Inserted ID:", entry["id"])
        print("=" * 60)
        print("")

        return True

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()

        print("=" * 60)
        print("MYSQL SAVE FAILED")
        print("Error:", e)
        print("=" * 60)
        print("")

        raise RuntimeError(f"MySQL save failed: {e}") from e

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def load_history():
    """Load the latest 200 predictions directly from MySQL."""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                filename,
                prediction,
                confidence,
                biodegradable,
                recyclable,
                created_at
            FROM predictions
            ORDER BY id DESC
            LIMIT 200
            """
        )

        rows = cursor.fetchall()

        history = []

        for row in rows:
            created_at = row.get("created_at")

            if hasattr(created_at, "isoformat"):
                timestamp = created_at.isoformat()
            else:
                timestamp = str(created_at or "")

            history.append(
                {
                    "id": str(row["id"]),
                    "image_filename": row.get("filename", ""),
                    "predicted_class": row.get("prediction", ""),
                    "confidence": float(row.get("confidence") or 0),
                    "biodegradable": bool(row.get("biodegradable")),
                    "recyclable": row.get("recyclable") or "",
                    "timestamp": timestamp,
                }
            )

        return history

    except mysql.connector.Error as e:
        print("MySQL history read error:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# ============================================================
# GENERAL HELPERS
# ============================================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def decode_base64_image(data_url):
    """Convert a webcam data URL into image bytes."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]

    return base64.b64decode(data_url)


# ============================================================
# LOAD AI MODEL
# ============================================================

try:
    load_model_once()
    MODEL_READY = True
    print("AI MODEL READY")
except Exception as e:
    MODEL_READY = False
    print("=" * 60)
    print("WARNING: AI MODEL COULD NOT BE LOADED")
    print("Error:", e)
    print("=" * 60)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/classifier")
def classifier():
    return render_template("classifier.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/guide")
def guide():
    return render_template("guide.html", waste_info=WASTE_INFO)


@app.route("/history")
def history_page():
    return render_template("history.html")


@app.route("/about")
def about():
    return render_template("about.html")


# ============================================================
# PREDICTION API
# ============================================================

@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Predict an uploaded/webcam image and save the result to MySQL.
    """

    global DB_READY

    # Retry DB connection in case MySQL was started after Flask.
    if not DB_READY:
        initialize_database()

    if not MODEL_READY:
        return jsonify(
            {
                "error": "model_unavailable",
                "message": "The AI model is currently unavailable.",
            }
        ), 503

    if not DB_READY:
        return jsonify(
            {
                "error": "database_unavailable",
                "message": (
                    "MySQL database is not available. "
                    "Please make sure XAMPP MySQL is ON."
                ),
            }
        ), 503

    try:
        image_bytes = None
        source_name = None

        explain = (
            request.args.get("explain", "false").lower() == "true"
        )

        # ----------------------------------------------------
        # OPTION 1: Normal file upload
        # ----------------------------------------------------
        if "image" in request.files:
            file = request.files["image"]

            if not file or file.filename == "":
                return jsonify(
                    {
                        "error": "no_image",
                        "message": "No image was uploaded.",
                    }
                ), 400

            if not allowed_file(file.filename):
                return jsonify(
                    {
                        "error": "unsupported_format",
                        "message": (
                            "Unsupported image format. "
                            "Please upload JPG, PNG, JPEG, or WEBP."
                        ),
                    }
                ), 400

            original_name = secure_filename(file.filename)

            source_name = f"{uuid.uuid4().hex}_{original_name}"
            image_bytes = file.read()

        # ----------------------------------------------------
        # OPTION 2: Webcam base64 image
        # ----------------------------------------------------
        elif request.is_json:
            payload = request.get_json(silent=True) or {}
            data_url = payload.get("image_data")

            if not data_url:
                return jsonify(
                    {
                        "error": "no_image",
                        "message": "No webcam image data was received.",
                    }
                ), 400

            try:
                image_bytes = decode_base64_image(data_url)
            except Exception:
                return jsonify(
                    {
                        "error": "corrupted_image",
                        "message": (
                            "The captured image could not be decoded."
                        ),
                    }
                ), 400

            source_name = f"webcam_{uuid.uuid4().hex}.png"

        else:
            return jsonify(
                {
                    "error": "no_image",
                    "message": "No image was provided.",
                }
            ), 400

        # ----------------------------------------------------
        # Validate image bytes
        # ----------------------------------------------------
        if not image_bytes:
            return jsonify(
                {
                    "error": "no_image",
                    "message": "The uploaded image is empty.",
                }
            ), 400

        if len(image_bytes) > MAX_CONTENT_LENGTH:
            return jsonify(
                {
                    "error": "file_too_large",
                    "message": "Please upload an image under 8 MB.",
                }
            ), 413

        # ----------------------------------------------------
        # Save image file
        # ----------------------------------------------------
        save_path = os.path.join(UPLOAD_FOLDER, source_name)

        with open(save_path, "wb") as f:
            f.write(image_bytes)

        # ----------------------------------------------------
        # AI prediction
        # ----------------------------------------------------
        try:
            result = predict_image(image_bytes)
        except Exception as e:
            print("Prediction error:", e)

            return jsonify(
                {
                    "error": "prediction_failed",
                    "message": (
                        "This image could not be processed. "
                        "Please upload a clear image."
                    ),
                }
            ), 400

        # ----------------------------------------------------
        # Optional Grad-CAM
        # ----------------------------------------------------
        if explain:
            try:
                predicted_class = result["predicted_class"]
                class_idx = CLASS_NAMES.index(predicted_class)

                heatmap = generate_gradcam(
                    image_bytes,
                    class_idx,
                )

                result["gradcam"] = heatmap

            except Exception as e:
                print("Grad-CAM generation failed:", e)
                result["gradcam"] = None

        # ----------------------------------------------------
        # Prepare database entry
        # ----------------------------------------------------
        waste_info = result.get("waste_info", {})

        entry = {
            "id": "",
            "image_filename": source_name,
            "predicted_class": result.get("predicted_class", ""),
            "confidence": float(result.get("confidence", 0)),
            "biodegradable": bool(
                waste_info.get("biodegradable", False)
            ),
            "recyclable": str(
                waste_info.get("recyclable", "")
            ),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # ----------------------------------------------------
        # IMPORTANT: SAVE TO MYSQL
        # ----------------------------------------------------
        try:
            save_history_entry(entry)
        except Exception as e:
            print("DATABASE SAVE ERROR:", e)

            return jsonify(
                {
                    "error": "database_save_failed",
                    "message": (
                        "Prediction completed, but the result "
                        "could not be saved to MySQL."
                    ),
                }
            ), 500

        # ----------------------------------------------------
        # Return prediction result
        # ----------------------------------------------------
        result["history_id"] = entry["id"]
        result["image_url"] = f"/uploads/{source_name}"

        return jsonify(result), 200

    except RequestEntityTooLarge:
        return jsonify(
            {
                "error": "file_too_large",
                "message": "The uploaded image is too large. Maximum is 8 MB.",
            }
        ), 413

    except Exception as e:
        print("=" * 60)
        print("UNEXPECTED SERVER ERROR")
        print("Error:", e)
        print("=" * 60)

        return jsonify(
            {
                "error": "server_error",
                "message": "Something went wrong while analyzing the image.",
            }
        ), 500


# ============================================================
# HISTORY API
# ============================================================

@app.route("/api/history", methods=["GET"])
def api_history():
    return jsonify(load_history())


@app.route("/api/history/clear", methods=["POST"])
def api_history_clear():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM predictions")
        conn.commit()

        return jsonify({"status": "cleared"})

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()

        return jsonify(
            {
                "error": "database_error",
                "message": str(e),
            }
        ), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


# ============================================================
# DASHBOARD API
# ============================================================

@app.route("/api/dashboard-stats", methods=["GET"])
def api_dashboard_stats():
    history = load_history()

    total = len(history)

    class_counts = {c: 0 for c in CLASS_NAMES}

    biodeg_count = 0
    non_biodeg_count = 0

    recyclable_count = 0
    non_recyclable_count = 0

    confidences = []

    for entry in history:
        cls = entry.get("predicted_class")

        if cls in class_counts:
            class_counts[cls] += 1

        if entry.get("biodegradable") is True:
            biodeg_count += 1
        else:
            non_biodeg_count += 1

        recyclable_str = str(
            entry.get("recyclable", "")
        ).lower()

        if recyclable_str.startswith("yes"):
            recyclable_count += 1
        elif recyclable_str.startswith("no"):
            non_recyclable_count += 1

        confidences.append(
            float(entry.get("confidence", 0))
        )

    most_frequent = (
        max(class_counts, key=class_counts.get)
        if total > 0
        else None
    )

    avg_confidence = (
        round(sum(confidences) / len(confidences), 2)
        if confidences
        else 0
    )

    return jsonify(
        {
            "total_classifications": total,
            "class_counts": class_counts,
            "most_frequent_class": most_frequent,
            "biodegradable_vs_non": {
                "biodegradable": biodeg_count,
                "non_biodegradable": non_biodeg_count,
            },
            "recyclable_vs_non": {
                "recyclable": recyclable_count,
                "non_recyclable": non_recyclable_count,
            },
            "average_confidence": avg_confidence,
            "recent": history[:10],
        }
    )


# ============================================================
# UPLOADED IMAGES
# ============================================================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():
    # Test DB again so the endpoint reflects current status.
    global DB_READY

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        database_name = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        DB_READY = True

        return jsonify(
            {
                "status": "ok",
                "model_ready": MODEL_READY,
                "database_ready": True,
                "database": database_name,
            }
        )

    except Exception as e:
        DB_READY = False

        return jsonify(
            {
                "status": "ok",
                "model_ready": MODEL_READY,
                "database_ready": False,
                "database": DB_CONFIG["database"],
                "database_error": str(e),
            }
        )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(413)
def handle_413(e):
    return jsonify(
        {
            "error": "file_too_large",
            "message": "The uploaded file is too large. Maximum is 8 MB.",
        }
    ), 413


@app.errorhandler(404)
def handle_404(e):
    try:
        return render_template(
            "error.html",
            code=404,
            message="Page not found.",
        ), 404
    except Exception:
        return jsonify(
            {
                "error": "not_found",
                "message": "Page not found.",
            }
        ), 404


@app.errorhandler(500)
def handle_500(e):
    try:
        return render_template(
            "error.html",
            code=500,
            message="Something went wrong on our end.",
        ), 500
    except Exception:
        return jsonify(
            {
                "error": "server_error",
                "message": "Something went wrong on our end.",
            }
        ), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    print("")
    print("=" * 60)
    print("SMART WASTE CLASSIFIER SERVER")
    print("=" * 60)
    print("Server:   http://127.0.0.1:5000")
    print("Network:  http://0.0.0.0:5000")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"DB Ready: {DB_READY}")
    print(f"Model:    {MODEL_READY}")
    print("=" * 60)
    print("")

    port = int(os.environ.get("PORT", "5000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )

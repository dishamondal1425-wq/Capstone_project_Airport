from flask import Flask, render_template, request, redirect, jsonify, session
import speech_recognition as sr
import joblib
import pandas as pd
from deep_translator import GoogleTranslator
import mysql.connector
import requests
import os
import re
from pydub import AudioSegment
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# Required for Flask session handling used in the chatbot
#app.secret_key = "super_secret_key_change_me"
app.secret_key = os.getenv("SECRET_KEY")
# ==========================================
# MYSQL DATABASE CONNECTION
# ==========================================

def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306))
    )


db = get_db()
cursor = db.cursor()
# ==========================================
# LOAD MODEL
# ==========================================

model = joblib.load("airport_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

recognized_text = ""
latest_booking = {}


# ==========================================
# LANGUAGES
# ==========================================

languages = {
    "English": "en",
    "Hindi": "hi",
    "Bengali": "bn",
    "Tamil": "ta",
    "Telugu": "te",
    "Marathi": "mr",
    "Malayalam": "ml",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Mizo": "lus"
}


# ==========================================
# TEXT IMPROVEMENT
# ==========================================

def improve_airport_text(text):

    replacements = {
        "has been delayed": "is delayed",
        "boarding announcement for": "boarding for",
        "please proceed to": "go to",
        "gate changed to": "new gate"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route('/home')
def home():

    api_key = "abd275dc2dcbfbfb89736fa3e231bd23"

    city = "Kolkata"

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)

    data = response.json()

    temperature = data['main']['temp']
    weather = data['weather'][0]['description']

    return render_template(
        'home.html',
        temperature=temperature,
        weather=weather
    )

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/announcement")
def announcement():
    return render_template("announcement.html")

@app.route("/flight-status", methods=["GET", "POST"])
def flight_status():

    df = pd.read_csv("database/flights.csv")

    # CLEAN STATUS
    df["status"] = df["status"].fillna("On Time")

    # DASHBOARD STATS
    total = len(df)
    on_time = len(df[df["status"].str.lower() == "on time"])
    delayed = len(df[df["status"].str.lower() == "delayed"])

    flights = []

    # ONLY FILTER WHEN USER SUBMITS FORM
    if request.method == "POST":

        user_time = request.form.get("time")

        if user_time:

            df["time"] = pd.to_datetime(df["time"], format="%H:%M")
            selected_time = pd.to_datetime(user_time, format="%H:%M")

            filtered = df[
                (df["time"] >= selected_time) &
                (df["time"] <= selected_time + pd.Timedelta(minutes=40))
            ].copy()

            filtered["time"] = filtered["time"].dt.strftime("%H:%M")

            flights = filtered.to_dict(orient="records")

    return render_template(
        "flight_status.html",
        flights=flights,
        total=total,
        on_time=on_time,
        delayed=delayed
    )

@app.route("/food-order")
def food_order():

    cursor.execute(
        "SELECT * FROM food_orders"
    )

    orders = cursor.fetchall()

    total_bill = sum(
        order[5] for order in orders
    )

    return render_template(
        "food_order.html",
        menu=food_menu,
        orders=orders,
        total_bill=total_bill
    )


@app.route("/add-food", methods=["POST"])
def add_food():

    restaurant = request.form["restaurant"]
    food_name = request.form["food_name"]
    quantity = int(
        request.form["quantity"]
    )
    price = int(
        request.form["price"]
    )

    total_price = (
        quantity * price
    )

    cursor.execute("""
        INSERT INTO food_orders
        (
            restaurant,
            food_name,
            quantity,
            price,
            total_price
        )
        VALUES (%s,%s,%s,%s,%s)
    """, (
        restaurant,
        food_name,
        quantity,
        price,
        total_price
    ))

    db.commit()

    return redirect("/food-order")


@app.route("/place-order")
def place_order():

    # Clear cart after order
    cursor.execute(
        "DELETE FROM food_orders"
    )

    db.commit()

    return render_template(
        "order_success.html"
    )


@app.route(
    "/ticket-booking",
    methods=["GET", "POST"]
)
def ticket_booking():

    booking = None

    if request.method == "POST":

        passenger_name = request.form[
            "passenger_name"
        ]

        source = request.form[
            "source"
        ]

        destination = request.form[
            "destination"
        ]

        flight_number = request.form[
            "flight_number"
        ]

        travel_date = request.form[
            "travel_date"
        ]

        seat_type = request.form[
            "seat_type"
        ]

        # Save in MySQL
        cursor.execute("""
            INSERT INTO
            ticket_bookings
            (
                passenger_name,
                source,
                destination,
                flight_number,
                travel_date,
                seat_type
            )
            VALUES
            (%s,%s,%s,%s,%s,%s)
        """, (
            passenger_name,
            source,
            destination,
            flight_number,
            travel_date,
            seat_type
        ))

        db.commit()

        booking = {
            "name": passenger_name,
            "source": source,
            "destination": destination,
            "flight": flight_number,
            "date": travel_date,
            "seat": seat_type
        }

    return render_template(
        "ticket_booking.html",
        booking=booking
    )

@app.route(
    "/search-flights",
    methods=["POST"]
)
def search_flights():

    source = request.form[
        "source"
    ]

    destination = request.form[
        "destination"
    ]

    travel_date = request.form[
        "travel_date"
    ]

    seat_type = request.form[
        "seat_type"
    ]

    passengers = request.form[
        "passengers"
    ]

    # Load flights
    df = pd.read_csv(
        "database/flights.csv"
    )

    # Search flights
    flights = df[
        (df["source"] == source)
        &
        (
            df["destination"]
            == destination
        )
    ]

    flights = flights.to_dict(
        orient="records"
    )

    return render_template(
        "ticket_booking.html",
        flights=flights,
        travel_date=travel_date,
        seat_type=seat_type,
        passengers=passengers
    )


@app.route(
    "/book-flight/<flight_no>"
)
def book_flight(
    flight_no
):

    df = pd.read_csv(
        "database/flights.csv"
    )

    # Remove spaces
    flight_no = flight_no.strip()

    # Remove spaces in CSV too
    df["flight_no"] = df[
        "flight_no"
    ].astype(str).str.strip()

    # Search flight
    flight_data = df[
        df["flight_no"]
        == flight_no
    ]

    # If not found
    if flight_data.empty:

        return f"""
        Flight {flight_no}
        not found
        """

    flight = flight_data.iloc[0]

    return render_template(
        "book_ticket.html",
        flight=flight
    )


@app.route(
    "/confirm-ticket",
    methods=["POST"]
)
def confirm_ticket():
    global latest_booking

    passenger_name = request.form[
        "passenger_name"
    ]

    source = request.form[
        "source"
    ]

    destination = request.form[
        "destination"
    ]

    flight_number = request.form[
        "flight_number"
    ]

    travel_date = request.form[
        "travel_date"
    ]

    seat_type = request.form[
        "seat_type"
    ]

    # Save to MySQL
    cursor.execute("""
        INSERT INTO
        ticket_bookings
        (
            passenger_name,
            source,
            destination,
            flight_number,
            travel_date,
            seat_type
        )
        VALUES
        (%s,%s,%s,%s,%s,%s)
    """, (
        passenger_name,
        source,
        destination,
        flight_number,
        travel_date,
        seat_type
    ))

    db.commit()

    latest_booking = {
        "name": passenger_name,
        "flight": flight_number,
        "source": source,
        "destination": destination,
        "date": travel_date,
        "seat": seat_type
    }

    return render_template(
        "ticket_success.html",
        name=passenger_name,
        flight=flight_number,
        source=source,
        destination=destination,
        date=travel_date,
        seat=seat_type
    )


@app.route("/download-ticket")
def download_ticket():

    file_path = "boarding_pass.pdf"

    doc = SimpleDocTemplate(
        file_path
    )

    styles = getSampleStyleSheet()

    content = []

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    content.append(
        Paragraph(
            "✈ BOARDING PASS",
            title_style
        )
    )

    content.append(
        Spacer(1, 20)
    )

    content.append(
        Paragraph(
            "Smart Airport Management System",
            heading_style
        )
    )

    content.append(
        Spacer(1, 20)
    )

    # Ticket Details
    content.append(
        Paragraph(
            f"<b>Passenger:</b> {latest_booking['name']}",
            normal_style
        )
    )

    content.append(
        Paragraph(
            f"<b>Flight:</b> {latest_booking['flight']}",
            normal_style
        )
    )

    content.append(
        Paragraph(
            f"<b>Route:</b> {latest_booking['source']} → {latest_booking['destination']}",
            normal_style
        )
    )

    content.append(
        Paragraph(
            f"<b>Date:</b> {latest_booking['date']}",
            normal_style
        )
    )

    content.append(
        Paragraph(
            f"<b>Seat:</b> {latest_booking['seat']}",
            normal_style
        )
    )

    content.append(
        Paragraph(
            "<b>Gate:</b> G-12",
            normal_style
        )
    )

    doc.build(content)

    return send_file(
        file_path,
        as_attachment=True
    )

# ==========================================
# SPEAK
# ==========================================

@app.route("/speak", methods=["POST"])
def speak():

    global recognized_text

    recognizer = sr.Recognizer()

    try:

        with sr.Microphone() as source:

            print("Adjusting for noise...")

            # Better noise cancellation
            recognizer.adjust_for_ambient_noise(
                source,
                duration=3
            )

            # More accurate speech detection
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 1.5

            print("Speak now...")

            audio = recognizer.listen(
                source,
                timeout=15,
                phrase_time_limit=20
            )

        print("Recognizing speech...")

        recognized_text = recognizer.recognize_google(
            audio,
            language="en-US"
        )

        print(
            "Recognized:",
            recognized_text
        )

        text_vector = vectorizer.transform(
            [recognized_text]
        )

        category = model.predict(
            text_vector
        )[0]

        return render_template(
            "announcement.html",
            original_text=recognized_text,
            translated_text=recognized_text,
            category=category,
            success_message="Announcement captured successfully!"
        )

    except sr.WaitTimeoutError:

        return render_template(
            "announcement.html",
            error="No speech detected. Please try again."
        )

    except sr.UnknownValueError:

        return render_template(
            "announcement.html",
            error="Could not understand audio. Speak clearly."
        )

    except Exception as e:

        return render_template(
            "announcement.html",
            error=str(e)
        )



# ==========================================
# AUDIO UPLOAD
# ==========================================

@app.route(
    "/upload-audio",
    methods=["POST"]
)
def upload_audio():

    global recognized_text

    try:

        file = request.files[
            "audio_file"
        ]

        if file.filename == "":

            return render_template(
                "announcement.html",
                error="No file selected"
            )

        upload_folder = (
            "static/uploads"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        filepath = os.path.join(
            upload_folder,
            file.filename
        )

        file.save(filepath)

        recognizer = sr.Recognizer()

        # ==================================
        # Convert Any Audio → Clean WAV
        # ==================================

        file_extension = (
            filepath.lower().split(".")[-1]
        )

        # If not wav OR wav is problematic
        if file_extension in [
            "mp3",
            "mp4",
            "mpeg",
            "m4a",
            "wav"
        ]:

            sound = AudioSegment.from_file(
                filepath
            )

            wav_path = os.path.join(
                upload_folder,
                "converted_audio.wav"
            )

            # Force proper PCM WAV
            sound.set_frame_rate(
                16000
            ).set_channels(
                1
            ).export(
                wav_path,
                format="wav"
            )

            filepath = wav_path

        # ==================================
        # Read audio
        # ==================================

        with sr.AudioFile(
            filepath
        ) as source:

            audio = recognizer.record(
                source
            )

        recognized_text = (
            recognizer.recognize_google(
                audio,
                language="en-US"
            )
        )

        # Predict category
        text_vector = (
            vectorizer.transform(
                [recognized_text]
            )
        )

        category = model.predict(
            text_vector
        )[0]

        return render_template(
            "announcement.html",
            original_text=recognized_text,
            translated_text=recognized_text,
            category=category,
            success_message="Audio analyzed successfully!"
        )

    except sr.UnknownValueError:

        return render_template(
            "announcement.html",
            error="Could not understand audio."
        )

    except Exception as e:

        return render_template(
            "announcement.html",
            error=str(e)
        )

# ==========================================
# TRANSLATE
# ==========================================
@app.route("/translate", methods=["POST"])
def translate():

    global recognized_text

    selected_language = request.form["language"]

    language_code = languages[selected_language]

    # Improve announcement text
    clean_text = improve_airport_text(
        recognized_text
    )

    # Predict category
    text_vector = vectorizer.transform(
        [recognized_text]
    )

    category = model.predict(
        text_vector
    )[0]

    # English selected
    if language_code == "en":

        translated_text = recognized_text
        translated_category = category

    # Other languages
    else:

        translated_text = GoogleTranslator(
            source="en",
            target=language_code
        ).translate(clean_text)

        translated_category = GoogleTranslator(
            source="en",
            target=language_code
        ).translate(category)

    return render_template(
        "announcement.html",
        original_text=recognized_text,
        translated_text=translated_text,
        category=translated_category
    )


# ==========================================
# CHATBOT AI VERSION
# ==========================================

@app.route("/chatbot", methods=["POST"])
def chatbot():

    if "messages" not in session:
        session["messages"] = []

    df = pd.read_csv("database/flights.csv")

    question = request.form.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Please enter a question."})

    q = normalize_query(question.lower())

    # ------------------------
    # Greetings
    # ------------------------
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]

    if q in greetings:
        answer = (
            "👋 Hello! I am your Airport Assistant.\n\n"
            "I can help you with:\n"
            "✈ Flight timings\n"
            "📍 Boarding gates\n"
            "📡 Flight status\n"
            "🌍 Flights to destinations\n\n"
            "Examples:\n"
            "• Show flights to Delhi\n"
            "• Status of AI269\n"
            "• Gate of SG128\n"
            "• Time of flight to Aizawl"
        )

        return jsonify({"answer": answer})

    # ------------------------
    # Detect intent
    # ------------------------
    intent = detect_intent(q)
    flight_no = extract_flight_no(q)

    destination = None

    for city in df["destination"].dropna().unique():
        if city.lower() in q:
            destination = city
            break

    # Detect "to Delhi"
    if not destination:
        match = re.search(r"to\s+([a-zA-Z ]+)", q)

        if match:
            city_name = match.group(1).strip()

            for city in df["destination"].unique():

                if city.lower() == city_name.lower():
                    destination = city
                    break

    answer = ""

    # ------------------------
    # Forgot flight number
    # ------------------------
    if "forgot" in q and "flight" in q:

        if session.get("last_flight"):
            answer = (
                f"✈ Your last searched flight was "
                f"{session['last_flight']}."
            )

        elif session.get("last_destination"):
            answer = (
                f"🌍 You recently searched flights to "
                f"{session['last_destination']}."
            )

        else:
            answer = (
                "I don't know your flight yet. "
                "Tell me your destination."
            )

    # ------------------------
    # Search by Flight Number
    # ------------------------
    elif flight_no:

        row = df[df["flight_no"].str.upper() == flight_no]

        if row.empty:

            answer = (
                f"❌ I couldn't find flight "
                f"{flight_no}."
            )

        else:

            row = row.iloc[0]

            session["last_flight"] = flight_no

            if intent == "status":

                answer = (
                    f"📡 Flight {flight_no} to "
                    f"{row['destination']} is currently "
                    f"{row['status']}."
                )

            elif intent == "gate":

                answer = (
                    f"📍 Flight {flight_no} will board "
                    f"from Gate {row['gate']}."
                )

            elif intent == "time":

                answer = (
                    f"🕒 Flight {flight_no} to "
                    f"{row['destination']} departs at "
                    f"{row['time']}."
                )

            else:

                answer = (
                    f"✈ Flight {flight_no}\n\n"
                    f"🌍 Destination: {row['destination']}\n"
                    f"🕒 Departure: {row['time']}\n"
                    f"📍 Gate: {row['gate']}\n"
                    f"📡 Status: {row['status']}"
                )

    # ------------------------
    # Search by Destination
    # ------------------------
    elif destination:

        matches = df[
            df["destination"].str.lower()
            == destination.lower()
        ]

        session["last_destination"] = destination

        if "time" in q or intent == "time":

            first = matches.iloc[0]

            answer = (
                f"🕒 The next flight to "
                f"{destination} is "
                f"{first['flight_no']} departing "
                f"at {first['time']}."
            )

        else:

            answer = format_flights(matches.head(10))

    # ------------------------
    # Help
    # ------------------------
    elif "help" in q:

        answer = (
            "Try asking:\n\n"
            "• Flights to Delhi\n"
            "• Status of AI269\n"
            "• Gate of SG128\n"
            "• Time of flight to Aizawl\n"
            "• I forgot my flight number"
        )

    # ------------------------
    # Fallback
    # ------------------------
    else:

        answer = (
            "🤖 Sorry, I didn't understand.\n\n"
            "Try:\n"
            "• Flights to Delhi\n"
            "• Status of AI269\n"
            "• Gate of SG128\n"
            "• Time of flight to Aizawl"
        )

    session["messages"].append({
        "sender": "user",
        "text": question
    })

    session["messages"].append({
        "sender": "bot",
        "text": answer
    })

    session.modified = True

    return jsonify({"answer": answer})


# ==========================================
# CHATBOT HELPER FUNCTION STUBS
# ==========================================

def normalize_query(query):
    return query.strip().lower()

def detect_intent(query):
    if "status" in query or "delayed" in query or "on time" in query:
        return "status"
    elif "gate" in query or "boarding" in query:
        return "gate"
    elif "time" in query or "schedule" in query or "departs" in query:
        return "time"
    return "general"

def extract_flight_no(query):
    # Regex look for standard flight numbers (e.g., AI269, SG128, 6E2342)
    match = re.search(r'\b([a-zA-Z0-9]{2,3}\s*\d{3,4})\b', query)
    if match:
        return match.group(1).replace(" ", "").upper()
    return None

def format_flights(df_slice):
    if df_slice.empty:
        return "No upcoming flights found for this destination."
    
    result = "✈ Upcoming Flights:\n"
    for _, row in df_slice.iterrows():
        result += f"• {row['flight_no']} | Departs: {row['time']} | Gate: {row['gate']} | Status: {row['status']}\n"
    return result.strip()


# ==========================================
# FOOD MENU STATIC DATA (FINAL CORRECTED PATHS)
# ==========================================

food_menu = {
    "KFC": {
        "image": "image/restaurant/kfc.png",
        "items": [
            {"name": "Chicken Burger", "price": 150, "image": "image/food/chicken_burger.png"},
            {"name": "Fries", "price": 100, "image": "image/food/fries.png"},
            {"name": "Chicken Wings", "price": 250, "image": "image/food/chicken_wings.png"}
        ]
    },
    "Dominos": {
        "image": "image/restaurant/dominos.png",
        "items": [
            {"name": "Veg Pizza", "price": 299, "image": "image/food/veg_pizza.png"},
            {"name": "Garlic Bread", "price": 120, "image": "image/food/garlic_bread.png"},
            {"name": "Cheese Pizza", "price": 350, "image": "image/food/cheese_pizza.png"}
        ]
    },
    "CCD": {
        "image": "image/restaurant/subway.png",  # Update to your actual ccd restaurant image if you have one!
        "items": [
            {"name": "Coffee", "price": 120, "image": "image/food/coffee.png"},
            {"name": "Sandwich", "price": 180, "image": "image/food/sandwich.png"},
            {"name": "Cold Coffee", "price": 160, "image": "image/food/cold_coffee.png"}
        ]
    },
    "Subway": {
        "image": "image/restaurant/subway.png",
        "items": [
            {"name": "Veg Sub", "price": 220, "image": "image/food/veg_sub.png"},
            {"name": "Chicken Sub", "price": 280, "image": "image/food/chicken_sub.png"},
            {"name": "Cookies", "price": 80, "image": "image/food/cookies.png"}
        ]
    }
}


if __name__ == "__main__":
    app.run()
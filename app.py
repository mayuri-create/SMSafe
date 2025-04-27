import sys
import streamlit as st
import numpy as np
import pickle
import string
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import nltk  # Import NLTK
import mysql.connector  # Import MySQL Connector
import pandas as pd
import re
import time
import requests
from streamlit_lottie import st_lottie
from cryptography.fernet import Fernet  # Import Cryptography
from sklearn.feature_extraction.text import CountVectorizer  # Import Scikit-Learn

# Download necessary NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Function to load Lottie animation from a URL
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Sidebar for persistent page selection using buttons
st.sidebar.title("Navigation")
if st.sidebar.button("Home", key="home_button_1"):
    st.session_state.page = "Home"
if st.sidebar.button("Create Account", key="create_account_nav_button"):
    st.session_state.page = "Create Account"
if st.sidebar.button("Login", key="login_nav_button"):
    st.session_state.page = "Login"
if st.sidebar.button("Message History", key="history_nav_button"):
    st.session_state.page = "Message History"
if st.sidebar.button("Feedback", key="feedback_nav_button"):
    st.session_state.page = "Feedback"
if st.sidebar.button("About", key="about_nav_button"):
    st.session_state.page = "About"
if st.sidebar.button("Translator", key="translator_nav_button"):
    st.session_state.page = "Translator"

indian_languages = ['en', 'hi', 'bn', 'te', 'mr', 'ta', 'ur', 'gu', 'ml', 'kn']
language_names = {
    'en': 'English',
    'hi': 'Hindi',
    'bn': 'Bengali',
    'te': 'Telugu',
    'mr': 'Marathi',
    'ta': 'Tamil',
    'ur': 'Urdu',
    'gu': 'Gujarati',
    'ml': 'Malayalam',
    'kn': 'Kannada'
}


# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = "Home"  # Default page
if 'prediction_time' not in st.session_state:
    st.session_state.prediction_time = 0.0
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""

# Database connection details
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "cipherscan"

# Add background image CSS
st.markdown(
    f"""
    <style>
        body {{
            background-image: url("file:///C:/Users/mahaj/OneDrive/Desktop/AI%20INTERNSHIP%20PROJECT/TextSafe-main/TextSafe-main/sms%20spam%20image.jpg");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            color: #333333; 
        }}
        .reportview-container {{
            background: transparent !important;
        }}
        .sidebar .sidebar-content {{
            background: linear-gradient(to bottom, #E0FFFFCC, #AFEEEECC) !important;
        }}
        .detection-timer {{
            font-size: 1.5em;
            font-weight: bold;
            color: #FF8C00; 
            margin-top: 10px;
            text-align: center;
            animation: pulse 1s infinite alternate;
        }}
        @keyframes pulse {{
            0% {{ opacity: 0.8; }}
            100% {{ opacity: 1; }}
        }}
        .spam-label {{
            font-size: 2em;  
            font-weight: bold; 
            color: white; 
            background-color: green; 
            padding: 10px; 
            border-radius: 5px; 
            text-align: center; 
            margin-top: 15px; 
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Fresh Custom CSS for vibrant styling and persistent sidebar buttons with gradient
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Poppins', sans-serif;
        }}
        .reportview-container {{
            padding: 1rem;
        }}
        h1, h2, h3 {{
            color: #2E8B57;
            animation: slideIn 1s ease-in-out;
            text-align: center;
        }}
        @keyframes slideIn {{
            0% {{ transform: translateY(-20px); opacity: 0; }}
            100% {{ transform: translateY(0); opacity: 1; }}
        }}
        .stButton > button {{
            background: linear-gradient(to right, #ADD8E6, #87CEEB) !important;
            color: #333333;
            font-weight: bold;
            border-radius: 8px;
            border: 1px solid #ADD8E6;
            padding: 10px 20px;
            margin-bottom: 5px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            width: 100%;
            box-sizing: border-box;
        }}
        .stButton > button:hover {{
            background: linear-gradient(to right, #87CEEB, #6495ED) !important;
            transform: scale(1.02);
            border-color: #6495ED;
        }}
        .stButton > button:focus:not(:active) {{
            outline: 2px solid #4682B4;
        }}
        .sidebar .sidebar-content {{
            color: #333333;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.05);
        }}
        .sidebar .stButton > button[data-baseweb="button"][aria-current="true"] {{
            background: linear-gradient(to right, #90EE90, #3CB371) !important;
            color: white;
            border-color: #3CB371;
        }}
        .css-1d391kg {{
            background-color: #f5f5f5cc !important;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            animation: fadeIn 0.8s ease-in-out;
        }}
        @keyframes fadeIn {{
            from {{opacity: 0;}}
            to {{opacity: 1;}}
        }}
        .stTextArea textarea {{
            background-color: #f0fff0 !important;
            border: 2px solid #98FB98;
            border-radius: 10px;
            padding: 10px;
            color: #000000;
            caret-color: #000000;
        }}
        .stTextInput > div > input {{
            background-color: #e0ffff !important;
            border: 2px solid #8FBC8F;
            border-radius: 10px;
            padding: 10px;
            color: #000000;
            caret-color: #000000;
        }}
        .stTable {{
            background-color: #fffaf0 !important;
            border-radius: 10px;
            padding: 1rem;
        }}
        .css-1kyxreq, .css-1d391kg {{
            padding: 2rem 2rem 0.5rem 2rem;
        }}
        .detection-timer {{
            font-size: 1.5em;
            font-weight: bold;
            color: #FF8C00;
            margin-top: 10px;
            text-align: center;
            animation: pulse 1s infinite alternate;
        }}
        @keyframes pulse {{
            0% {{ opacity: 0.8; }}
            100% {{ opacity: 1; }}
        }}
    </style>
""", unsafe_allow_html=True)

# --- Database Interaction Functions ---
def create_account(full_name, username, password):
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        mycursor = mydb.cursor()
        sql = "INSERT INTO users (full_name, username, password) VALUES (%s, %s, %s)"
        val = (full_name, username, password) # In a real app, hash the password!
        mycursor.execute(sql, val)
        mydb.commit()
        return mycursor.rowcount > 0
    except mysql.connector.Error as err:
        print(f"Error creating account: {err}")
        return False
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()

def validate_login(username, password):
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        mycursor = mydb.cursor()
        sql = "SELECT * FROM users WHERE username = %s AND password = %s" # In a real app, compare hashed passwords!
        val = (username, password)
        mycursor.execute(sql, val)
        result = mycursor.fetchone()
        return result is not None
    except mysql.connector.Error as err:
        print(f"Error validating login: {err}")
        return False
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()

def insert_message(sms, is_spam, username):
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        mycursor = mydb.cursor()
        # Get the user_id based on the username
        mycursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_result = mycursor.fetchone()
        if user_result:
            user_id = user_result[0]
            sql = "INSERT INTO messages (user_id, message_text, is_spam) VALUES (%s, %s, %s)"
            val = (user_id, sms, is_spam)
            mycursor.execute(sql, val)
            mydb.commit()
            return mycursor.rowcount > 0
        else:
            print(f"User  not found: {username}")
            return False
    except mysql.connector.Error as err:
        print(f"Error inserting message: {err}")
        return False
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()

def fetch_message_history(username):
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        mycursor = mydb.cursor()
        mycursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        user_result = mycursor.fetchone()
        if user_result:
            user_id = user_result[0]
            sql = "SELECT message_text, is_spam FROM messages WHERE user_id = %s ORDER BY processed_at DESC"
            mycursor.execute(sql, (user_id,))
            history = mycursor.fetchall()
            return history
        else:
            print(f"User  not found: {username}")
            return []
    except mysql.connector.Error as err:
        print(f"Error fetching message history: {err}")
        return []
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()

def insert_feedback(feedback, username):
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        mycursor = mydb.cursor()
        # Get the user_id based on the username (can be NULL if you allow anonymous feedback)
        user_id = None
        if username:
            mycursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            user_result = mycursor.fetchone()
            if user_result:
                user_id = user_result[0]
        sql = "INSERT INTO feedback (user_id, feedback_text) VALUES (%s, %s)"
        val = (user_id, feedback)
        mycursor.execute(sql, val)
        mydb.commit()
        return mycursor.rowcount > 0
    except mysql.connector.Error as err:
        print(f"Error inserting feedback: {err}")
        return False
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)
    y = []
    for i in text:
        if i.isalnum():
            y.append(i)
    text = y[:]
    y.clear()
    for i in text:
        if i not in stopwords.words('english') and i not in string.punctuation:
            y.append(i)
    text = y[:]
    y.clear()
    for i in text:
        y.append(ps.stem(i))
    return " ".join(y)

# Load your model and vectorizer
try:
    model = pickle.load(open('model.pkl', 'rb'))
    tk = pickle.load(open('vectorizer.pkl', 'rb'))
except FileNotFoundError:
    st.error("Model or vectorizer file not found. Please ensure 'model.pkl' and 'vectorizer.pkl' are in the same directory.")
    st.stop()
except Exception as e:
    st.error(f"Error loading model or vectorizer: {e}")
    st.stop()


def animated_result(prediction):
    """Displays the prediction with color-coded and animated text."""
    color = "red" if prediction == "Spam" else "green"
    return components.html(
        f"""
        <div style="font-size: 24px; font-weight: bold; color: {color}; animation: fadeIn 1s;">
            {prediction}
        </div>
        <style>
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        </style>
        """,
        height=30,
    )

if st.session_state.page == "Home":
    st.title("Welcome to CipherScan")

    if st.session_state.logged_in:
        st.write(f"Logged in as: {st.session_state.username}")

        # Logout
        if st.sidebar.button("Logout", key="logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.page = "Home"
            st.rerun()

        # Main App Section
        st.subheader("Enter SMS Messages for Prediction")
        user_input = st.text_area("Type your message (one per line):", key="input_sms", value=st.session_state.get('input_sms', ''))

        if user_input:
            st.markdown(f"<span style='font-size: 20px; font-weight: bold;'>{user_input}</span>", unsafe_allow_html=True)

        if st.button("Predict"):
            loading_url = "https://lottie.host/1bd199a3-c7c4-4866-bebf-93d4cd535d7e/i5UF9K47la.lottie"  # Loading animation URL
            loading_animation = load_lottie_url(loading_url)
            st_lottie(loading_animation, speed=1, width=200, height=200, key="loading_animation")
            if user_input:
                start_time = time.time()
                with st.spinner("Processing..."):
                    sms_list = user_input.splitlines()
                    results = []
                    spam_words = []

                    for sms in sms_list:
                        transformed_sms = transform_text(sms)
                        vector_input = tk.transform([transformed_sms])
                        prediction_value = model.predict(vector_input)[0]
                        prediction_label = "Spam" if prediction_value == 1 else "Not Spam"

                        if insert_message(sms, int(prediction_value), st.session_state.username):
                            results.append((sms, prediction_label))
                            if prediction_value == 1:
                                spam_words.extend(transformed_sms.split())

                    end_time = time.time()
                    st.session_state.prediction_time = end_time - start_time
                # Hide loading animation and show success message
                st.success("Prediction completed!") 
                # Timer display
                st.markdown(
                    f"<div class='detection-timer'>Detection Time: {st.session_state.prediction_time:.4f} seconds</div>",
                    unsafe_allow_html=True
                )

                # Results display
                st.subheader("Prediction Results:")
                for sms, prediction_result in results:
                    st.write(f"Message: '{sms}'")
                    if prediction_result == "Not Spam":
                        st.markdown('<div class="spam-label">Not Spam</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="spam-label" style="background-color: red; color: white; padding: 5px; border-radius: 5px;">Spam</div>', unsafe_allow_html=True)

                # Optional spam word frequency
                if spam_words:
                    st.subheader("Top 10 Most Frequent Spam Words")
                    word_freq = pd.Series(spam_words).value_counts()
                    st.bar_chart(word_freq.head(10))
            else:
                st.error("Please enter at least one message.")

        # Add some space before the Clear Input button
        st.markdown("<br><br>", unsafe_allow_html=True)  # Adds vertical space

        if st.button('Clear Input'):
            st.session_state.input_sms = ""
            st.rerun()

    else:
        st.info("Please log in or create an account to use the spam detection features.")

# Create Account Page
elif st.session_state.page == "Create Account":
    st.title("Create Account")
    full_name_input = st.text_input("Full Name")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    re_password_input = st.text_input("Re-enter Password", type="password")
    password_regex = re.compile(r'^(?=.\d)(?=.[A-Z])(?=.*[^a-zA-Z0-9\s]).{8,}$')  # Corrected regex
    name_regex = re.compile(r"^[a-zA-Z\s]+$")  # Regex to allow only alphabets and spaces

    if st.button("Create Account", key="create_account_button"):
        if full_name_input and username_input and password_input and re_password_input:
            full_name = full_name_input.strip()
            if not name_regex.match(full_name):
                st.error("Please enter a valid name using alphabets and spaces only.")
            elif password_input != re_password_input:
                st.error("Passwords do not match. Please try again.")
            elif not password_regex.match(password_input):
                print(f"Password entered: '{password_input}'") # Debug print
                match_result = password_regex.match(password_input)
                print(f"Regex match result: {match_result}") # Debug print
                st.error("Password must be at least 8 characters long, contain at least one uppercase letter, one number, and one special character.") # Updated error message
            else:
                if create_account(full_name, username_input, password_input):
                    st.success("Account created successfully! You can now log in.")
                    st.session_state.page = "Login" # Redirect to login after successful creation
                    st.rerun()
                else:
                    st.error("Failed to create account. Please try again.")
        else:
            st.error("Please fill in all fields.")

# Login Page
elif st.session_state.page == "Login":
    st.title("Login")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    if st.button("Login", key="login_button"):
        if username_input and password_input:
            if validate_login(username_input, password_input):
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success("Logged in successfully!")
                st.session_state.page = "Home" # Redirect to home after successful login
                st.rerun()
            else:
                st.error("Invalid username or password. Please create an account first.")
        else:
            st.error("Please enter both username and password.")

# Message History Page
elif st.session_state.page == "Message History":
    st.title("Message History")
    if st.session_state.logged_in:
        history = fetch_message_history(st.session_state.username)
        if history:
            st.subheader("Your Message History")
            history_df = pd.DataFrame(history, columns=["Message", "Is Spam"])
            st.table(history_df)
        else:
            st.write("No message history found.")
    else:
        st.error("Please log in to view your message history.")

# Feedback Page
elif st.session_state.page == "Feedback":
    st.title("Feedback")
    if st.session_state.logged_in:
        feedback_input = st.text_area("Your Feedback")
        if st.button("Submit Feedback", key="submit_feedback_button"):
            if feedback_input:
                if insert_feedback(feedback_input, st.session_state.username):
                    st.success("Feedback submitted successfully!")
                    st.session_state.page = "Home" # Redirect to home after submitting feedback
                    st.rerun()
                else:
                    st.error("Failed to submit feedback. Please try again.")
            else:
                st.error("Please enter your feedback.")
    else:
        st.error("Please log in to submit feedback.")

# About Page
elif st.session_state.page == "About":
    st.title("About CipherScan")
    st.write("""
    Welcome to CipherScan, your trusted partner in safeguarding your digital communication! In an age where spam messages can clutter your inbox and compromise your privacy, we are dedicated to providing you with a reliable solution to identify and filter out unwanted content.

    *What We Do:*  
    CipherScan utilizes advanced machine learning algorithms to analyze your SMS messages and determine whether they are spam or legitimate. Our intuitive interface allows you to easily input your messages for instant analysis, giving you peace of mind and control over your communications.

    *Why Choose Us?*

    - *User-Friendly Interface:* Our platform is designed with you in mind, making it easy to navigate and use.
    - *Real-Time Analysis:* Get immediate feedback on your messages, helping you make informed decisions.
    - *Privacy First:* We prioritize your privacy and ensure that your data is handled securely and confidentially.
    - *Feedback-Driven:* Your input is invaluable to us! We continuously improve our system based on user feedback to enhance your experience.

    *Join Us Today!*  
    Create an account, log in, and start protecting yourself from spam messages. Together, we can create a safer and more enjoyable messaging experience.

    Thank you for choosing CipherScan. Your trust is our greatest asset!
    """)
# Translator Page
elif st.session_state.page == "Translator":
    st.title("Translate Message")
    if st.session_state.logged_in:
        text_to_translate = st.text_area("Enter text to translate:", value=st.session_state.translated_text)
        target_language = st.selectbox("Select target language", ["English", "Hindi"])

        if st.button("Translate"):
            if text_to_translate.strip():  # Check if there is text to translate
                try:
                    translator = GoogleTranslator(source='auto', target=target_language.lower())
                    st.session_state.translated_text = translator.translate(text_to_translate)
                    st.success("Translation successful!")
                except Exception as e:
                    st.error(f"Translation failed: {e}")
            else:
                st.error("Please add text to translate.")  # Validation message
    else:
        st.error("Please log in to use the translation feature.")



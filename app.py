import streamlit as st
import numpy as np
import pickle 
import string
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import nltk
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt

# Download necessary NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
ps = PorterStemmer()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Database functions
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='smsspam_detection'
        )
        return connection
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return None

def insert_message(message, is_spam, username):
    if not username:
        st.error("Please log in to submit messages")
        return False
    
    connection = connect_to_db()
    if connection:
        try:
            cursor = connection.cursor()
            sql = "INSERT INTO message (message, is_spam, username) VALUES (%s, %s, %s)"
            cursor.execute(sql, (message, is_spam, username))
            connection.commit()
            return True
        except mysql.connector.Error as err:
            st.error(f"Error saving message: {err}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False

def insert_feedback(feedback, username):
    if not username:
        st.error("Please log in to submit feedback")
        return False
    
    connection = connect_to_db()
    if connection:
        try:
            cursor = connection.cursor()
            sql = "INSERT INTO feedback (feedback, username) VALUES (%s, %s)"
            cursor.execute(sql, (feedback, username))
            connection.commit()
            return True
        except mysql.connector.Error as err:
            st.error(f"Error saving feedback: {err}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False

def fetch_message_history(username):
    connection = connect_to_db()
    if connection:
        try:
            cursor = connection.cursor()
            sql = "SELECT message, is_spam FROM message WHERE username = %s"
            cursor.execute(sql, (username,))
            records = cursor.fetchall()
            return records
        except mysql.connector.Error as err:
            st.error(f"Error fetching message history: {err}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []

# Text transformation function
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

# Load models
tk = pickle.load(open("vectorizer.pkl", 'rb'))
model = pickle.load(open("model.pkl", 'rb'))

# Page configuration
st.set_page_config(page_title="SMSafe", page_icon="📱", layout="wide")

# Custom CSS for styling with the new color scheme
st.markdown(
    """
    <style>
        body {
            background-color: #FAF0E6; /* Linen */
            color: #283593; /* Indigo Blue */
        }
        .reportview-container {
            background: #FAF0E6; /* Linen */
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        h1, h2 {
            color: #D32F2F; /* Crimson Red */
        }
        .stButton>button {
            background-color: #1A237E; /* Deep Navy */
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            cursor: pointer;
            transition: background-color 0.3s;
            width: 100%; /* Make buttons full width */
            height: 50px; /* Set a fixed height */
        }
        .stButton>button:hover {
            background-color: #0D47A1; /* Darker Navy for hover */
        }
        .sidebar .sidebar-content {
            background-color: #E57373; /* Blush Red for sidebar */
            border-radius: 10px;
            padding: 10px;
        }
        .sidebar {
            background-color: #E57373; /* Blush Red for sidebar */
            color: white; /* Sidebar text color */
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar for page selection using buttons
st.sidebar.title("Navigation")
if st.sidebar.button("Home"):
    st.session_state.page = "Home"
elif st.sidebar.button("Message History"):
    st.session_state.page = "Message History"
elif st.sidebar.button("Feedback"):
    st.session_state.page = "Feedback"
elif st.sidebar.button("About"):
    st.session_state.page = "About"

# Set default page if not set
if 'page' not in st.session_state:
    st.session_state.page = "Home"

# Home Page
if st.session_state.page == "Home":
    st.title("Welcome to SMSafe")
    
    # Authentication Section
    if not st.session_state.logged_in:
        st.warning("Please log in to use the SMSafe service")
        username_input = st.sidebar.text_input("Username")
        if st.sidebar.button("Login"):
            if username_input:
                st.session_state.username = username_input
                st.session_state.logged_in = True
                st.success(f"Welcome, {username_input}!")
                st.experimental_rerun()
            else:
                st.error("Please enter a username")
    else:
        # Show logged in user
        st.write(f"Logged in as: {st.session_state.username}")
        
        # Logout button
        if st.sidebar.button("Logout", key="logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.experimental_rerun()
        
        # Main Application (only shown when logged in)
        st.subheader("Enter SMS Messages for Prediction")
        user_input = st.text_area("Type your message (one per line):")
        
        # Display user input in bold and increased size
        if user_input:
            st.markdown(f"<span style='font-size: 20px; font-weight: bold;'>{user_input}</span>", unsafe_allow_html=True)
        
        if st.button("Predict"):
            if user_input:
                with st.spinner("Processing..."):
                    sms_list = user_input.splitlines()
                    results = []
                    spam_words = []
                    for sms in sms_list:
                        transformed_sms = transform_text(sms)
                        vector_input = tk.transform([transformed_sms])
                        result = model.predict(vector_input)[0]
                        result = int(result)
                        # Store message with username
                        if insert_message(sms, result, st.session_state.username):
                            results.append((sms, "Spam" if result == 1 else "Not Spam"))
                            if result == 1:
                                spam_words.extend(transformed_sms.split())
                    # Display results
                    if results:
                        st.subheader("Prediction Results")
                        results_df = pd.DataFrame(results, columns=["Message", "Prediction"])
                        st.table(results_df)
                        # Visualize spam words
                        if spam_words:
                            st.subheader("Common Words in Spam Messages")
                            word_freq = pd.Series(spam_words).value_counts()
                            st.bar_chart(word_freq.head(10))
            else:
                st.error("Please enter at least one message.")
        
        # Clear Input Button
        if st.button('Clear Input'):
            st.session_state.input_sms = ""
            st.experimental_rerun()  # Rerun the app to refresh

# Message History Page
if st.session_state.page == "Message History":
    st.title("Message History")
    
    if st.session_state.logged_in:
        # Fetch and display message history
        messages = fetch_message_history(st.session_state.username)
        if messages:
            st.subheader("Your Message History")
            message_df = pd.DataFrame(messages, columns=["Message", "Is Spam"])
            st.table(message_df)
        else:
            st.write("No messages found in your history.")
    else:
        st.warning("Please log in to view your message history.")

# Feedback Page
if st.session_state.page == "Feedback":
    st.title("User  Feedback")
    
    if st.session_state.logged_in:
        feedback_input = st.text_area("Please provide your feedback:")
        
        if st.button("Submit Feedback"):
            if feedback_input:
                if insert_feedback(feedback_input, st.session_state.username):
                    st.success("Thank you for your feedback!")
                else:
                    st.error("There was an error submitting your feedback.")
            else:
                st.error("Feedback cannot be empty.")
    else:
        st.warning("Please log in to submit feedback.")

# About Page
if st.session_state.page == "About":
    st.title("About SMSafe")
    st.write("""
        SMSafe is a spam detection application that helps users identify spam messages in their SMS inbox.
        Users can log in, submit messages for prediction, and provide feedback on the service.
    """)
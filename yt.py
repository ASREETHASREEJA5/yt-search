import streamlit as st
import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Fetch API keys from .env
SHEET_ID = os.getenv('SHEET_ID')  # Replace with your Google Sheets ID
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Initialize session state for video links and feedback if they don't exist
if 'video_links' not in st.session_state:
    st.session_state.video_links = []

if 'feedback' not in st.session_state:
    st.session_state.feedback = []

# Function to fetch YouTube video links
def get_video_links(query):
    API_KEY = os.getenv('API_KEY')  # You can get an individual API key or choose from your list
    BASE_URL = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'key': API_KEY,
        'type': 'video',
        'maxResults': 5
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if 'error' in data:
        st.error(f"Error: {data['error']}")
        return []

    if 'items' not in data:
        st.warning("No items found in the response.")
        return []

    video_links = []
    for item in data['items']:
        video_id = item['id']['videoId']
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        video_links.append(video_url)

    return video_links

# Function to authenticate and get the Google Sheets client
def authenticate_google_sheets():
    try:
        credentials = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(credentials)
        return gc.open_by_key(SHEET_ID)
    except Exception as e:
        st.error(f"Error authenticating Google Sheets: {e}")
        print(f"Error authenticating Google Sheets: {e}")

# Function to save feedback in Google Sheets
def save_feedback_to_sheets(video_url, feedback):
    try:
        gc = authenticate_google_sheets()
        worksheet = gc.worksheet('Sheet1')  # Ensure 'Sheet1' is the correct sheet name
        st.write(f"Saving to Google Sheets: Video URL: {video_url}, Feedback: {feedback}")  # Debug output
        worksheet.append_row([video_url, feedback])
    except Exception as e:
        st.error(f"Error saving feedback to Google Sheets: {e}")
        print(f"Error saving feedback to Google Sheets: {e}")

# Streamlit app
st.title("YouTube Video Search and Feedback")

# Query input
question = st.text_input("Enter your question:")
if st.button("Search"):
    if question:
        st.write("Searching for videos...")  # Temporary message while searching
        # Fetch actual YouTube video links based on the user's query
        videos = get_video_links(question)
        st.session_state.video_links = videos
    else:
        st.warning("Please enter a question to search.")

# Display video links and feedback buttons
if st.session_state.video_links:
    st.subheader("Video Links:")
    for video in st.session_state.video_links:
        st.write(video)
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"👍 Like {video}", key=f"like-{video}"):
                save_feedback_to_sheets(video, "like")
        with col2:
            if st.button(f"👎 Dislike {video}", key=f"dislike-{video}"):
                save_feedback_to_sheets(video, "dislike")

# Feedback records (just for displaying)
st.subheader("Feedback Records")
if st.session_state.feedback:
    for record in st.session_state.feedback:
        st.write(f"Video: {record['video_url']} - Feedback: {record['feedback']}")
else:
    st.write("No feedback records found.")

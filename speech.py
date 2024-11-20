import os
import pickle
import tempfile
from datetime import datetime

import streamlit as st
from audiorecorder import audiorecorder
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from audiogpt import process_audio_with_openai

st.set_page_config(layout="wide", page_title="Speech Proficiency Test")
st.html("<style> .main {overflow: hidden} </style>")

# OAuth Scopes
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def authenticate_google_drive():
    """Authenticate and return a Drive API client."""
    creds = None
    client_secrets = {
        "web": {
            "client_id": st.secrets["web"]["client_id"],
            "project_id": st.secrets["web"]["project_id"],
            "auth_uri": st.secrets["web"]["auth_uri"],
            "token_uri": st.secrets["web"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["web"][
                "auth_provider_x509_cert_url"
            ],
            "client_secret": st.secrets["web"]["client_secret"],
            "redirect_uris": st.secrets["web"]["redirect_uris"],
        }
    }
    # Load credentials if they exist
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If no credentials, authenticate with the user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def upload_to_drive(file_path, file_name):
    """Upload a file to Google Drive."""
    drive_service = authenticate_google_drive()
    file_metadata = {"name": file_name}
    media = MediaFileUpload(file_path, mimetype="audio/wav")
    drive_service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()


def reset_form():
    st.session_state["form_submitted"] = False


def show_sign_up_form():
    st.markdown(
        """
        <div style="text-align: center; font-size: 36px; font-weight: bold; color: red; margin-bottom: 15px; margin-top: 0; padding: 0;">
            User Sign Up Form
        </div>
        """,
        unsafe_allow_html=True,
    )
    col = st.columns((1, 3, 1))[1]
    name = col.text_input("Name")
    age = col.number_input("Age", min_value=0, max_value=120)
    sex = col.selectbox("Sex", options=["Male", "Female", "Other"])
    email = col.text_input("Email")

    col = st.columns((5, 1, 5))[1]
    if col.button("Submit"):
        # Validate inputs
        if name and age and email:
            st.session_state["user_data"] = {
                "name": name,
                "age": age,
                "sex": sex,
                "email": email,
            }
            st.session_state["form_submitted"] = True
            st.rerun()
        else:
            st.warning("Please fill in all required fields")


def show_audio_recorder():
    st.markdown(
        """
        <div style="text-align: center; font-size: 36px; font-weight: bold; color: red;">
            Technical Speech Proficiency 
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns((1, 1))
    with col1:
        audio = audiorecorder("", "", "", show_visualizer=True)

    if len(audio) > 0:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            audio.export(temp_file.name, format="wav")
            temp_file_path = temp_file.name

        with col2:
            st.audio(temp_file_path)

        t = datetime.now().strftime("%m-%d-%H-%M")
        file_name = (
            st.session_state["user_data"]["name"]
            + "_"
            + st.session_state["user_data"]["email"]
            + "_"
            + str(st.session_state["user_data"]["age"])
            + "_"
            + st.session_state["user_data"]["sex"]
            + "_"
            + t
            + ".wav"
        )
        upload_to_drive(temp_file_path, file_name)

        technical = process_audio_with_openai(temp_file_path)

        # Scores (dummy values, replace with real ones as needed)
        scores = {
            "Coherence": 4,
            "Pronunciation": 3,
            "Vocabulary": 5,
            "Fluency": 4,
            "Grammar": 3,
        }

        st.markdown(
            """
            <div style="text-align: center; font-size: 18px; font-weight: bold; color: red; margin-bottom: 15px; margin-top: 20px; padding: 0;">
                Scores 
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(
                f'<div style="text-align: center; font-size: 36px; font-weight: bold;">{scores["Coherence"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="text-align: center; font-size: 18px; margin-bottom: 10px">Coherence</div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<div style="text-align: center; font-size: 36px; font-weight: bold; margin-bottom: 10px">{scores["Pronunciation"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="text-align: center; font-size: 18px;">Pronunciation</div>',
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f'<div style="text-align: center; font-size: 36px; font-weight: bold; ">{scores["Vocabulary"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="text-align: center; font-size: 18px;">Vocabulary</div>',
                unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                f'<div style="text-align: center; font-size: 36px; font-weight: bold;">{scores["Fluency"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="text-align: center; font-size: 18px;">Fluency</div>',
                unsafe_allow_html=True,
            )
        with col5:
            st.markdown(
                f'<div style="text-align: center; font-size: 36px; font-weight: bold;">{scores["Grammar"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="text-align: center; font-size: 18px;">Grammar</div>',
                unsafe_allow_html=True,
            )

        # Feedback Container
        container = st.container()
        with container:
            st.markdown(
                """
                <div style="text-align: center; font-size: 18px; font-weight: bold; color: red; margin-bottom: 5px; margin-top: 20px; padding: 0;">
                    Feedback 
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(technical, unsafe_allow_html=True)

        os.remove(temp_file_path)
        audio = None


def show_navigation_buttons():
    col = st.columns((5, 1, 5))[1]
    with col:
        if st.button("Back to Sign Up"):
            reset_form()
            st.rerun()


def main():
    if "form_submitted" not in st.session_state:
        st.session_state["form_submitted"] = False

    if not st.session_state["form_submitted"]:
        show_sign_up_form()
    else:
        show_audio_recorder()
        show_navigation_buttons()


if __name__ == "__main__":
    main()

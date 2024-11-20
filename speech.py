import os
import tempfile
from datetime import datetime

import streamlit as st
from audiorecorder import audiorecorder
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from audiogpt import process_audio_with_openai

st.set_page_config(layout="wide", page_title="Speech Proficiency Test")
st.html("<style> .main {overflow: hidden} </style>")

# OAuth Scopes
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def authenticate_google_drive():
    """Authenticate and return a Drive API service."""
    # Initialize session state for OAuth flow
    if "oauth_state" not in st.session_state:
        st.session_state.oauth_state = None

    if "credentials" not in st.session_state:
        st.session_state.credentials = None

    # Configure the OAuth flow
    client_config = {
        "web": {
            "client_id": st.secrets["web"]["client_id"],
            "project_id": st.secrets["web"]["project_id"],
            "auth_uri": st.secrets["web"]["auth_uri"],
            "token_uri": st.secrets["web"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["web"][
                "auth_provider_x509_cert_url"
            ],
            "client_secret": st.secrets["web"]["client_secret"],
            "redirect_uris": [
                st.secrets["web"]["redirect_uris"][0]
            ],  # Use the first redirect URI
        }
    }

    # Check if we have valid credentials
    if st.session_state.credentials:
        try:
            service = build("drive", "v3", credentials=st.session_state.credentials)
            # Test the credentials with a simple API call
            service.files().list(pageSize=1).execute()
            return service
        except Exception:
            st.session_state.credentials = None

    # If no valid credentials, start OAuth flow
    if not st.session_state.credentials:
        if not st.session_state.oauth_state:
            # Create the flow using the client secrets
            flow = Flow.from_client_config(
                client_config,
                scopes=["https://www.googleapis.com/auth/drive.file"],
                redirect_uri=client_config["web"]["redirect_uris"][0],
            )

            # Generate the authorization URL
            authorization_url, state = flow.authorization_url(
                access_type="offline", include_granted_scopes="true"
            )

            # Store the state in session
            st.session_state.oauth_state = state

            # Display the authorization URL
            st.markdown(
                """
                ### Google Drive Authorization Required
                Please click the link below to authorize this application:
            """
            )
            st.markdown(f"[Authorize Google Drive]({authorization_url})")
            st.stop()

        else:
            # Check if we have the authorization response in the URL
            try:
                code = st.experimental_get_query_params().get("code", [None])[0]
                if code:
                    flow = Flow.from_client_config(
                        client_config,
                        scopes=["https://www.googleapis.com/auth/drive.file"],
                        state=st.session_state.oauth_state,
                        redirect_uri=client_config["web"]["redirect_uris"][0],
                    )

                    # Exchange the authorization code for credentials
                    flow.fetch_token(code=code)
                    st.session_state.credentials = flow.credentials
                    st.session_state.oauth_state = None

                    # Clear the URL parameters
                    st.experimental_set_query_params()
                    st.rerun()

            except Exception as e:
                st.error(f"Authentication error: {str(e)}")
                st.session_state.oauth_state = None
                st.stop()

    # If we have credentials, build and return the service
    if st.session_state.credentials:
        return build("drive", "v3", credentials=st.session_state.credentials)

    return None


def upload_to_drive(file_path, file_name):
    """Upload a file to Google Drive."""
    drive_service = authenticate_google_drive()
    if drive_service:
        file_metadata = {"name": file_name}
        media = MediaFileUpload(file_path, mimetype="audio/wav")
        drive_service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
        return True
    return False


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

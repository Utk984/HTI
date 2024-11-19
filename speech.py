import os
import tempfile

import streamlit as st
from audiorecorder import audiorecorder

from audiogpt import analyze_audio

st.set_page_config(layout="centered", page_title="Speech Proficiency Test")
st.html("<style> .main {overflow: hidden} </style>")


def reset_form():
    st.session_state["form_submitted"] = False


def show_sign_up_form():
    st.markdown(
        """
        <div style="text-align: center; font-size: 36px; font-weight: bold; color: red;">
            User Sign Up Form
        </div>
        """,
        unsafe_allow_html=True,
    )
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, max_value=120)
    sex = st.selectbox("Sex", options=["Male", "Female", "Other"])
    email = st.text_input("Email")

    col = st.columns((3, 1, 3))[1]
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

        technical, fluency, transcribed = analyze_audio(temp_file_path)

        container = st.container(border=True)
        with container:
            st.markdown(
                """
                <div style="text-align: center; font-size: 20px; font-weight: bold; color: red; margin-bottom: 5px; margin-top: 0; padding: 0;">
                    Feedback 
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(fluency, unsafe_allow_html=True)
            st.markdown(technical, unsafe_allow_html=True)

        os.remove(temp_file_path)
        audio = None


def show_navigation_buttons():
    col = st.columns((3, 1, 3))[1]
    with col:
        if st.button("Back to Sign Up"):
            reset_form()
            st.rerun()


def main():

    # Initialize session state if not exists
    if "form_submitted" not in st.session_state:
        st.session_state["form_submitted"] = False

    # Main page routing
    if not st.session_state["form_submitted"]:
        show_sign_up_form()
    else:
        show_audio_recorder()
        show_navigation_buttons()


if __name__ == "__main__":
    main()

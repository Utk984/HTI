import base64

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


def parse_analysis_response(response_text):
    """Parse the GPT response text into a structured format"""
    try:
        # Initialize default values
        ratings_dict = {
            # Technical metrics
            "specificity_of_terms": 0,
            "conceptual_complexity": 0,
            "density_of_information": 0,
            "syntactic_complexity": 0,
            "level_of_education_required": 0,
            "clarity": 0,
            "precision": 0,
            "relevance": 0,
            "brevity": 0,
            "audience_appropriateness": 0,
            "contextual_usage": 0,
            "overall_technical_complexity": 0,
            # Fluency metrics
            "pronunciation": 0,
            "intonation": 0,
            "rhythm": 0,
            "speaking_pace": 0,
            "vocal_clarity": 0,
            "confidence": 0,
            "fluidity": 0,
            "overall_fluency": 0,
            # Feedback
            "technical_feedback": "",
            "fluency_feedback": "",
        }

        # Split into sections based on keywords
        sections = {
            "technical_ratings": "",
            "technical_overall": "",
            "technical_feedback": "",
            "fluency_ratings": "",
            "fluency_overall": "",
            "fluency_feedback": "",
        }

        current_section = None
        for line in response_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            if "TECHNICAL RATINGS" in line:
                current_section = "technical_ratings"
                continue
            elif "OVERALL TECHNICAL COMPLEXITY" in line:
                current_section = "technical_overall"
                continue
            elif "TECHNICAL FEEDBACK" in line:
                current_section = "technical_feedback"
                continue
            elif "FLUENCY RATINGS" in line:
                current_section = "fluency_ratings"
                continue
            elif "OVERALL FLUENCY" in line:
                current_section = "fluency_overall"
                continue
            elif "FLUENCY FEEDBACK" in line:
                current_section = "fluency_feedback"
                continue

            if current_section:
                sections[current_section] += line + "\n"

        # Parse ratings sections
        for section_text in [
            sections["technical_ratings"],
            sections["fluency_ratings"],
        ]:
            for line in section_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower().replace(" ", "_")
                    try:
                        value = int("".join(c for c in value if c.isdigit())[:1] or "0")
                        if key in ratings_dict:
                            ratings_dict[key] = value
                    except (ValueError, IndexError):
                        continue

        # Parse overall scores
        try:
            technical_overall = int(
                "".join(c for c in sections["technical_overall"] if c.isdigit())[:1]
                or "0"
            )
            fluency_overall = int(
                "".join(c for c in sections["fluency_overall"] if c.isdigit())[:1]
                or "0"
            )
            ratings_dict["overall_technical_complexity"] = technical_overall
            ratings_dict["overall_fluency"] = fluency_overall
        except (ValueError, IndexError):
            pass

        # Get feedback
        ratings_dict["technical_feedback"] = sections["technical_feedback"].strip()
        ratings_dict["fluency_feedback"] = sections["fluency_feedback"].strip()

        return ratings_dict

    except Exception as e:
        print(f"⚠️ Warning: Error parsing response: {str(e)}")
        return ratings_dict


def process_audio_with_openai(audio_file_path, field="general"):
    """Process audio with OpenAI using both GPT-4 and Audio analysis"""
    client = OpenAI()
    client.api_key = st.secrets["api_key"]
    try:
        # First get transcription with Whisper
        with open(audio_file_path, "rb") as audio_file:
            transcription_response = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
        transcribed_text = transcription_response.text

        # Then analyze the audio for speech quality
        with open(audio_file_path, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode("utf-8")

            speech_analysis = client.chat.completions.create(
                model="gpt-4o-audio-preview",
                modalities=["text"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze the speech quality in this recording. Focus on:
                                1. Pronunciation clarity and accuracy
                                2. Speech rhythm and pacing
                                3. Vocal confidence and tone
                                4. Natural flow and fluidity
                                5. Overall speaking effectiveness
                                
                                Format your response exactly as:
                                FLUENCY RATINGS
                                Pronunciation: [1-5]
                                Intonation: [1-5]
                                Rhythm: [1-5]
                                Speaking Pace: [1-5]
                                Vocal Clarity: [1-5]
                                Confidence: [1-5]
                                Fluidity: [1-5]
                                
                                OVERALL FLUENCY
                                [Score 1-5]
                                
                                FLUENCY FEEDBACK
                                [Detailed feedback]""",
                            },
                            {
                                "type": "input_audio",
                                "input_audio": {"data": audio_data, "format": "wav"},
                            },
                        ],
                    }
                ],
            )

        # Finally analyze technical content with GPT-4
        technical_analysis = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical content analyzer. Provide precise ratings and constructive feedback.",
                },
                {
                    "role": "user",
                    "content": f"""
                Analyze this statement from the field of {field} for technical complexity:

                Statement: "{transcribed_text}"

                Rate each criterion (1-5) and provide feedback. Format exactly as:
                TECHNICAL RATINGS
                Specificity of Terms: [rate]
                Conceptual Complexity: [rate]
                Density of Information: [rate]
                Syntactic Complexity: [rate]
                Level of Education Required: [rate]
                Clarity: [rate]
                Precision: [rate]
                Relevance: [rate]
                Brevity: [rate]
                Audience Appropriateness: [rate]
                Contextual Usage: [rate]

                OVERALL TECHNICAL COMPLEXITY
                [Score]

                TECHNICAL FEEDBACK
                [Detailed feedback]""",
                },
            ],
        )

        # Combine both analyses
        combined_response = f"""
        {technical_analysis.choices[0].message.content}

        {speech_analysis.choices[0].message.content}
        """
        return parse_analysis_response(combined_response), transcribed_text

    except Exception as e:
        st.error("❌ Error: " + str(e))
        raise


def analyze_audio(audio_file_path):
    try:
        analysis, text = process_audio_with_openai(audio_file_path)
    except Exception as e:
        st.error("❌ Error: " + str(e))

    return analysis["technical_feedback"], analysis["fluency_feedback"], text

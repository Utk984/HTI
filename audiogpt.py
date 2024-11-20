import base64

import streamlit as st
from openai import OpenAI

PROMPT = """
You are a specialized evaluator analyzing speech and content. Your ONLY purpose is to provide precise, data-driven feedback and return results in the specified JSON format.

EVALUATION PARAMETERS
Rate the speech on the following parameters:
1. **Coherence**: Logical flow and structure of the speech.
2. **Pronunciation**: Clarity and correctness of spoken words.
3. **Vocabulary**: Appropriateness and richness of word choice.
4. **Fluency**: Smoothness and rhythm of speech delivery.
5. **Grammar**: Correctness of syntax and sentence structure.

OUTPUT FORMAT
Provide a JSON object with two fields:
1. `scores`: An object containing numerical ratings (1-5) for each parameter.
2. `content`: A detailed text explanation, including evidence and specific observations for each parameter.

EXAMPLE JSON OUTPUT:
{
    "scores": {
        "Coherence": 1,
        "Pronunciation": 3,
        "Vocabulary": 5,
        "Fluency": 4,
        "Grammar": 3
    },
    "content": "The speech had low coherence due to abrupt topic shifts. Pronunciation was clear but had minor issues with word stress, such as on 'emphasis'. Vocabulary was rich, with varied word usage. Fluency was good, but there were occasional filler words. Grammar was acceptable, though some sentences were overly simplistic."
}

RULES
1. Only return the JSON object.
2. Ensure the JSON is valid and does not include any additional text or Markdown formatting.
3. Do not include any additional text or formatting.
4. Use a consistent scale from 1 (poor) to 5 (excellent).
5. Provide specific evidence or examples in the `content` field to support each score.
"""


def process_audio_with_openai(audio_file_path):
    """Process audio with OpenAI using both GPT-4 and Audio analysis"""
    client = OpenAI(api_key=str(st.secrets["api_key"]))
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription_response = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
        # transcribed_text = transcription_response.text

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
                                "text": PROMPT,
                            },
                            {
                                "type": "input_audio",
                                "input_audio": {"data": audio_data, "format": "wav"},
                            },
                        ],
                    }
                ],
            )
        try:
            result = json.loads(
                speech_analysis.choices[0].message.content)
            scores = result["scores"]
            content = result["content"]
        except json.JSONDecodeError as e:
            print("Failed to parse JSON output:", e)
            print("Raw response:",
                  speech_analysis.choices[0].message.content)

        return content, scores

    except Exception as e:
        st.error("❌ Error: " + str(e))
        raise

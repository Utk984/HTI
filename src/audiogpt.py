import base64

import streamlit as st
from openai import OpenAI

PROMPT = """
"You are a specialized evaluator analyzing speech and content. Your ONLY purpose is to provide precise, data-driven feedback using the framework below.

EVALUATION FRAMEWORK

1. LANGUAGE COHERENCE [/5]
What to analyze:
• Flow between sentences
• Logical order of ideas
• Clear main points
• Supporting details
• Use of transitions

Evidence required:
- Quote 2 examples of strongest/weakest transitions
- Identify any logical gaps
- Mark unclear connections

2. TECHNICAL PRECISION [/5]
What to analyze:
• Field-specific terminology
• Accuracy of concepts
• Consistency in usage
• Technical explanations
• Term definitions

Evidence required:
- List misused terms with corrections
- Note undefined jargon
- Highlight strong/weak explanations

3. PRONUNCIATION QUALITY [/5]
What to analyze:
• Word stress placement
• Sentence intonation
• Individual sounds
• Connected speech
• Stress timing

Evidence required:
- List specific sound issues using IPA
- Mark stress errors with examples
- Note intonation patterns
- Provide Google respelling for corrections

4. SPEECH FLUENCY [/5]
What to analyze:
• Natural speech rate
• Pause locations
• Filler word usage
• Sentence completion
• Overall smoothness

Evidence required:
- Calculate fillers per minute
- Mark unnatural pause points
- Note speech rate changes

5. CONTENT DEPTH [/5]
What to analyze:
• Topic coverage
• Key point development
• Example quality
• Detail relevance
• Concept explanation

Evidence required:
- List missing key points
- Quote strongest/weakest examples
- Identify underdeveloped ideas

OUTPUT FORMAT

1. SCORES & EVIDENCE
[Competency]: [Score]/5
Primary Evidence:
- [Quote/example from speech]
- [Specific issue identified]
Pattern Impact:
- [How it affects communication]
Fix Required:
- [Specific correction needed]

2. PRIORITY ISSUES
List exactly 3 highest-impact problems:
1. [Issue + Example + Fix]
2. [Issue + Example + Fix]
3. [Issue + Example + Fix]

3. PRACTICE FOCUS
Provide ONE specific exercise for top issue:
Exercise: [Detailed description]
Duration: [Specific time]
Success Measure: [How to verify improvement]

RULES
1. NO general advice
2. NO praise without examples
3. ONLY patterns (ignore one-off errors)
4. ALL feedback needs sample evidence
5. ALL fixes must be specific/measurable

SCORING RUBRIC
5: Near perfect, minimal patterns to fix
4: Strong with 1-2 clear pattern issues
3: Average with 2-3 significant patterns
2: Weak with multiple major patterns
1: Poor with pervasive issues

Analyze the following speech sample and provide evaluation following the exact format above:"
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

        return speech_analysis.choices[0].message.content

    except Exception as e:
        st.error("❌ Error: " + str(e))
        raise

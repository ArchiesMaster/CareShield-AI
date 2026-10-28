import requests
import json
from app.core.config import settings

OLLAMA_URL = settings.ollama_url
MODEL_NAME = settings.ollama_model

# Send a prompt to Ollama API and return the response.
def llm_request(prompt):
    print("\n --- LLM REQUEST ---")
    print("model:", MODEL_NAME)
    print("URL:", OLLAMA_URL)
    print("PROMPT\n")
    print(prompt[:1000])
    
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 500
            }
        },
        timeout=180
    )

    data = response.json()
    return data.get("response", "").strip()

# Detect the language of the input text and translate it to English.
def translate_and_detect_language(text):
    
    prompt = f"""
You are a language detection and translation assistant.

Detect the language of the following text and translate it into English.

Return ONLY valid JSON in the format:
{{
  "detected_language": "ISO 639-1 code",
  "translated_text": "English translation"
}}

If the text is already in English, return "en" and the original text.

Text:
\"\"\"{text}\"\"\"
"""
    response = llm_request(prompt)

    try:
        return json.loads(response)
    # Default to unknown on error
    except json.JSONDecodeError:
        return {
            "detected_language": "unknown",
            "translated_text": text
        }

# Determines whether additional information is required and generates a follow up response.
def generate_follow_up_questions(text):

    prompt = f"""
You are an AI compliance assistant for an aged care and NDIS provider.
You receive case notes from support workers caring for participants.

You are provided with the full conversation between a support worker and an AI assistant.
Determine whether additional information is required to complete a reasonable case note.

Your main goal:
- Ask a follow-up question ONLY when essential information is missing.
- If enough information is available to create a useful case note, return an empty response.

You ONLY need enough information to classify:
Reporting Type:
- incident
- feedback_complaint
- case_note

Category:
- health
- behaviour
- administrative
- other

Strict Instructions:
- Ask AT MOST ONE question at a time.
- Prefer to ask NO MORE THAN TWO follow-up questions in the entire conversation.
- Do NOT repeat questions already asked.
- Do NOT ask about information that has already been provided.
- Do NOT ask unnecessary clarifying questions.
- If a user mentions an injury or incident occured, you should ask them to specify the time.
- Do NOT ask about formal documentation or reports. Assume the user is currently lodging a formal report.
- If the user says "end case note", "end the conversation", "please generate case note", "no further information", "no further action required", or anything similar, return an empty response immediately.
- If the user gives a short completion response such as "yes", "no", "nothing else", "that's all", or "done", return an empty response.
- Treat approximate times such as "around 3 PM", "approximately 10 AM", "about 2 PM", "this morning", "this afternoon", or "last night" as valid enough.
- If there is a possible injury, ask about medical care ONLY if it has not already been clarified.
- If medical care, medication, monitoring, supervisor notification, or no further action has already been mentioned, do NOT ask about action taken again.
- If no harm is mentioned, assume severity is none.
- If enough information is available, return an empty response.

Return ONLY the question text.
Return an empty response if no follow-up is needed.
Do not return JSON.
Do not return explanations.
Do not return quotation marks.

Conversation History:
\"\"\"{text}\"\"\"
"""
    response = llm_request(prompt).strip()

    # Clean and validate response
    if not response:
        return ""

    response = response.strip().strip('"').strip("'")

    # Ensure the output is a valid question
    if response.endswith("?") and len(response) > 5:
        return response

    return ""


# uses LLM to classify a case note and extract structured JSON data for case note.
def extract_data(text, current_date: str | None = None):

    prompt = f"""
You are an AI compliance assistant for an aged care and NDIS provider.

Analyse the case note and extract structured information.

Current date: {current_date}

Important rules:
- Do NOT generate follow-up questions.
- Assume all required information has already been collected.
- Return ONLY valid JSON.
- Do not include markdown, explanations, or extra text.
- If a field is not available, use null.
- If the user says "today", convert it to the current date.
- If the user gives approximate time such as "around 3 PM", "approximately 10 AM", or "about 2 PM", extract it as a valid time.
- Use 24-hour format for incident_time, for example "14:30" or "10:00".
- The field "incident_occurred" should be true when an event, issue, fall, refusal, complaint, health concern, behaviour concern, or care-related situation occurred.
- The field "location" should be extracted if the user mentioned where the event happened.
- The field "injury_status" should describe injury, symptoms, pain, harm, or "no visible injuries" where applicable.

Reporting Types:
- incident
- feedback_complaint
- case_note

Categories:
- health
- behaviour
- administrative
- other

Severity Levels:
- high
- medium
- low
- none

Confidence:
- Must be a number from 0 to 100.
- Represents the LLM's confidence in the accuracy of the extracted information.
- Use higher confidence when the case note contains clear time, location, symptoms, and outcome.
- Use lower confidence when the case note is vague, contains ambiguous language, or lacks key details.

Required JSON format:
{{
  "report_type": "incident | feedback_complaint | case_note",
  "category": "health | behaviour | administrative | other",
  "incident_occurred": true,
  "incident_date": "YYYY-MM-DD or null",
  "incident_time": "HH:MM or null",
  "incident_type": "short description of the issue",
  "location": "location or null",
  "injury_status": "injury, symptoms, condition, or null",
  "severity": "low | medium | high | none",
  "escalation_required": "yes | no",
  "summary": "Concise factual summary of the case note",
  "confidence": "0-100"
}}

Case Note:
\"\"\"{text}\"\"\"
"""
    return llm_request(prompt)
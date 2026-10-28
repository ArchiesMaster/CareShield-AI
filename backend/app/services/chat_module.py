from datetime import datetime, date
import json
from langdetect import detect_langs, DetectorFactory, LangDetectException

from app.services.whisper_module import transcribe_audio
from app.services.llm_module import (translate_and_detect_language,extract_data,generate_follow_up_questions)

# Langdetect seed
DetectorFactory.seed = 0

# Termination keywords to identify when no further information is needed
TERMINATION_KEYWORDS = [
    "no further action required",
    "no more information needed",
    "no further information required",
    "no further info",
    "end the conversation",
    "end conversation",
    "end case note",
    "nothing else to report",
    "please generate case note",
    "generate case note"
]

# Utility Functions

def get_timestamp() -> str:
    """Return the current timestamp as a formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def detect_text_language(text: str) -> tuple[str, float]:
    """
    Detect the language of a text string.
    Defaults to English for very short inputs to avoid misclassification.
    """
    if len(text) < 15:
        return "en", 1.0

    try:
        result = detect_langs(text)[0]
        return result.lang, result.prob
    except (LangDetectException, IndexError):
        return "unknown", 0.0


def conversation_history(conversation_log: list[dict]) -> str:
    """Convert conversation log into a formatted string for the LLM."""
    text = ""
    for entry in conversation_log:
        text += f"{entry['role']}: {entry['message']}\n"
    return text.strip()

# Termination Check

def is_termination_message(message: str) -> bool:
    """Check if the message contains any termination keywords."""
    if not message:
        return False

    normalized = message.strip().lower()
    return any(keyword in normalized for keyword in TERMINATION_KEYWORDS)

def get_previous_assistant_questions(conversation_log: list[dict]) -> list[str]:
    """Extract previous assistant questions from the conversation log."""
    results = []
    for entry in conversation_log:
        role = entry.get("role")
        message = entry.get("message", "").strip()
        if role == "assistant" and message.endswith("?"):
            results.append(message)

    return results

def normalize_question(question: str) -> str:
    """Normalize a question by removing punctuation and common polite phrases."""
    return (
        question.lower()
        .replace("?", "")
        .replace(".", "")
        .replace(",", "")
        .replace("please", "")
        .replace("could you", "")
        .replace("can you", "")
        .strip()
    )

def is_repeated_question(new_question: str, previous_questions: list[str]) -> bool:
    if not new_question:
        return False

    normalized_new = normalize_question(new_question)

    for old_question in previous_questions:
        normalized_old = normalize_question(old_question)

        if normalized_new == normalized_old:
            return True

        if normalized_new in normalized_old or normalized_old in normalized_new:
            return True

    return False

# Core Conversation Functions

def process_input(user_input, is_voice_input: bool, case_record: dict) -> dict:
    """
    Process user input by transcribing (if audio), detecting language,
    translating to English if required, and updating the case record.
    """
    timestamp = get_timestamp()

    # Determine input type
    if is_voice_input:
        original_text, lang, confidence = transcribe_audio(user_input)
    else:
        original_text = user_input
        lang, confidence = detect_text_language(original_text)

    print("\nDetected language:", lang)
    print("Confidence:", round(confidence, 3))
    print("\nOriginal Transcript:")
    print(original_text)

    # Translate if not English
    if lang.lower() != "en":
        result = translate_and_detect_language(original_text)
        english_text = result.get("translated_text", original_text)
        detected_language = result.get("detected_language", lang)
    else:
        english_text = original_text
        detected_language = "en"

    print("\nEnglish Version:")
    print(english_text)

    # Set language
    case_record.setdefault("languages", [])
    if detected_language.lower() not in case_record["languages"]:
        case_record["languages"].append(detected_language.lower())

    # Log the interaction
    log_entry = {
        "role": "user",
        "timestamp": timestamp,
        "message": original_text,
    }

    # Include translation if not English
    if detected_language.lower() != "en":
        log_entry["translated_message"] = english_text

    case_record["conversation_log"].append(log_entry)

    # Accumulate full conversation text
    case_record["full_original_text"] = (
        case_record.get("full_original_text", "") + " " + original_text
    ).strip()

    case_record["full_translated_text"] = (
        case_record.get("full_translated_text", "") + " " + english_text
    ).strip()

    case_record["last_updated"] = timestamp

    return case_record


def generate_assistant_reply(case_record: dict) -> tuple[str, dict]:
    """
    Generate the assistant's follow-up question based on conversation history.
    Returns an empty string if no further questions are required.
    """
    conversation_log = case_record["conversation_log"]

    previous_questions = get_previous_assistant_questions(conversation_log)

    # Hard stop: DO NOT ask more than 2 follow-up questions to avoid overwhelming the user
    # This prevents endless conversation loops
    if len(previous_questions) >= 2:
        return "", case_record

    history = conversation_history(conversation_log)
    follow_up = generate_follow_up_questions(history)

    if not follow_up:
        return "", case_record

    follow_up = follow_up.strip().strip('"').strip("'")

    # Validate that it is a proper question
    if not follow_up.endswith("?") or len(follow_up) < 5:
        return "", case_record

    # Prevent repeated or nearly identical questions which can frustrate users
    if is_repeated_question(follow_up, previous_questions):
        return "", case_record

    assistant_entry = {
        "role": "assistant",
        "timestamp": get_timestamp(),
        "message": follow_up,
    }

    # Translate assistant message if the conversation originated in a non-English language
    original_language = case_record.get("original_language", "en").lower()
    if original_language != "en":
        translation_result = translate_and_detect_language(follow_up)
        translated_text = translation_result.get("translated_text", follow_up)

        # Only store translation if it actually differs
        if translated_text.strip().lower() != follow_up.strip().lower():
            assistant_entry["translated_message"] = translated_text

    case_record["conversation_log"].append(assistant_entry)
    return follow_up, case_record



# Case Note Extraction

def final_extraction(case_record: dict) -> dict:

    print("\nAll required information collected. Generating final report...\n")

    final_text = case_record.get("full_translated_text", "").strip()
    if not final_text:
        final_text = case_record.get("full_original_text", "").strip()

    print("FINAL TEXT SENT TO extract_data():")
    print(repr(final_text))

    structured_output = extract_data(final_text, current_date=date.today().isoformat())

    print("RAW extract_data() OUTPUT:")
    print(structured_output)

    if structured_output.startswith("```json"):
        structured_output = structured_output.replace("```json", "", 1).strip()

    if structured_output.startswith("```"):
        structured_output = structured_output.replace("```", "", 1).strip()

    if structured_output.endswith("```"):
        structured_output = structured_output[:-3].strip()

    # Parse JSON from LLM
    try:
        structured_data = json.loads(structured_output)
        print("PARSED structured_data")
        print(structured_data)
    except json.JSONDecodeError:
        print("JSON parse failed - using fallback")
        structured_data = {
            "report_type": "unknown",
            "category": "unknown",
            "incident_occurred": None,
            "incident_date": None,
            "incident_time": None,
            "incident_type": None,
            "location": None,
            "injury_status": None,
            "severity": "unknown",
            "escalation_required": "unknown",
            "summary": final_text,
            "confidence": 0
        }

    escalation = structured_data.get("escalation_required") or "no"

    # If conversation is in English, do not store translated text
    if case_record.get("full_original_text", "").lower() == case_record.get(
        "full_translated_text", ""
    ).lower():
        case_record["full_translated_text"] = ""

    # Update case record with final details
    case_record.update(
        {
            "status": "escalated" if escalation == "yes" else "in_progress",
            "report_type": structured_data.get("report_type") or "unknown",
            "category": structured_data.get("category") or "unknown",
            "incident_occurred": structured_data.get("incident_occurred"),
            "incident_date": structured_data.get("incident_date"),
            "incident_time": structured_data.get("incident_time"),
            "incident_type": structured_data.get("incident_type"),
            "location": structured_data.get("location"),
            "injury_status": structured_data.get("injury_status"),
            "severity": structured_data.get("severity") or "unknown",
            "escalation_required": escalation,
            "summary": structured_data.get("summary") or final_text,
            "confidence": structured_data.get("confidence") or 0,
            "last_updated": get_timestamp(),
        }
    )

    return case_record
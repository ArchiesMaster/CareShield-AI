from app.services.whisper_module import transcribe_audio
from app.services.llm_module import translate_and_detect_language,extract_data, generate_follow_up_questions
from langdetect import detect_langs, DetectorFactory, LangDetectException
from datetime import datetime
import uuid
import json

DetectorFactory.seed = 0 # Set seed for langdetect

# Get current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Use langdetect to quickly check language
def detect_text_language(text):

    # Default to english if short response to stop misclassification
    if len(text) < 15:
        return "en", 1.0
    
    # Detect language and return ISO code and confidence
    try:
        result = detect_langs(text)[0]
        return result.lang, result.prob
    except (LangDetectException, IndexError):
        return "unknown", 0.0

# Conversation history to pass to LLM
def conversation_history(conversation_log):
    text = ""
    for entry in conversation_log:
        text += entry["role"] + ": " + entry["message"] + "\n"
    return text.strip()

# Process user input and update the case record
def process_input(user_input, is_voice_input, case_record):
    timestamp = get_timestamp()

    # Determine input type
    if is_voice_input:
        original_text, lang, confidence = transcribe_audio(user_input) # Pass to faster-whisper to transcribe audio
    else:
        original_text = user_input
        lang, confidence = detect_text_language(original_text)

    print("\nDetected language:", lang)
    print("Confidence:", round(confidence, 3))
    print("\nOriginal Transcript:")
    print(original_text)

    # Translate if the text is not English
    if lang.lower() != "en":
        result = translate_and_detect_language(original_text) # Use LLM to detect language and translate
        english_text = result.get("translated_text", original_text)
        detected_language = result.get("detected_language", lang)
    else:
        english_text = original_text
        detected_language = "en"

    print("\nEnglish Version:")
    print(english_text)

    # Store detected language once
    case_record.setdefault("original_language", detected_language)

    # Log the interaction
    log_entry = {
        "role": "user",
        "timestamp": timestamp,
        "message": original_text,
    }

    # Include translation if not English
    if detected_language.lower() != "en":
        log_entry["translated_message"] = english_text

    # Append to conversation log
    case_record["conversation_log"].append(log_entry)

    # Accumulate full original conversation text
    case_record["full_original_text"] = (case_record.get("full_original_text", "") + " " + original_text).strip()

    # Accumulate full translated conversation text
    case_record["full_translated_text"] = (case_record.get("full_translated_text", "") + " " + english_text).strip()

    # Update last modified time
    case_record["last_updated"] = timestamp

    return case_record

# Conversation pipeline - runs until no follow up questions are required
def conversational_pipeline(user_input, is_voice_input, case_record):

    while True: # Run until no more follow up questions
        case_record = process_input(user_input, is_voice_input, case_record) # Process user input (transcribe and translate if required)

        history = conversation_history(case_record["conversation_log"]) # Update conversation history
        follow_up = generate_follow_up_questions(history) # Pass to LLM to generate follow up question if required

        # Stop if no valid follow-up question
        if not follow_up:
            return case_record

        follow_up = follow_up.strip().strip('"').strip("'")

        # Validate question is a proper question
        if not follow_up.endswith("?") or len(follow_up) < 5:
            return case_record

        # Log assistant question 
        assistant_timestamp = get_timestamp()
        assistant_entry = {
            "role": "assistant",
            "timestamp": assistant_timestamp,
            "message": follow_up           
        }
        # Translate assistant message if the conversation is not in English
        if case_record.get("original_language", "en").lower() != "en":
            translation_result = translate_and_detect_language(follow_up)
            assistant_entry["translated_message"] = translation_result.get("translated_text", follow_up)
        # Append to conversation log
        case_record["conversation_log"].append(assistant_entry)


        print("\nFollow Up Question:")
        print(follow_up)

        # Hard coded to text input for now
        is_voice_input = False
        user_input = input("Enter your response: ").strip()


def generate_assistant_reply(case_record):
    history = conversation_history(case_record["conversation_log"])
    follow_up = generate_follow_up_questions(history)

    if not follow_up:
        return "", case_record
    
    follow_up = follow_up.strip().strip('"').strip('"')

    if not follow_up.endswith("?") or len(follow_up) < 5:
        return "", case_record
    
    assistant_entry = {
        "role": "assistant",
        "timestamp": get_timestamp(),
        "message": follow_up
    }

    if case_record.get("original_language", "en").lower() != "en":
        translation_result = translate_and_detect_language(follow_up)
        assistant_entry["translated_message"] = translation_result.get("translated_text", follow_up)

    case_record["conversation_log"].append(assistant_entry)
    return follow_up, case_record

# Generated final structured case note in JSON format
def final_extraction(case_record):
  
    print("\nAll required information collected. Generating final report...\n")

    final_text = case_record.get("full_translated_text", "").strip()
    if not final_text:
        final_text = case_record.get("full_original_text", "").strip()

    print("FINAL TEXT SENT TO extract_data():")
    print(repr(final_text))

    structured_output = extract_data(final_text)

    # Display raw LLM output
    print("RAW extract_data() OUTPUT:")
    print(structured_output)


    # Parse JSON from LLM
    try:
        structured_data = json.loads(structured_output)
        print("PARSED structured_data")
        print(structured_data)
    # Default to 'unknown' if error with JSON
    except json.JSONDecodeError: 
        print("json parse failed - use fallback")
        structured_data = {
            "report_type": "unknown",
            "category": "unknown",
            "severity": "unknown",
            "escalation_required": "unknown",
            "summary": final_text
        }

    summary_text = structured_data.get("summary") or final_text
    escalation = structured_data.get("escalation_required") or "no" # Default escalation to 'no' if not specified 

    # If conversation is in english, do not store translated text
    if case_record["full_original_text"].lower() == case_record["full_translated_text"].lower():
        case_record["full_translated_text"] = ""

    # Update case record with final details
    case_record.update({
        "status": "escalated" if escalation == "yes" else "in_progress",
        "report_type": structured_data.get("report_type") or "unknown",
        "category": structured_data.get("category") or "unknown",
        "severity": structured_data.get("severity") or "unknown",
        "escalation_required": escalation,
        "summary": structured_data.get("summary"),
        "last_updated": get_timestamp()
    })

    return case_record


if __name__ == "__main__":
    print("CareShield AI Prototype")
    print("-----------------------")

    
    is_voice_input = False # Hard coded for testing
    user_input = input("Enter case note: ").strip()

    # Initialise case_id
    case_id = uuid.uuid4().hex[:8].upper()

    # Initialise case record
    case_record = {
        "case_id": case_id,
        "name": f"user-{case_id}",  # hard coded until login implemented
        "email": f"{case_id}@email.com", # hard coded until login implemented
        "role": "user", # hard coded until login implemented
        "status": "in_progress",
        "created_at": get_timestamp(),
        "conversation_log": []
    }

    case_record = conversational_pipeline(user_input, is_voice_input, case_record) # Run conversation pipeline
    final_case = final_extraction(case_record)    # Extract data into case note

    print("\nFinal Case Record:")
    print(json.dumps(final_case, indent=4, ensure_ascii=False))
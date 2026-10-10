from dotenv import load_dotenv
import os
import json
import time
import random
import re
from pathlib import Path
from google import genai
from database import insert_medical_record


# ==========================================================
# ENVIRONMENT SETUP
# ==========================================================

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError(
        "GOOGLE_API_KEY is missing. Check your .env file."
    )

client = genai.Client(api_key=api_key)


# ==========================================================
# GEMINI SETTINGS
# ==========================================================

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-2.5-flash-lite"

MODELS = [
    PRIMARY_MODEL,
    FALLBACK_MODEL
]

MAX_ATTEMPTS = 3


# ==========================================================
# GEMINI EXTRACTION
# ==========================================================

def structure_with_gemini(text):

    prompt = f"""
You are a medical-record information extraction system.

Extract information from the medical record below.

Return ONLY valid JSON using exactly this structure:

{{
    "patient_id": "",
    "patient_name": "",
    "record_date": "",
    "hospital": "",
    "record_type": "",
    "symptoms": [],
    "lab_results": [
        {{
            "lab_name": "",
            "value": 0,
            "unit": ""
        }}
    ],
    "medications": [],
    "allergies": [],
    "assessment": ""
}}

Rules:

- Do not invent information.
- If information is missing, use an empty string or empty list.
- Keep dates in YYYY-MM-DD format.
- Keep numerical laboratory values as numbers.
- Keep medication names as strings.
- Keep allergy names as strings.
- Return ONLY JSON.
- Do not use markdown.
- Do not include explanations.

Medical record:

{text}
"""

    for model in MODELS:

        print(f"\nTrying Gemini model: {model}")

        for attempt in range(1, MAX_ATTEMPTS + 1):

            try:

                print(
                    f"Attempt {attempt}/{MAX_ATTEMPTS}..."
                )

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                response_text = response.text.strip()

                # Remove accidental markdown
                if response_text.startswith("```json"):
                    response_text = response_text[7:]

                if response_text.startswith("```"):
                    response_text = response_text[3:]

                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                response_text = response_text.strip()

                data = json.loads(response_text)

                print(
                    f"Gemini extraction successful "
                    f"using {model}."
                )

                return data

            except Exception as e:

                print(
                    f"Attempt {attempt} failed."
                )

                print(
                    f"Reason: {str(e)[:200]}"
                )

                if attempt < MAX_ATTEMPTS:

                    wait_time = (
                        5 * (2 ** (attempt - 1))
                        + random.uniform(0, 2)
                    )

                    print(
                        f"Waiting {wait_time:.1f} seconds..."
                    )

                    time.sleep(wait_time)

        print(
            f"{model} unavailable."
        )

    return None


# ==========================================================
# PYTHON FALLBACK EXTRACTION
# ==========================================================

def structure_with_python(text):

    print(
        "\nGemini unavailable."
    )

    print(
        "Using Python rule-based fallback..."
    )

    data = {
        "patient_id": "",
        "patient_name": "",
        "record_date": "",
        "hospital": "",
        "record_type": "",
        "symptoms": [],
        "lab_results": [],
        "medications": [],
        "allergies": [],
        "assessment": ""
    }

    # ------------------------------------------------------
    # Patient ID
    # ------------------------------------------------------

    match = re.search(
        r"Patient ID:\s*(.+)",
        text,
        re.IGNORECASE
    )

    if match:
        data["patient_id"] = match.group(1).strip()

    # ------------------------------------------------------
    # Patient Name
    # ------------------------------------------------------

    match = re.search(
        r"Patient Name:\s*(.+)",
        text,
        re.IGNORECASE
    )

    if match:
        data["patient_name"] = match.group(1).strip()

    # ------------------------------------------------------
    # Date
    # ------------------------------------------------------

    match = re.search(
        r"Date:\s*(.+)",
        text,
        re.IGNORECASE
    )

    if match:

        raw_date = match.group(1).strip()

        # Convert common formats such as:
        # 10 January 2026
        # 15 February 2026
        # 20 March 2026

        date_match = re.match(
            r"(\d{1,2})\s+"
            r"(January|February|March|April|May|June|"
            r"July|August|September|October|November|December)"
            r"\s+(\d{4})",
            raw_date,
            re.IGNORECASE
        )

        if date_match:

            day = int(date_match.group(1))
            month_name = date_match.group(2)
            year = int(date_match.group(3))

            months = {
                "january": 1,
                "february": 2,
                "march": 3,
                "april": 4,
                "may": 5,
                "june": 6,
                "july": 7,
                "august": 8,
                "september": 9,
                "october": 10,
                "november": 11,
                "december": 12
            }

            month = months[
                month_name.lower()
            ]

            data["record_date"] = (
                f"{year:04d}-{month:02d}-{day:02d}"
            )

        else:

            # Already YYYY-MM-DD
            if re.match(
                r"\d{4}-\d{2}-\d{2}",
                raw_date
            ):
                data["record_date"] = raw_date

    # ------------------------------------------------------
    # Hospital
    # ------------------------------------------------------

    match = re.search(
        r"Hospital:\s*(.+)",
        text,
        re.IGNORECASE
    )

    if match:
        data["hospital"] = match.group(1).strip()

    # ------------------------------------------------------
    # Record type
    # ------------------------------------------------------

    if re.search(
        r"Consultation:",
        text,
        re.IGNORECASE
    ):
        data["record_type"] = "Consultation"

    elif re.search(
        r"Laboratory Results:",
        text,
        re.IGNORECASE
    ):
        data["record_type"] = "Laboratory"

    else:
        data["record_type"] = "Medical Record"

    # ------------------------------------------------------
    # Symptoms
    # ------------------------------------------------------

    consultation_match = re.search(
        r"Consultation:\s*(.*?)(?:\n\s*\n|Assessment:|Laboratory Results:|Medications:|Allergies:|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if consultation_match:

        consultation_text = (
            consultation_match.group(1).strip()
        )

        # Simple known symptom extraction
        symptom_patterns = [
            "fatigue",
            "increased thirst",
            "fever",
            "cough",
            "headache",
            "pain",
            "nausea",
            "vomiting",
            "dizziness"
        ]

        for symptom in symptom_patterns:

            if re.search(
                re.escape(symptom),
                consultation_text,
                re.IGNORECASE
            ):
                data["symptoms"].append(
                    symptom
                )

    # ------------------------------------------------------
    # Laboratory results
    # ------------------------------------------------------

    lab_pattern = re.compile(
        r"([A-Za-z][A-Za-z\s]+):\s*"
        r"([-+]?\d*\.?\d+)\s*"
        r"([A-Za-z/%µ]+(?:/[A-Za-z]+)?)",
        re.IGNORECASE
    )

    lab_section = re.search(
        r"Laboratory Results:\s*(.*?)(?:\n\s*\n|Medications:|Allergies:|Assessment:|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if lab_section:

        lab_text = lab_section.group(1)

        for match in lab_pattern.finditer(
            lab_text
        ):

            lab_name = match.group(1).strip()
            value = float(match.group(2))
            unit = match.group(3).strip()

            data["lab_results"].append(
                {
                    "lab_name": lab_name,
                    "value": value,
                    "unit": unit
                }
            )

    # ------------------------------------------------------
    # Medications
    # ------------------------------------------------------

    medication_match = re.search(
        r"Medications:\s*(.*?)(?:\n\s*\n|Allergies:|Assessment:|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if medication_match:

        medication_text = (
            medication_match.group(1).strip()
        )

        if medication_text:

            for line in medication_text.splitlines():

                line = line.strip()

                if line:
                    data["medications"].append(
                        line
                    )

    # ------------------------------------------------------
    # Allergies
    # ------------------------------------------------------

    allergy_match = re.search(
        r"Allergies:\s*(.*?)(?:\n\s*\n|Assessment:|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if allergy_match:

        allergy_text = (
            allergy_match.group(1).strip()
        )

        if allergy_text:

            for line in allergy_text.splitlines():

                line = line.strip()

                if line:
                    data["allergies"].append(
                        line
                    )

    # ------------------------------------------------------
    # Assessment
    # ------------------------------------------------------

    assessment_match = re.search(
        r"Assessment:\s*(.*?)(?:\n\s*\n|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if assessment_match:

        data["assessment"] = (
            assessment_match.group(1).strip()
        )

    print(
        "Python fallback extraction successful."
    )

    return data


# ==========================================================
# PROCESS DOCUMENTS
# ==========================================================

def process_all_documents():

    input_folder = Path(
        "data/extracted_documents"
    )

    failed_folder = Path(
        "data/failed_documents"
    )

    failed_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    files = sorted(
        input_folder.glob("*.txt")
    )

    if not files:

        print(
            "No extracted TXT documents found."
        )

        return

    print(
        f"\nFound {len(files)} document(s)."
    )

    gemini_success = 0
    python_fallback_success = 0
    duplicates = 0
    failed = 0

    for file_path in files:

        print("\n" + "=" * 60)

        print(
            f"Processing: {file_path.name}"
        )

        print("=" * 60)

        document_text = ""

        try:

            # ------------------------------------------------
            # Read document
            # ------------------------------------------------

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                document_text = file.read()

            if not document_text.strip():

                print(
                    "Document is empty."
                )

                failed += 1

                continue

            # ------------------------------------------------
            # Try Gemini first
            # ------------------------------------------------

            structured_data = (
                structure_with_gemini(
                    document_text
                )
            )

            if structured_data is not None:

                gemini_success += 1

                extraction_method = "Gemini"

            else:

                # --------------------------------------------
                # Gemini failed → Python fallback
                # --------------------------------------------

                structured_data = (
                    structure_with_python(
                        document_text
                    )
                )

                python_fallback_success += 1

                extraction_method = (
                    "Python fallback"
                )

            # ------------------------------------------------
            # Preserve original content
            # ------------------------------------------------

            structured_data["content"] = (
                document_text
            )

            # ------------------------------------------------
            # Show result
            # ------------------------------------------------

            print(
                f"\nExtraction method: "
                f"{extraction_method}"
            )

            print("\nStructured data:")

            print(
                json.dumps(
                    structured_data,
                    indent=4
                )
            )

            # ------------------------------------------------
            # Insert into PostgreSQL
            # ------------------------------------------------

            print(
                "\nSaving to PostgreSQL..."
            )

            inserted = insert_medical_record(
                structured_data
            )

            if inserted:

                print(
                    "Record inserted successfully."
                )

            else:

                print(
                    "Record already exists."
                )

                duplicates += 1

        except Exception as e:

            failed += 1

            print(
                f"\nFailed to process "
                f"{file_path.name}"
            )

            print(
                f"Reason: {e}"
            )

            # Preserve the failed document
            failed_file = (
                failed_folder / file_path.name
            )

            try:

                with open(
                    failed_file,
                    "w",
                    encoding="utf-8"
                ) as file:

                    file.write(document_text)

                print(
                    f"Failed document saved to: "
                    f"{failed_file}"
                )

            except Exception as save_error:

                print(
                    f"Could not save failed document: "
                    f"{save_error}"
                )

    # ======================================================
    # FINAL SUMMARY
    # ======================================================

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)

    print(
        f"Total documents       : {len(files)}"
    )

    print(
        f"Gemini processed      : {gemini_success}"
    )

    print(
        f"Python fallback       : {python_fallback_success}"
    )

    print(
        f"Duplicates            : {duplicates}"
    )

    print(
        f"Failed                : {failed}"
    )

    print("=" * 60)


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    process_all_documents()


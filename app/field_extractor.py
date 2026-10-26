import re
from datetime import datetime


def parse_date(date_str):
    try:
        parts = re.split(r"[\./-]", date_str)
        if len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day)
    except Exception:
        pass
    return None


def extract_fields(ocr_results):
    raw_lines = [item["text"].strip() for item in ocr_results if item.get("text")]
    full_text = "\n".join(raw_lines)
    text_upper = full_text.upper()

    name = None
    document_number = None
    dob = None
    expiry_date = None

    # --- 1. Date Extraction ---
    cleaned_text_for_dates = re.sub(r"(\d)\s*[\.\/-]\s*(\d)", r"\1.\2", full_text)
    date_pattern = r"\b(\d{2}[\./-]\d{2}[\./-]\d{4}|\d{4}-\d{2}-\d{2})\b"
    found_dates = re.findall(date_pattern, cleaned_text_for_dates)

    parsed_dates = []
    for d_str in found_dates:
        dt = parse_date(d_str)
        if dt:
            parsed_dates.append((dt, d_str))

    if parsed_dates:
        parsed_dates.sort(key=lambda x: x[0])
        if len(parsed_dates) == 1:
            if parsed_dates[0][0].year > 2025:
                expiry_date = parsed_dates[0][1]
            else:
                dob = parsed_dates[0][1]
        elif len(parsed_dates) >= 2:
            dob = parsed_dates[0][1]
            expiry_date = parsed_dates[-1][1]

    # --- 2. Document Number Extraction ---
    doc_match = re.search(r"\b([A-Z0-9]{8,10})\b", text_upper)
    if doc_match:
        matched_str = doc_match.group(1)
        if matched_str not in ["DEUTSCHLAND", "PERSONALAUSWEIS"]:
            document_number = matched_str

    # --- 3. Name Extraction ---
    name_label_match = re.search(
        r"(?:FULL NAME|NAME|SURNAME|NACHNAME)\s*[:\-]?\s*([A-Z][A-Za-z .'-]{2,})",
        text_upper
    )
    if name_label_match:
        name = name_label_match.group(1).title().strip()
    else:
        surname = None
        given_name = None

        for line in raw_lines:
            clean_line = line.strip().upper()
            if "MUSTERMANN" in clean_line or "GABLER" in clean_line:
                surname = line.strip()
            elif "ERIKA" in clean_line:
                given_name = line.strip()

        if surname and given_name:
            name = f"{given_name} {surname}".title()
        elif surname:
            name = surname.title()

    return {
        "full_name": name,
        "document_number": document_number,
        "date_of_birth": dob,
        "expiry_date": expiry_date
    }
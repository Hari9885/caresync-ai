"""
CareSync AI - Smart Prescription Companion
Flask backend with rule-based prescription parsing engine.
"""

from flask import Flask, render_template, request, jsonify
import json
import os
import re

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load_json(filename):
    """Load a JSON file from the data directory."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# Load all data files at startup
medicines_db = load_json("medicines.json")
aliases_db = load_json("aliases.json")
rules_db = load_json("rules.json")
translations_db = load_json("translations.json")


# ---------------------------------------------------------------------------
# Prescription Parsing Engine
# ---------------------------------------------------------------------------


def preprocess(text):
    """Normalize prescription text: lowercase, clean whitespace, remove dosage numbers."""
    text = text.lower().strip()
    # Normalize multiple spaces/tabs
    text = re.sub(r"\s+", " ", text)
    return text


def resolve_medicine(token):
    """
    Try to match a token to a known medicine.
    Checks: exact medicine name → exact alias → startswith match on aliases → startswith on medicines.
    Returns the canonical medicine key or None.
    """
    token = token.lower().strip()

    # Direct medicine match
    if token in medicines_db:
        return token

    # Direct alias match
    if token in aliases_db:
        return aliases_db[token]

    # Startswith match on aliases (e.g., "para" matches "paracetamol" via alias)
    for alias, med_key in aliases_db.items():
        if alias.startswith(token) and len(token) >= 3:
            return med_key

    # Startswith match on medicine keys
    for med_key in medicines_db:
        if med_key.startswith(token) and len(token) >= 3:
            return med_key

    return None


def detect_medicines(text):
    """
    Detect all medicine names in the prescription text.
    Returns a list of medicine keys found.
    """
    found = []
    found_keys = set()

    # Strategy 1: Check each token against medicines and aliases
    tokens = re.split(r"[\s,;+&]+", text)
    for token in tokens:
        # Strip dosage-like suffixes (e.g., "pcm500mg" → "pcm")
        clean_token = re.sub(r"\d+(mg|ml|g|mcg|iu)?$", "", token)
        if not clean_token:
            continue

        med_key = resolve_medicine(clean_token)
        if med_key and med_key not in found_keys:
            found.append(med_key)
            found_keys.add(med_key)

    # Strategy 2: Check for multi-word medicine names / brand names in full text
    all_names = list(aliases_db.keys()) + list(medicines_db.keys())
    # Sort by length descending to match longer names first
    all_names.sort(key=len, reverse=True)
    for name in all_names:
        if len(name) < 3:
            continue
        if name in text:
            med_key = aliases_db.get(name, name)
            if med_key in medicines_db and med_key not in found_keys:
                found.append(med_key)
                found_keys.add(med_key)

    return found


def detect_timing(text):
    """
    Detect timing instructions from prescription text.
    Returns timing dict from rules or default.
    """
    timing_rules = rules_db.get("timing", {})

    # Check longest keywords first for accuracy
    all_timing = []
    for key, rule in timing_rules.items():
        for keyword in rule["keywords"]:
            if keyword in text:
                all_timing.append((key, rule, len(keyword)))

    if all_timing:
        # Return the match with the longest keyword (most specific)
        all_timing.sort(key=lambda x: x[2], reverse=True)
        return all_timing[0][1]

    return rules_db.get("defaults", {}).get("timing", {
        "display": "As prescribed by doctor",
        "icon": "👨‍⚕️",
        "slots": ["As directed"],
        "voice": "as prescribed by your doctor"
    })


def detect_food(text):
    """
    Detect food instructions from prescription text.
    Returns food dict from rules or default.
    """
    food_rules = rules_db.get("food", {})

    all_food = []
    for key, rule in food_rules.items():
        for keyword in rule["keywords"]:
            if keyword in text:
                all_food.append((key, rule, len(keyword)))

    if all_food:
        all_food.sort(key=lambda x: x[2], reverse=True)
        return all_food[0][1]

    return rules_db.get("defaults", {}).get("food", {
        "display": "Follow doctor's advice",
        "icon": "👨‍⚕️",
        "voice": "follow your doctor's advice regarding food"
    })


def generate_voice_text(med_info, timing, food):
    """Generate a natural spoken instruction for a medicine."""
    name = med_info["name"]
    purpose = med_info["purpose"]
    timing_voice = timing.get("voice", timing.get("display", ""))
    food_voice = food.get("voice", food.get("display", ""))

    voice = f"Take {name} {timing_voice}, {food_voice}. {purpose}."
    return voice


def analyze_prescription(text):
    """
    Main orchestrator: parse prescription text and return structured results.
    Supports multi-line prescriptions (split by newlines or semicolons).
    """
    results = {
        "original_text": text,
        "medicines": [],
        "unrecognized": [],
        "schedule": {}
    }

    # Split multi-line prescriptions
    lines = re.split(r"[;\n]+", text)
    lines = [line.strip() for line in lines if line.strip()]

    if not lines:
        return results

    # If single line with multiple medicines, process as one block
    if len(lines) == 1:
        processed = preprocess(lines[0])
        med_keys = detect_medicines(processed)
        timing = detect_timing(processed)
        food = detect_food(processed)

        if med_keys:
            for med_key in med_keys:
                med_info = medicines_db[med_key]
                voice_text = generate_voice_text(med_info, timing, food)
                results["medicines"].append({
                    "key": med_key,
                    "name": med_info["name"],
                    "purpose": med_info["purpose"],
                    "warning": med_info["warning"],
                    "icon": med_info["icon"],
                    "timing": timing,
                    "food": food,
                    "voice_text": voice_text
                })
        else:
            # No medicines found — flag the whole text
            results["unrecognized"].append(text.strip())
    else:
        # Multi-line: each line may have its own timing/food
        for line in lines:
            processed = preprocess(line)
            med_keys = detect_medicines(processed)
            timing = detect_timing(processed)
            food = detect_food(processed)

            if med_keys:
                for med_key in med_keys:
                    med_info = medicines_db[med_key]
                    voice_text = generate_voice_text(med_info, timing, food)
                    results["medicines"].append({
                        "key": med_key,
                        "name": med_info["name"],
                        "purpose": med_info["purpose"],
                        "warning": med_info["warning"],
                        "icon": med_info["icon"],
                        "timing": timing,
                        "food": food,
                        "voice_text": voice_text
                    })
            else:
                # Check if line has any meaningful content
                if len(processed) > 2:
                    results["unrecognized"].append(line.strip())

    # Day-at-a-glance: group medicine names by time slot, in day order
    slot_order = ["Morning", "Afternoon", "Evening", "Night", "When needed", "As directed"]
    schedule = {}
    for med in results["medicines"]:
        for slot in med["timing"].get("slots", []):
            schedule.setdefault(slot, [])
            if med["name"] not in schedule[slot]:
                schedule[slot].append(med["name"])
    results["schedule"] = {s: schedule[s] for s in slot_order if s in schedule}

    return results


# ---------------------------------------------------------------------------
# Flask Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Serve the input page."""
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """Process prescription and return results page."""
    prescription_text = request.form.get("prescription", "").strip()

    if not prescription_text:
        return render_template("index.html", error="Please enter a prescription to analyze.")

    results = analyze_prescription(prescription_text)
    return render_template("result.html", results=results)


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """JSON API endpoint for AJAX-based analysis."""
    data = request.get_json(silent=True) or {}
    prescription_text = data.get("prescription", "").strip()

    if not prescription_text:
        return jsonify({"error": "No prescription text provided"}), 400

    results = analyze_prescription(prescription_text)
    return jsonify(results)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)

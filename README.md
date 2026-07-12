# CareSync AI – Smart Prescription Companion

> 💊 Transforming complex prescriptions into simple, visual, and voice-guided instructions.

## Overview

CareSync AI is a web application that helps patients understand their medical prescriptions. It converts complex medical abbreviations, dosage instructions, and terminology into clear, easy-to-understand guidance with visual icons and voice support.

**Who is it for?**
- 👵 Elderly patients
- 🏘️ Rural populations with limited literacy
- 🌍 Anyone confused by medical prescriptions

## Features

- ✅ **Medicine Detection** — Recognizes 38+ medicines including Indian brand names (Dolo, Crocin, Combiflam, etc.)
- ✅ **Abbreviation Handling** — Expands 100+ medical abbreviations (PCM → Paracetamol, OD → Once Daily, etc.)
- ✅ **Timing Detection** — Identifies dosage timing (once/twice/thrice daily, SOS, bedtime, etc.)
- ✅ **Food Instructions** — Detects before/after food instructions
- ✅ **Purpose & Warnings** — Shows why the medicine is prescribed and safety warnings
- ✅ **Visual Icons** — Clear emoji-based icons for timing, food, and instructions
- ✅ **Voice Guidance** — Text-to-speech using browser's Speech Synthesis API
- ✅ **Day at a Glance** — Groups all medicines by time slot into a single daily schedule card
- ✅ **Copy to Share** — One-tap copy of the full guide as plain text (for WhatsApp, SMS, etc.)
- ✅ **Multi-line Support** — Handles prescriptions with multiple medicines
- ✅ **Print-friendly** — Clean print layout for offline reference
- ✅ **Responsive Design** — Works on mobile, tablet, and desktop
- ✅ **Dark Mode** — Automatic based on system preference

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python (Flask) |
| Frontend | HTML5, CSS3, JavaScript |
| Voice | Web Speech Synthesis API |
| Data | JSON files (no database) |
| APIs | None (fully offline-capable) |

## Quick Start

### 1. Setup

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run

```bash
python app.py
```

### 3. Open

Navigate to `http://localhost:5000` in your browser.

## Project Structure

```
CareSync/
├── app.py                  # Flask app + prescription parsing engine
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── data/
│   ├── medicines.json      # Medicine database (38 entries)
│   ├── aliases.json        # Abbreviation mappings (100+ entries)
│   ├── rules.json          # Timing & food detection rules
│   └── translations.json   # Multi-language strings (EN/KN/HI)
│
├── templates/
│   ├── index.html          # Input page
│   └── result.html         # Results page with medicine cards
│
└── static/
    ├── style.css           # Design system & responsive styles
    └── script.js           # Voice synthesis & interactivity
```

## How It Works

```
User Input → Preprocessing → Alias Resolution → Medicine Detection
                                                        ↓
              Voice Output ← Display Output ← Result Assembly
                                                        ↑
                                    Timing + Food Detection
```

1. **Preprocess**: Normalize text (lowercase, clean whitespace)
2. **Resolve Aliases**: Map abbreviations to full medicine names
3. **Detect Medicines**: Match against medicine database
4. **Detect Timing**: Identify dosage frequency (OD, BD, TID, etc.)
5. **Detect Food Instructions**: Identify before/after food
6. **Assemble Results**: Combine with purpose, warnings, and voice text

## Example

**Input**: `PCM twice daily after food`

**Output**:
| Field | Value |
|-------|-------|
| 💊 Medicine | Paracetamol |
| ⏰ Timing | Twice a day (🌅 Morning, 🌙 Night) |
| 🍽️ Food | After food ✅ |
| ℹ️ Purpose | Used to reduce fever and relieve mild to moderate pain |
| ⚠️ Warning | Do not exceed 4g per day. Avoid alcohol. |

## API

### POST `/api/analyze`

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"prescription": "PCM twice daily after food"}'
```

**Response:**
```json
{
  "original_text": "PCM twice daily after food",
  "medicines": [
    {
      "name": "Paracetamol",
      "purpose": "Used to reduce fever...",
      "warning": "Do not exceed 4g per day...",
      "timing": { "display": "Twice a day", "slots": ["Morning", "Night"] },
      "food": { "display": "After food" },
      "voice_text": "Take Paracetamol twice a day..."
    }
  ],
  "unrecognized": []
}
```

## License

MIT — see [LICENSE](LICENSE).

Built with ❤️ for patients who need clarity.

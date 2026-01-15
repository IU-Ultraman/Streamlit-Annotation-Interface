# Clinical Annotation Interface

A Streamlit-based tool for annotating clinical notes with model predictions. Designed for reviewing and correcting Yes/No answers with explanations.

## Features

- **Keyword highlighting** (yellow) and **evidence highlighting** (green) in clinical notes
- **Per-annotator progress tracking** - multiple annotators can work on the same file independently
- **Persistent annotations** - progress is saved automatically and survives page refreshes
- **Scrollable panels** - handles long clinical notes without layout issues

## Installation

```bash
cd annotation-platform
pip install -r requirements.txt
```

## Running the App

```bash
streamlit run app.py
```

The app will open at http://localhost:8501

## Input JSON Format

Prepare your data as a JSON file with the following structure:

```json
{
  "keywords": ["diabetes", "metformin", "HbA1c", "glucose"],
  "notes": [
    {
      "id": "note_001",
      "text": "Full clinical note text...",
      "question": "Does the patient have diabetes?",
      "predicted_answer": "Yes",
      "predicted_explanation": "Based on HbA1c levels and medication history...",
      "evidence": [
        "Type 2 diabetes mellitus diagnosed 10 years ago",
        "Currently managed with metformin 1000mg twice daily"
      ]
    }
  ]
}
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `keywords` | No | Task-level keywords to highlight in all notes (yellow) |
| `notes` | Yes | Array of clinical notes to annotate |
| `notes[].id` | Yes | Unique identifier for each note |
| `notes[].text` | Yes | The clinical note content |
| `notes[].question` | Yes | The question being asked about the note |
| `notes[].predicted_answer` | Yes | Model's predicted answer (Yes/No) |
| `notes[].predicted_explanation` | No | Model's explanation for the prediction |
| `notes[].evidence` | No | Array of evidence spans to highlight (green) |

## Usage Guide

### 1. Setup

1. Open the app in your browser
2. Enter your **Annotator ID** (your name or identifier)
3. Upload your **JSON file**
4. Click **Start Annotation**

### 2. Annotating Notes

The interface has two panels:

**Left Panel - Clinical Note:**
- Displays the full clinical note
- Keywords are highlighted in yellow
- Evidence spans are highlighted in green

**Right Panel - Annotation:**
- Shows the model's prediction (Yes/No with explanation)
- Select your corrected answer (Yes/No)
- Edit or confirm the explanation
- Add optional comments
- Click **Submit Annotation**

### 3. Navigation

- Use **← Previous** / **Next →** buttons at the top
- Click any note in the sidebar to jump directly
- Progress bar shows your completion status
- ✓ indicates completed notes, ○ indicates pending

### 4. Settings

Click **Settings** in the sidebar to:
- Edit keywords (updates highlighting in real-time)
- Download results as JSON
- Change setup (different file or annotator)

### 5. Resuming Work

Your progress is saved automatically. To continue later:
1. Open the app
2. Enter the **same Annotator ID**
3. Upload the **same JSON file**
4. Your previous annotations will be loaded

## Output Format

Annotations are saved back to the input file. Each note will have an `annotations` object with entries per annotator:

```json
{
  "id": "note_001",
  "text": "...",
  "annotations": {
    "Annotator_A": {
      "corrected_answer": "Yes",
      "corrected_explanation": "Updated explanation...",
      "comment": "Reviewer notes here",
      "timestamp": "2026-01-14T19:23:56.556298"
    },
    "Annotator_B": {
      "corrected_answer": "No",
      "corrected_explanation": "Different interpretation...",
      "comment": "",
      "timestamp": "2026-01-14T20:15:30.123456"
    }
  }
}
```

## Multiple Annotators

- Each annotator's work is stored separately under their ID
- Annotators only see their own progress and annotations
- All annotations are preserved in the same file
- Use **Download Results** to export the file with all annotations

### Important: Avoid Concurrent Editing

**Do NOT have multiple annotators work on the same file simultaneously.** This app saves directly to a local file, so concurrent edits will overwrite each other.

**Recommended workflow for teams:**
1. **Option A - Sequential:** One annotator completes their work, downloads the results, then passes the file to the next annotator
2. **Option B - Separate files:** Give each annotator their own copy of the input file, then merge results afterward
3. **Option C - Separate instances:** Run the app on different machines/ports with different file copies

## Resetting Annotations

To start fresh with a file:
1. On the setup screen, expand **Reset Annotations**
2. Click **Reset and Overwrite File**
3. Re-upload the file to load clean data

## File Structure

```
annotation-platform/
├── app.py              # Main Streamlit application
├── utils.py            # Helper functions
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── data/               # Working directory for JSON files
    └── sample_input.json
```

## Sample Data

A sample file is provided at `data/sample_input.json` with 3 clinical notes for testing.

import json
import re
from datetime import datetime
from typing import Any


def load_json_data(filepath: str) -> dict[str, Any]:
    """
    Load clinical notes from a JSON file.

    Expected structure:
    {
        "keywords": ["keyword1", "keyword2", ...],
        "notes": [
            {
                "id": "note_001",
                "text": "Clinical note text...",
                "question": "Question to answer?",
                "predicted_answer": "Yes/No",
                "predicted_explanation": "Model's explanation",
                "evidence": ["evidence span 1", "evidence span 2"],
                "annotation": {  // Optional - added when annotated
                    "annotator_id": "...",
                    "corrected_answer": "...",
                    "corrected_explanation": "...",
                    "comment": "...",
                    "timestamp": "..."
                }
            }
        ]
    }

    Returns dict with 'keywords' and 'notes'.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "notes" not in data:
        raise ValueError("JSON must contain a 'notes' key")

    required_fields = ["id", "text", "question", "predicted_answer"]
    for i, note in enumerate(data["notes"]):
        for field in required_fields:
            if field not in note:
                raise ValueError(f"Note at index {i} missing required field: {field}")
        # Ensure evidence is a list
        if "evidence" not in note:
            note["evidence"] = []
        elif not isinstance(note["evidence"], list):
            note["evidence"] = [note["evidence"]]

    # Ensure keywords exists
    if "keywords" not in data:
        data["keywords"] = []

    return data


def save_json_data(filepath: str, data: dict[str, Any]) -> None:
    """Save the data back to the JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_annotation_to_note(
    data: dict[str, Any],
    note_id: str,
    annotator_id: str,
    corrected_answer: str,
    corrected_explanation: str,
    comment: str,
) -> None:
    """
    Save annotation directly to a note in the data structure.
    Annotations are stored per-annotator.
    Call save_json_data() after this to persist to file.
    """
    for note in data["notes"]:
        if note.get("id") == note_id:
            # Initialize annotations dict if not exists
            if "annotations" not in note:
                note["annotations"] = {}

            # Store annotation under annotator's ID
            note["annotations"][annotator_id] = {
                "corrected_answer": corrected_answer,
                "corrected_explanation": corrected_explanation,
                "comment": comment,
                "timestamp": datetime.now().isoformat(),
            }
            break


def get_annotation_for_annotator(note: dict[str, Any], annotator_id: str) -> dict[str, Any]:
    """Get annotation for a specific annotator from a note."""
    annotations = note.get("annotations", {})
    return annotations.get(annotator_id, {})


def highlight_text(text: str, keywords: list[str], evidence: list[str]) -> str:
    """
    Return HTML with highlighted keywords (yellow) and evidence spans (green).
    Evidence highlighting takes precedence over keyword highlighting.
    """
    if not text:
        return ""

    # Track spans to highlight: (start, end, type)
    spans = []

    # Find evidence spans first (higher priority)
    for ev in evidence:
        if not ev:
            continue
        pattern = re.escape(ev)
        for match in re.finditer(pattern, text, re.IGNORECASE):
            spans.append((match.start(), match.end(), "evidence"))

    # Find keyword matches
    for kw in keywords:
        if not kw:
            continue
        pattern = r'\b' + re.escape(kw) + r'\b'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            overlaps = False
            for start, end, span_type in spans:
                if span_type == "evidence":
                    if not (match.end() <= start or match.start() >= end):
                        overlaps = True
                        break
            if not overlaps:
                spans.append((match.start(), match.end(), "keyword"))

    spans.sort(key=lambda x: x[0])

    result = []
    last_end = 0

    for start, end, span_type in spans:
        if start > last_end:
            result.append(_escape_html(text[last_end:start]))

        span_text = _escape_html(text[start:end])
        if span_type == "evidence":
            result.append(
                f'<span style="background-color: #90EE90; padding: 2px 4px; '
                f'border-radius: 3px; border: 1px solid #228B22;">{span_text}</span>'
            )
        else:
            result.append(
                f'<span style="background-color: #FFFF99; padding: 1px 2px; '
                f'border-radius: 2px;">{span_text}</span>'
            )

        last_end = end

    if last_end < len(text):
        result.append(_escape_html(text[last_end:]))

    html_text = "".join(result)
    html_text = html_text.replace("\n", "<br>")

    return html_text


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

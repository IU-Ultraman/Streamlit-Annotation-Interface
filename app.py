import streamlit as st
from utils import load_json_data, save_json_data, save_annotation_to_note, get_annotation_for_annotator, highlight_text
import os

# Page configuration
st.set_page_config(
    page_title="Clinical Annotation Interface",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "data" not in st.session_state:
    st.session_state.data = None
if "annotator_id" not in st.session_state:
    st.session_state.annotator_id = ""
if "keywords" not in st.session_state:
    st.session_state.keywords = []
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "file_path" not in st.session_state:
    st.session_state.file_path = None


def go_to_note(index):
    """Navigate to a specific note index."""
    st.session_state.current_index = index


def get_completed_notes(annotator_id: str):
    """Get set of note IDs that have annotations by this annotator."""
    if st.session_state.data is None:
        return set()
    return {
        note["id"]
        for note in st.session_state.data["notes"]
        if annotator_id in note.get("annotations", {})
    }


# ============================================
# SETUP SCREEN
# ============================================
if not st.session_state.setup_complete:
    st.title("Clinical Annotation Interface")
    st.markdown("---")

    st.header("Setup")

    # Annotator ID
    annotator_id = st.text_input(
        "Annotator ID",
        value=st.session_state.annotator_id,
        placeholder="Your name or ID",
    )
    st.session_state.annotator_id = annotator_id

    st.markdown("")

    # File upload (JSON)
    uploaded_file = st.file_uploader(
        "Upload JSON File",
        type=["json"],
        help="JSON with keywords and notes array",
    )

    if uploaded_file is not None:
        try:
            # Save uploaded file to persistent location in data folder
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            file_path = os.path.join(data_dir, uploaded_file.name)

            # Only write if file doesn't exist or user is uploading new content
            if not os.path.exists(file_path):
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # Load from persistent location (may have existing annotations)
            data = load_json_data(file_path)
            st.session_state.data = data
            st.session_state.keywords = data.get("keywords", [])
            st.session_state.file_path = file_path

            # Count notes and show info
            total = len(data["notes"])
            st.success(f"Loaded {total} notes")

        except Exception as e:
            st.error(f"Error loading file: {e}")

    st.markdown("")

    # Start button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Start Annotation", type="primary", use_container_width=True):
            if not st.session_state.annotator_id:
                st.error("Please enter your Annotator ID")
            elif st.session_state.data is None:
                st.error("Please upload a JSON file")
            else:
                st.session_state.setup_complete = True
                st.rerun()

    # Show expected JSON format
    with st.expander("JSON Format Guide"):
        st.markdown("""
        **Expected structure:**
        ```json
        {
            "keywords": ["diabetes", "metformin", "HbA1c"],
            "notes": [
                {
                    "id": "note_001",
                    "text": "Clinical note text...",
                    "question": "Does the patient have diabetes?",
                    "predicted_answer": "Yes",
                    "predicted_explanation": "Based on HbA1c...",
                    "evidence": ["HbA1c of 7.2%", "history of metformin"]
                }
            ]
        }
        ```

        **Progress is saved automatically.** Re-upload the same filename to continue where you left off.
        """)

    # Option to reset file
    with st.expander("Reset Annotations"):
        st.warning("This will clear all annotations for the uploaded file.")
        if st.button("Reset and Overwrite File"):
            if uploaded_file is not None:
                file_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "data", uploaded_file.name
                )
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("File reset. Please re-upload to load fresh data.")
                st.session_state.data = None
                st.rerun()

    st.stop()


# ============================================
# MAIN ANNOTATION INTERFACE
# ============================================
notes = st.session_state.data["notes"]
total = len(notes)
current_note = notes[st.session_state.current_index]
note_id = current_note.get("id", f"note_{st.session_state.current_index}")
annotator_id = st.session_state.annotator_id
completed_notes = get_completed_notes(annotator_id)
is_completed = note_id in completed_notes

# Sidebar
with st.sidebar:
    st.caption(f"Annotator: {st.session_state.annotator_id}")

    # Progress bar
    completed_count = len(completed_notes)
    st.progress(completed_count / total if total > 0 else 0)
    st.caption(f"{completed_count} of {total} completed")

    st.markdown("---")

    # Settings expander for keywords
    with st.expander("Settings"):
        keywords_edit = st.text_area(
            "Keywords (one per line)",
            value="\n".join(st.session_state.keywords),
            height=100,
            key="keywords_edit",
        )
        if st.button("Update Keywords", use_container_width=True):
            st.session_state.keywords = [
                kw.strip() for kw in keywords_edit.split("\n") if kw.strip()
            ]
            # Also update in data and save
            st.session_state.data["keywords"] = st.session_state.keywords
            save_json_data(st.session_state.file_path, st.session_state.data)
            st.success("Keywords updated!")
            st.rerun()

        st.markdown("---")

        if st.button("Change Setup", use_container_width=True):
            st.session_state.setup_complete = False
            st.rerun()

        # Download button for results
        st.markdown("---")
        st.download_button(
            "Download Results",
            data=open(st.session_state.file_path, "r").read(),
            file_name="annotated_results.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("---")

    # Note list
    st.markdown("**Notes**")

    for i, note in enumerate(notes):
        nid = note.get("id", f"note_{i}")
        is_current = i == st.session_state.current_index
        is_done = annotator_id in note.get("annotations", {})

        if is_done:
            status_icon = "✓"
            status_color = "#28a745"
        else:
            status_icon = "○"
            status_color = "#6c757d"

        if is_current:
            st.markdown(
                f"""<div style="background-color: #e3f2fd; padding: 6px 10px; border-radius: 4px;
                    margin-bottom: 4px; border-left: 3px solid #1976d2; font-size: 0.9em;">
                    <span style="color: {status_color};">{status_icon}</span> <strong>{nid}</strong></div>""",
                unsafe_allow_html=True,
            )
        else:
            if st.button(f"{status_icon} {nid}", key=f"nav_{i}", use_container_width=True):
                go_to_note(i)
                st.rerun()


# Main content area
# Top navigation bar
nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 3])

with nav_col1:
    prev_disabled = st.session_state.current_index == 0
    if st.button("← Previous", use_container_width=True, disabled=prev_disabled):
        st.session_state.current_index -= 1
        st.rerun()

with nav_col2:
    next_disabled = st.session_state.current_index >= total - 1
    if st.button("Next →", use_container_width=True, disabled=next_disabled, type="primary"):
        st.session_state.current_index += 1
        st.rerun()

with nav_col3:
    if is_completed:
        st.markdown(
            f"""<div style="background-color: #d4edda; color: #155724; padding: 8px 16px;
                border-radius: 4px; text-align: center;">
                <strong>✓ VERIFIED</strong> - Note {st.session_state.current_index + 1} of {total}</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style="background-color: #fff3cd; color: #856404; padding: 8px 16px;
                border-radius: 4px; text-align: center;">
                <strong>○ PENDING</strong> - Note {st.session_state.current_index + 1} of {total}</div>""",
            unsafe_allow_html=True,
        )

st.markdown("---")

# Question display
question = current_note.get("question", "No question provided")
st.markdown(f"### Question: {question}")

st.markdown("")

# Two-column layout with independent scroll
left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("Clinical Note")

    # Legend
    keywords = st.session_state.keywords
    evidence = current_note.get("evidence", [])

    legend_parts = []
    if keywords:
        legend_parts.append(
            '<span style="background-color: #FFFF99; padding: 2px 6px; border-radius: 3px; margin-right: 10px;">Keywords</span>'
        )
    if evidence:
        legend_parts.append(
            '<span style="background-color: #90EE90; padding: 2px 6px; border-radius: 3px; border: 1px solid #228B22;">Evidence</span>'
        )

    if legend_parts:
        st.markdown(
            f'<div style="margin-bottom: 10px; font-size: 0.9em;">{"".join(legend_parts)}</div>',
            unsafe_allow_html=True,
        )

    # Clinical note in scrollable container
    note_text = current_note.get("text", "")
    highlighted_html = highlight_text(note_text, keywords, evidence)

    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;
                    height: 450px; overflow-y: auto; line-height: 1.6; border: 1px solid #dee2e6;">
            {highlighted_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show evidence list
    if evidence:
        with st.expander("Evidence Spans", expanded=False):
            for i, ev in enumerate(evidence, 1):
                st.markdown(f"{i}. {ev}")

with right_col:
    st.subheader("Annotation Panel")

    # Get existing annotation for this annotator
    existing_annotation = get_annotation_for_annotator(current_note, annotator_id)

    # Model prediction display
    st.markdown("**Model Prediction:**")
    predicted_answer = current_note.get("predicted_answer", "N/A")
    predicted_explanation = current_note.get("predicted_explanation", "")

    pred_color = "#d4edda" if str(predicted_answer).lower() == "yes" else "#f8d7da"
    st.markdown(
        f"""
        <div style="background-color: {pred_color}; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <strong>Answer:</strong> {predicted_answer}<br>
            <strong>Explanation:</strong> {predicted_explanation or "No explanation provided"}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Annotation form
    st.markdown("**Your Annotation:**")

    # Answer selection - use existing annotation or model prediction
    answer_options = ["Yes", "No"]
    if existing_annotation:
        default_index = 0 if existing_annotation.get("corrected_answer", "").lower() == "yes" else 1
    else:
        default_index = (
            0 if str(predicted_answer).lower() == "yes"
            else 1 if str(predicted_answer).lower() == "no" else 0
        )

    corrected_answer = st.radio(
        "Corrected Answer",
        answer_options,
        index=default_index,
        horizontal=True,
        key=f"answer_{note_id}",
    )

    # Explanation - use existing or model prediction
    default_explanation = existing_annotation.get("corrected_explanation", predicted_explanation)
    corrected_explanation = st.text_area(
        "Explanation",
        value=default_explanation,
        height=120,
        placeholder="Provide or modify the explanation...",
        key=f"explanation_{note_id}",
    )

    # Comment - use existing or empty
    default_comment = existing_annotation.get("comment", "")
    comment = st.text_area(
        "Additional Comments (Optional)",
        value=default_comment,
        height=80,
        placeholder="Add any notes or feedback...",
        key=f"comment_{note_id}",
    )

    st.markdown("---")

    # Submit button
    if st.button("Submit Annotation", type="primary", use_container_width=True):
        # Save annotation to the note
        save_annotation_to_note(
            data=st.session_state.data,
            note_id=note_id,
            annotator_id=st.session_state.annotator_id,
            corrected_answer=corrected_answer,
            corrected_explanation=corrected_explanation,
            comment=comment,
        )

        # Save to file
        save_json_data(st.session_state.file_path, st.session_state.data)

        st.success("Annotation saved!")

        # Auto-advance to next note or show completion
        if st.session_state.current_index < len(notes) - 1:
            st.session_state.current_index += 1
        else:
            st.balloons()
            st.info("You have completed all notes!")

        st.rerun()

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ECG_HRV_Project_Study_Guide.docx"

TEAL = "239B92"
PALE = "EAF6F4"
LIGHT = "F4F7FB"
DARK = "172033"
GRAY = "62718A"
WHITE = "FFFFFF"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_border(cell, color="D9D9D9", size="6"):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell_text(cell, text, bold=False, color=DARK, size=9.5):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, headers, rows, widths=None, font_size=9.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_shading(cell, TEAL)
        set_cell_border(cell)
        set_cell_text(cell, header, bold=True, color=WHITE, size=font_size)
        if widths:
            cell.width = Inches(widths[i])
    for r, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_border(cells[i])
            set_cell_shading(cells[i], LIGHT if r % 2 == 0 else WHITE)
            set_cell_text(cells[i], str(value), size=font_size)
            if widths:
                cells[i].width = Inches(widths[i])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_bullet(doc, text, level=0):
    paragraph = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.line_spacing = 1.05
    run = paragraph.add_run(text)
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(10.5)
    return paragraph


def add_numbered(doc, text):
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run(text)
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(10.5)
    return paragraph


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    return p


def add_answer(doc, question, answer):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(question)
    r.bold = True
    r.font.name = "Aptos"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor.from_string(TEAL)
    q = doc.add_paragraph(answer)
    q.paragraph_format.left_indent = Inches(0.18)
    q.paragraph_format.space_after = Pt(4)
    for run in q.runs:
        run.font.name = "Aptos"
        run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
        run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
        run.font.size = Pt(10.5)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Page ")
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def setup_document():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.62)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(DARK)
    for style_name, size in [("Title", 25), ("Heading 1", 17), ("Heading 2", 12.5), ("Heading 3", 11.5)]:
        style = styles[style_name]
        style.font.name = "Aptos Display" if style_name == "Title" else "Aptos"
        style._element.rPr.rFonts.set(qn("w:ascii"), style.font.name)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), style.font.name)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
    footer = section.footer
    add_page_number(footer.paragraphs[0])
    for run in footer.paragraphs[0].runs:
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor.from_string(GRAY)
    return doc


def build():
    doc = setup_document()

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("ECG HRV Anxiety Level Estimation")
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("Presentation Study Guide and Viva Preparation")
    r.font.size = Pt(14)
    r.font.color.rgb = RGBColor.from_string(TEAL)
    doc.add_paragraph()
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run("Student: ____________________    Roll No.: ____________________\n").bold = True
    meta.add_run("Guide: ____________________    Department: ____________________")
    doc.add_paragraph()
    intro = doc.add_paragraph()
    intro.alignment = WD_ALIGN_PARAGRAPH.CENTER
    intro.add_run("Use this guide to explain the project clearly, answer viva questions, and present the results accurately.").italic = True
    doc.add_page_break()

    add_heading(doc, "1 Project in one minute", 1)
    doc.add_paragraph("This project estimates anxiety level from engineered ECG and heart-rate-variability features. The system predicts Low, Medium, or High anxiety. It uses a subject-aware machine-learning pipeline so that records from the same person do not appear in both training and testing. The final model is Logistic Regression, selected after comparison with Random Forest. On an external labeled test set, the model achieved 88.25% accuracy and 87.69% macro-F1.")
    add_heading(doc, "One minute presentation script", 2)
    doc.add_paragraph("My project is an ECG and HRV based anxiety-level estimation system. I used tabular ECG-derived features such as mean heart rate, RMSSD, SDNN, LF/HF ratio, and signal quality. I validated the data, handled missing values, removed duplicate subject-window records, and used subject-wise splitting to prevent data leakage. I compared Logistic Regression with Random Forest using grouped cross-validation. Logistic Regression performed better and was selected. On 2,000 labeled records from 20 unseen subjects, the model achieved 88.25% accuracy. The current system is a prototype using engineered features. The next stage is to connect an IoT ECG device, process raw ECG signals, extract HRV features, and run real-time prediction.")

    add_heading(doc, "2 Motivation and background", 1)
    add_bullet(doc, "Anxiety can affect autonomic nervous-system activity.")
    add_bullet(doc, "Heart rate may increase during stress or anxiety-related arousal.")
    add_bullet(doc, "Short-term HRV measures such as RMSSD can change with autonomic balance.")
    add_bullet(doc, "ECG is a practical physiological signal for a future wearable or IoT system.")
    add_bullet(doc, "The project aims to estimate anxiety level, not diagnose a clinical disorder.")
    add_heading(doc, "Research methods considered", 2)
    add_table(doc, ["Method", "Signal or source", "Main limitation"], [
        ["EEG", "Brain electrical activity", "Complex hardware, artifacts, and daily-use difficulty"],
        ["ECG / HRV", "Heart electrical activity", "Not anxiety-specific; needs generalisation"],
        ["PPG / BVP", "Optical blood-volume signal", "Noisy and non-specific"],
        ["EDA / GSR", "Skin conductance", "Measures arousal more directly than anxiety"],
        ["DASS-21", "Self-report questionnaire", "Subjective and episodic"],
        ["Social media / voice", "Posts or recordings", "Privacy, context, and person-to-person variation"],
    ], [1.25, 2.2, 3.7], 9)
    doc.add_paragraph("Project choice: ECG/HRV was selected because it is non-invasive, physiologically meaningful, compatible with future wearable hardware, and usable for a feature-based prototype before raw-ECG collection is available.")

    add_heading(doc, "3 Objectives", 1)
    add_numbered(doc, "Build a reproducible ECG/HRV feature-based anxiety estimator.")
    add_numbered(doc, "Predict three levels: Low, Medium, and High.")
    add_numbered(doc, "Compare interpretable and nonlinear classical machine-learning models.")
    add_numbered(doc, "Use subject-aware evaluation to avoid optimistic results from data leakage.")
    add_numbered(doc, "Create an evaluation interface that shows matches, mismatches, and metrics.")

    add_heading(doc, "4 Datasets and data structure", 1)
    add_table(doc, ["Use", "Files", "Size and purpose"], [
        ["Training", "ecg_hrv_dataset.csv; ecg_hrv_dataset_2.csv; ecg_hrv_dataset_synthetic_10k.csv", "29,900 unique rows after duplicate removal; 299 subjects"],
        ["External evaluation", "ecg_hrv_prediction_labeled.csv", "2,000 records from 20 unseen subjects"],
        ["Target", "anxiety_level", "Low, Medium, High"],
        ["Identifiers", "subject_id, window_id", "Used for grouping and duplicate detection, not as model features"],
    ], [1.35, 3.55, 2.25], 9)
    doc.add_paragraph("Important: the files contain engineered ECG/HRV features. They do not contain raw ECG waveforms. Therefore, filtering and R-peak detection are not part of the current training run.")

    add_heading(doc, "5 What the features mean", 1)
    add_table(doc, ["Feature group", "Examples", "Meaning"], [
        ["Cardiac rate", "mean_hr_bpm, mean_rr_ms", "Average heart rate and time between beats"],
        ["Time-domain HRV", "sdnn_ms, rmssd_ms, pnn50_pct", "Beat-to-beat variation"],
        ["Frequency-domain HRV", "lf_power_ms2, hf_power_ms2, lf_hf_ratio", "Frequency components and autonomic balance"],
        ["Nonlinear HRV", "sd1_ms, sd2_ms, sample_entropy", "Poincare geometry and signal complexity"],
        ["Signal descriptors", "qrs_duration_ms, r_peak_amp_mv, signal_quality_index", "Morphology and signal-quality context"],
    ], [1.65, 2.4, 3.1], 9)
    doc.add_paragraph("The model does not decide from one feature alone. It learns a combined pattern across the available features.")

    add_heading(doc, "6 Data processing pipeline", 1)
    add_heading(doc, "Current pipeline", 2)
    add_numbered(doc, "Load the CSV files and validate required columns and target labels.")
    add_numbered(doc, "Remove duplicate records using subject_id plus window_id.")
    add_numbered(doc, "Separate identifiers and anxiety_level from the 21 numeric features.")
    add_numbered(doc, "Impute missing numeric values using the training-fold median.")
    add_numbered(doc, "Standardize features for Logistic Regression.")
    add_numbered(doc, "Split subjects into training and holdout groups.")
    add_numbered(doc, "Train and compare models using GroupKFold cross-validation.")
    add_numbered(doc, "Evaluate on unseen labeled subjects.")
    add_heading(doc, "Raw ECG pipeline planned for future work", 2)
    doc.add_paragraph("Raw ECG → bandpass and notch filtering → baseline-wander removal → R-peak detection → RR intervals → HRV features → trained model → Low / Medium / High estimate")

    add_heading(doc, "7 Duplicate records, missing values, and data leakage", 1)
    add_heading(doc, "Duplicate handling", 2)
    doc.add_paragraph("A duplicate is defined as the same subject_id and window_id appearing more than once. The loader keeps the first copy and removes later copies. Combining the three training files removed 100 repeated subject-window rows.")
    add_heading(doc, "Missing-value handling", 2)
    doc.add_paragraph("Some rows have missing values, especially in features such as sample_entropy. SimpleImputer(strategy='median') replaces missing numeric values with the median learned from the training data. The test data is not used to calculate that median.")
    add_heading(doc, "Why subject-wise splitting matters", 2)
    doc.add_paragraph("Windows from one person are correlated. If the same person appears in both training and testing, the model may recognise the person instead of learning anxiety-related patterns. GroupShuffleSplit and GroupKFold keep subjects together and prevent this leakage.")

    add_heading(doc, "8 Algorithms and baseline", 1)
    add_heading(doc, "What is a baseline", 2)
    doc.add_paragraph("A baseline is a reproducible reference model used to judge whether later changes improve performance. In this project, classical tabular models provide the first baseline before any raw-ECG deep-learning model is attempted.")
    add_heading(doc, "Logistic Regression", 2)
    add_bullet(doc, "Interpretable classification model for tabular features.")
    add_bullet(doc, "Works well after feature scaling.")
    add_bullet(doc, "Produces class probabilities that support confidence estimates.")
    add_bullet(doc, "Used class_weight='balanced' to reduce the effect of class imbalance.")
    add_heading(doc, "Random Forest", 2)
    add_bullet(doc, "Combines many decision trees.")
    add_bullet(doc, "Can learn nonlinear relationships and feature interactions.")
    add_bullet(doc, "Used as a strong comparison model for tabular data.")
    add_paragraph = doc.add_paragraph("Selection result: Logistic Regression was chosen because its grouped cross-validation macro-F1 was 0.8926, higher than Random Forest at 0.8867.")
    add_paragraph.paragraph_format.space_before = Pt(6)

    add_heading(doc, "9 Evaluation metrics", 1)
    add_table(doc, ["Metric", "Simple meaning", "Why it matters"], [
        ["Accuracy", "Correct predictions divided by all predictions", "Overall correctness"],
        ["Balanced accuracy", "Average recall across classes", "Useful when class counts differ"],
        ["Precision", "Of the records predicted as a class, how many were correct", "Measures false alarms"],
        ["Recall", "Of the actual records in a class, how many were found", "Measures missed cases"],
        ["F1-score", "Balance between precision and recall", "Single class-quality score"],
        ["Macro-F1", "Average F1 across Low, Medium, High", "Gives each class equal importance"],
    ], [1.35, 3.35, 2.45], 9)
    doc.add_paragraph("Example: High-anxiety recall of 91.63% means the model found 91.63% of the actual High records in the labeled test set.")

    add_heading(doc, "10 Confusion matrix", 1)
    doc.add_paragraph("A confusion matrix compares the actual label with the predicted label. Rows show the true class. Columns show the predicted class. The diagonal contains correct predictions. Off-diagonal cells show mistakes.")
    add_table(doc, ["Actual \\ Predicted", "Low", "Medium", "High"], [
        ["Low", "790", "70", "2"],
        ["Medium", "46", "603", "83"],
        ["High", "0", "34", "372"],
    ], [2.1, 1.35, 1.35, 1.35], 10)
    add_bullet(doc, "790 Low records were correctly predicted as Low.")
    add_bullet(doc, "603 Medium records were correctly predicted as Medium.")
    add_bullet(doc, "372 High records were correctly predicted as High.")
    add_bullet(doc, "The largest confusion is between Medium and High.")

    add_heading(doc, "11 Final results", 1)
    add_table(doc, ["Result", "Value"], [
        ["Test records", "2,000"],
        ["Test subjects", "20"],
        ["Training/test subject overlap", "0"],
        ["Accuracy", "88.25%"],
        ["Balanced accuracy", "88.55%"],
        ["Macro-F1", "87.69%"],
        ["High-anxiety recall", "91.63%"],
    ], [3.8, 2.3], 10)
    doc.add_paragraph("How to explain the result: the model correctly classified most unseen labeled records, but it still confuses some Medium and High cases. The result is strong for this prototype, but it should not be presented as clinical accuracy because the current data is engineered and prototype-oriented.")

    add_heading(doc, "12 Frontend and demonstration", 1)
    add_bullet(doc, "The React frontend lets the user upload a labeled CSV.")
    add_bullet(doc, "The FastAPI backend loads the saved Logistic Regression model.")
    add_bullet(doc, "The backend compares predicted_anxiety_level with the true anxiety_level.")
    add_bullet(doc, "The interface shows correct and incorrect counts, accuracy, precision, recall, F1, and a confusion matrix.")
    add_bullet(doc, "The results can be downloaded as a CSV with row-level predictions.")
    doc.add_paragraph("For the final demonstration, use the labeled test file with 2,000 records. Do not use a two-row sample to claim overall accuracy because a tiny sample can show 100% by chance.")

    add_heading(doc, "13 Limitations and responsible use", 1)
    add_bullet(doc, "The current files do not contain raw ECG waveforms.")
    add_bullet(doc, "The supplied data is synthetic or prototype-oriented, so real-world performance may differ.")
    add_bullet(doc, "ECG/HRV is not specific enough to diagnose anxiety by itself.")
    add_bullet(doc, "A model confidence value is not medical certainty.")
    add_bullet(doc, "The system should be described as anxiety-level estimation or screening support.")

    add_heading(doc, "14 Future work with the IoT device", 1)
    add_numbered(doc, "Connect an AD8232 ECG module, ESP32, or wearable ECG device.")
    add_numbered(doc, "Capture and transmit raw ECG data from the device.")
    add_numbered(doc, "Filter noise using bandpass, notch, and baseline-wander removal.")
    add_numbered(doc, "Detect R-peaks and calculate RR intervals.")
    add_numbered(doc, "Extract the same HRV features used by the current model.")
    add_numbered(doc, "Send features to the trained model for real-time Low, Medium, or High estimation.")
    add_numbered(doc, "Validate predictions using real-world labeled data and improve generalisation.")

    add_heading(doc, "15 Viva questions and short answers", 1)
    add_answer(doc, "What is the project?", "It is an ECG/HRV feature-based anxiety-level estimation system that predicts Low, Medium, or High anxiety.")
    add_answer(doc, "What is the main limitation?", "The current dataset contains engineered features, not raw ECG signals, so raw signal processing is future work.")
    add_answer(doc, "Why did you choose ECG/HRV?", "It is non-invasive, physiologically meaningful, and has a practical path to wearable or IoT implementation.")
    add_answer(doc, "Why not use EEG?", "EEG can be informative, but it usually requires more complex hardware, careful placement, and artifact handling.")
    add_answer(doc, "Why Logistic Regression?", "It is interpretable, fast, suitable for scaled tabular features, and produced the best grouped cross-validation macro-F1.")
    add_answer(doc, "Why Random Forest?", "It is a strong tabular-data comparison model that can capture nonlinear feature interactions.")
    add_answer(doc, "What is the baseline?", "The baseline is the first reproducible reference model used for comparison. Here, classical Logistic Regression and Random Forest form the initial baseline.")
    add_answer(doc, "Why subject-wise splitting?", "To prevent data leakage. Windows from one person must not appear in both training and testing.")
    add_answer(doc, "How were duplicates handled?", "Records with the same subject_id and window_id were treated as duplicates. Repeated records were removed before training.")
    add_answer(doc, "How were missing values handled?", "Numeric missing values were replaced with the training-fold median inside the pipeline.")
    add_answer(doc, "What does 88.25% accuracy mean?", "Out of 2,000 labeled test records, about 88.25% received the correct anxiety-level label.")
    add_answer(doc, "What does High recall of 91.63% mean?", "The model detected 91.63% of the actual High-anxiety records in the test set.")
    add_answer(doc, "What does the confusion matrix show?", "It shows which actual classes were correctly predicted and which classes were confused with each other.")
    add_answer(doc, "Does the model diagnose anxiety?", "No. It estimates an anxiety level from physiological features. It is not a clinical diagnostic system.")
    add_answer(doc, "What will you do next?", "I will connect an IoT ECG device, capture raw ECG, process it, extract HRV features, and pass them to the trained model for real-time prediction.")

    add_heading(doc, "16 Presentation checklist", 1)
    add_bullet(doc, "Fill in your name, roll number, guide, and department on the presentation cover.")
    add_bullet(doc, "Start with the one-minute project explanation.")
    add_bullet(doc, "Say clearly that the current data contains engineered ECG/HRV features, not raw ECG.")
    add_bullet(doc, "Show the 88.25% accuracy and 87.69% macro-F1 on the labeled test set.")
    add_bullet(doc, "Explain why subject-wise splitting prevents leakage.")
    add_bullet(doc, "End with the IoT future-work pipeline.")
    add_bullet(doc, "Use the phrase anxiety-level estimation, not anxiety diagnosis.")

    add_heading(doc, "17 Useful project commands", 1)
    doc.add_paragraph("Train the model:")
    doc.add_paragraph("python3 src/train.py \\\n  --data /Users/nishantnikhil/Downloads/ecg_hrv_dataset.csv \\\n  --data /Users/nishantnikhil/Downloads/ecg_hrv_dataset_2.csv \\\n  --data /Users/nishantnikhil/Downloads/ecg_hrv_dataset_synthetic_10k.csv \\\n  --output-dir artifacts/model-three")
    doc.add_paragraph("Evaluate the labeled test set:")
    doc.add_paragraph("python3 src/evaluate.py \\\n  --model artifacts/model-three/model.joblib \\\n  --data /Users/nishantnikhil/Downloads/ecg_hrv_prediction_labeled.csv")
    doc.add_paragraph("Run the React frontend with the Python API:")
    doc.add_paragraph("python -m uvicorn api:app --reload --port 8000\n\ncd frontend\nnpm run dev")

    add_heading(doc, "References", 1)
    add_bullet(doc, "Project datasets supplied for this work: ECG/HRV feature CSV files and labeled evaluation CSV.")
    add_bullet(doc, "Scikit-learn User Guide: https://scikit-learn.org/stable/")
    add_bullet(doc, "FastAPI documentation: https://fastapi.tiangolo.com/")
    add_bullet(doc, "React documentation: https://react.dev/")
    add_bullet(doc, "Research-method comparison notes supplied for the project.")

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()

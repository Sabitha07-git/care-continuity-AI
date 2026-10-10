import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
import json

from extraction import read_document, read_pdf, read_docx
from transform import structure_with_gemini, structure_with_python
from database import (
    insert_medical_record,
    get_all_medical_records,
    delete_medical_record
)



# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Care Continuity AI",
    page_icon="Care",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "records" not in st.session_state:
    try:
        st.session_state.records = get_all_medical_records()
    except Exception as e:
        st.session_state.records = []
        st.error(f"Could not load saved records from PostgreSQL: {e}") 

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

/* ============================================================
   GLOBAL
   ============================================================ */

.stApp {
    background: #f5faf9;
    color: #173d38;
}

.block-container {
    max-width: 1420px !important;

    padding-top: 0.5rem !important;
    padding-bottom: 3rem !important;

    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
}

header[data-testid="stHeader"] {
    height: 0 !important;
    background: transparent !important;
}

footer {
    display: none !important;
}


/* ============================================================
   GLOBAL HEADINGS
   ============================================================ */

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: #123b37 !important;
}


/* ============================================================
   HEADER
   ============================================================ */

.st-key-header {
    position: relative !important;
    z-index: 99999 !important;

    background: #ffffff !important;

    border: 1px solid #dce9e6 !important;

    border-radius: 0 0 18px 18px !important;

    padding: 12px 20px 10px 20px !important;

    margin-top: -8px !important;
    margin-bottom: 22px !important;

    box-shadow: 0 5px 20px rgba(20,60,55,0.05) !important;

    pointer-events: auto !important;
}

.st-key-header > div {
    position: relative !important;
    z-index: 100000 !important;
}

.st-key-header [data-testid="column"] {
    position: relative !important;
    z-index: 100001 !important;
}


/* ============================================================
   BRAND
   ============================================================ */

.brand-name {
    color: #087f73 !important;

    font-size: 24px;

    font-weight: 850;

    line-height: 1.1;

    white-space: nowrap;
}

.brand-subtitle {
    color: #718480 !important;

    font-size: 11px;

    margin-top: 5px;
}


/* ============================================================
   NAVIGATION
   ============================================================ */

.st-key-header button {
    position: relative !important;

    z-index: 100002 !important;

    width: 100% !important;

    min-height: 42px !important;

    height: 42px !important;

    padding: 0 10px !important;

    margin: 0 !important;

    border-radius: 9px !important;

    cursor: pointer !important;

    pointer-events: auto !important;

    font-size: 13px !important;

    font-weight: 750 !important;

    transition: 0.15s ease !important;
}


/* Normal navigation button */

.st-key-header button[kind="secondary"] {
    background: #121722 !important;

    color: #ffffff !important;

    border: 1px solid #242b38 !important;
}


/* Active navigation button */

.st-key-header button[kind="primary"] {
    background: #ff5252 !important;

    color: #ffffff !important;

    border: 1px solid #ff5252 !important;
}


/* Hover */

.st-key-header button:hover {
    background: #087f73 !important;

    color: #ffffff !important;

    border-color: #087f73 !important;
}


/* Entire button content is non-blocking */

.st-key-header button > div {
    width: 100% !important;

    height: 100% !important;

    display: flex !important;

    align-items: center !important;

    justify-content: center !important;

    pointer-events: none !important;
}


/* ============================================================
   ONLINE STATUS
   ============================================================ */

.online-status {
    background: #e2f7f1 !important;

    color: #087f73 !important;

    border-radius: 25px;

    padding: 10px 15px;

    text-align: center;

    font-size: 11px;

    font-weight: 800;

    white-space: nowrap;
}


/* ============================================================
   HERO
   ============================================================ */

.st-key-hero {
    position: relative !important;

    z-index: 1 !important;

    min-height: 310px;

    background:
        linear-gradient(
            120deg,
            #06463f 0%,
            #087f73 48%,
            #14aa97 100%
        ) !important;

    border-radius: 27px !important;

    padding: 48px 58px !important;

    margin-bottom: 25px !important;

    overflow: hidden !important;

    box-shadow:
        0 20px 45px rgba(4,90,82,0.18) !important;
}


/* Hero decorative circle */

.st-key-hero::before {
    content: "";

    position: absolute;

    width: 370px;
    height: 370px;

    right: -100px;
    top: -210px;

    border-radius: 50%;

    background: rgba(255,255,255,0.08);
}


/* Hero decorative circle */

.st-key-hero::after {
    content: "";

    position: absolute;

    width: 150px;
    height: 150px;

    right: 100px;
    bottom: -80px;

    border-radius: 50%;

    background: rgba(255,255,255,0.07);
}


/* Hero content above decorations */

.st-key-hero > div {
    position: relative !important;

    z-index: 2 !important;
}


/* ============================================================
   HERO EYEBROW
   ============================================================ */

.st-key-hero .stAlert {
    background: rgba(255,255,255,0.08) !important;

    border: none !important;

    border-radius: 9px !important;

    padding: 13px 18px !important;

    margin-bottom: 18px !important;
}

.st-key-hero .stAlert p,
.st-key-hero .stAlert span,
.st-key-hero .stAlert div {
    color: #d4f8f2 !important;

    -webkit-text-fill-color: #d4f8f2 !important;

    font-size: 12px !important;

    font-weight: 850 !important;

    letter-spacing: 1.5px !important;

    text-transform: uppercase !important;
}


/* ============================================================
   HERO TITLE
   ============================================================ */

.st-key-hero h1,
.st-key-hero h1 *,
.st-key-hero [data-testid="stMarkdownContainer"] h1,
.st-key-hero [data-testid="stMarkdownContainer"] h1 * {
    color: #ffffff !important;

    -webkit-text-fill-color: #ffffff !important;
}

.st-key-hero h1 {
    font-size: 48px !important;

    line-height: 1.08 !important;

    letter-spacing: -1.8px !important;

    font-weight: 850 !important;

    max-width: 1050px !important;

    margin: 0 !important;
}


/* ============================================================
   HERO DESCRIPTION
   ============================================================ */

.st-key-hero p,
.st-key-hero [data-testid="stMarkdownContainer"] p {
    color: #e4f5f2 !important;

    -webkit-text-fill-color: #e4f5f2 !important;

    font-size: 15px !important;

    line-height: 1.7 !important;

    max-width: 900px !important;
}


/* ============================================================
   SEARCH
   ============================================================ */

.search-input input {
    background: #ffffff !important;

    color: #173d38 !important;

    border: 1px solid #d4e4e0 !important;

    border-radius: 11px !important;

    min-height: 50px !important;

    font-size: 14px !important;

    box-shadow:
        0 4px 18px rgba(20,60,55,0.04) !important;
}

.search-input input::placeholder {
    color: #81918d !important;
}

.search-button button {
    min-height: 50px !important;

    background: #079b8a !important;

    color: #ffffff !important;

    border: none !important;

    border-radius: 11px !important;

    font-weight: 800 !important;
}


/* ============================================================
   SECTION TITLES
   ============================================================ */

.section-title {
    color: #123b37 !important;

    font-size: 25px;

    font-weight: 850;

    letter-spacing: -0.5px;

    margin-top: 24px;

    margin-bottom: 3px;
}

.section-description {
    color: #718480 !important;

    font-size: 13px;

    margin-bottom: 17px;
}


/* ============================================================
   QUICK ACTION CARDS
   ============================================================ */

.st-key-upload-card,
.st-key-patient-card,
.st-key-clinical-card {
    background: #ffffff !important;

    border: 1px solid #dce9e6 !important;

    border-radius: 18px !important;

    padding: 24px !important;

    min-height: 225px !important;

    box-shadow:
        0 8px 28px rgba(20,65,60,0.055) !important;
}

.st-key-upload-card {
    border-top: 4px solid #5aa8df !important;
}

.st-key-patient-card {
    border-top: 4px solid #0da990 !important;
}

.st-key-clinical-card {
    border-top: 4px solid #e7b934 !important;
}


/* ============================================================
   CARD CONTENT
   ============================================================ */

.card-symbol {
    width: 48px;

    height: 48px;

    border-radius: 12px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 12px;

    font-weight: 850;

    margin-bottom: 17px;
}

.upload-symbol {
    background: #eaf5fc;

    color: #398cc7 !important;
}

.patient-symbol {
    background: #e5f7f2;

    color: #087f73 !important;
}

.clinical-symbol {
    background: #fff6d9;

    color: #c59414 !important;
}

.card-title {
    color: #173d38 !important;

    font-size: 18px;

    font-weight: 850;

    margin-bottom: 7px;
}

.card-description {
    color: #718480 !important;

    font-size: 12px;

    line-height: 1.6;

    min-height: 42px;
}


/* ============================================================
   CARD BUTTONS
   ============================================================ */

.st-key-upload_action button,
.st-key-patient_action button,
.st-key-clinical_action button {
    background: #121722 !important;

    color: #ffffff !important;

    border: none !important;

    border-radius: 9px !important;

    min-height: 42px !important;

    font-weight: 750 !important;
}

.st-key-upload_action button:hover,
.st-key-patient_action button:hover,
.st-key-clinical_action button:hover {
    background: #087f73 !important;
}


/* ============================================================
   METRIC CARDS
   ============================================================ */

.st-key-record-metric,
.st-key-lab-metric,
.st-key-med-metric,
.st-key-allergy-metric {
    background: #ffffff !important;

    border-radius: 17px !important;

    padding: 19px !important;

    border: 1px solid #dce9e6 !important;

    box-shadow:
        0 8px 25px rgba(20,65,60,0.05) !important;
}

.st-key-record-metric {
    border-top: 4px solid #5aa8df !important;
}

.st-key-lab-metric {
    border-top: 4px solid #0da990 !important;
}

.st-key-med-metric {
    border-top: 4px solid #e7b934 !important;
}

.st-key-allergy-metric {
    border-top: 4px solid #e66c6c !important;
}

.st-key-record-metric *,
.st-key-lab-metric *,
.st-key-med-metric *,
.st-key-allergy-metric * {
    color: #173d38 !important;
}


/* ============================================================
   CARE OVERVIEW
   ============================================================ */

.st-key-records-panel,
.st-key-activity-panel {
    background: #ffffff !important;

    border: 1px solid #dce9e6 !important;

    border-radius: 18px !important;

    padding: 23px !important;

    box-shadow:
        0 8px 25px rgba(20,65,60,0.05) !important;
}

.st-key-records-panel h3,
.st-key-activity-panel h3 {
    color: #173d38 !important;
}


/* ============================================================
   UPLOAD PROCESS CARDS
   ============================================================ */

.upload-step {
    background: #ffffff !important;

    border: 1px solid #dce9e6 !important;

    border-radius: 16px !important;

    padding: 22px !important;

    min-height: 125px !important;

    box-shadow:
        0 6px 20px rgba(20,65,60,0.04) !important;
}

.upload-step-number {
    color: #079b8a !important;

    font-size: 13px !important;

    font-weight: 800 !important;

    letter-spacing: 1px !important;
}

.upload-step-title {
    color: #173d38 !important;

    font-size: 17px !important;

    font-weight: 800 !important;

    margin-top: 10px !important;
}

.upload-step-description {
    color: #718480 !important;

    font-size: 12px !important;

    margin-top: 6px !important;
}


/* ============================================================
   UPLOAD BOX
   ============================================================ */

.upload-box {
    background: #ffffff !important;

    border: 1px solid #dce9e6 !important;

    border-radius: 18px !important;

    padding: 24px !important;

    margin-top: 4px !important;

    box-shadow:
        0 7px 25px rgba(20,65,60,0.05) !important;
}

.upload-box label {
    color: #173d38 !important;

    font-weight: 700 !important;
}


/* ============================================================
   FILE UPLOADER
   ============================================================ */

div[data-testid="stFileUploader"] {
    background: #f8fbfa !important;

    border: 1px solid #d5e4e1 !important;

    border-radius: 12px !important;

    padding: 12px !important;
}

div[data-testid="stFileUploader"] * {
    color: #173d38 !important;
}

div[data-testid="stFileUploader"] button {
    background: #121722 !important;

    color: #ffffff !important;

    border: none !important;

    border-radius: 8px !important;
}


/* ============================================================
   DATAFRAME
   ============================================================ */

div[data-testid="stDataFrame"] {
    border-radius: 12px !important;

    overflow: hidden !important;

    border: 1px solid #dce9e6 !important;
}


/* ============================================================
   TABS
   ============================================================ */

button[data-baseweb="tab"] {
    color: #637570 !important;

    font-weight: 750 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #087f73 !important;
}


/* ============================================================
   RESPONSIVE
   ============================================================ */

@media(max-width: 1000px) {

    .block-container {
        padding-left: 1rem !important;

        padding-right: 1rem !important;
    }

    .st-key-hero {
        padding: 35px 25px !important;
    }

    .st-key-hero h1 {
        font-size: 36px !important;
    }

    .brand-name {
        font-size: 19px;
    }
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

with st.container(key="header"):

    brand_col, nav_col, status_col = st.columns(
        [2.7, 6.4, 1.8],
        vertical_alignment="center"
    )

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    with brand_col:

        st.markdown(
            """
            <div class="brand-name">
                Care Continuity AI
            </div>

            <div class="brand-subtitle">
                Connected healthcare information
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    with nav_col:

        nav1, nav2, nav3, nav4, nav5 = st.columns(
            [1, 1, 1.15, 1.1, 1],
            gap="small"
        )

        # Dashboard
        with nav1:

            if st.session_state.page == "Dashboard":

                if st.button(
                    "Dashboard",
                    key="nav_dashboard_active",
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state.page = "Dashboard"
                    st.rerun()

            else:

                if st.button(
                    "Dashboard",
                    key="nav_dashboard",
                    use_container_width=True
                ):
                    st.session_state.page = "Dashboard"
                    st.rerun()

        # Patients
        with nav2:

            if st.session_state.page == "Patients":

                if st.button(
                    "Patients",
                    key="nav_patients_active",
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state.page = "Patients"
                    st.rerun()

            else:

                if st.button(
                    "Patients",
                    key="nav_patients",
                    use_container_width=True
                ):
                    st.session_state.page = "Patients"
                    st.rerun()

        # Upload
        with nav3:

            if st.session_state.page == "Upload Record":

                if st.button(
                    "Upload Record",
                    key="nav_upload_active",
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state.page = "Upload Record"
                    st.rerun()

            else:

                if st.button(
                    "Upload Record",
                    key="nav_upload",
                    use_container_width=True
                ):
                    st.session_state.page = "Upload Record"
                    st.rerun()

        # Clinical
        with nav4:

            if st.session_state.page == "Clinical Data":

                if st.button(
                    "Clinical Data",
                    key="nav_clinical_active",
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state.page = "Clinical Data"
                    st.rerun()

            else:

                if st.button(
                    "Clinical Data",
                    key="nav_clinical",
                    use_container_width=True
                ):
                    st.session_state.page = "Clinical Data"
                    st.rerun()

        # Records
        with nav5:

            if st.session_state.page == "Records":

                if st.button(
                    "Records",
                    key="nav_records_active",
                    type="primary",
                    use_container_width=True
                ):
                    st.session_state.page = "Records"
                    st.rerun()

            else:

                if st.button(
                    "Records",
                    key="nav_records",
                    use_container_width=True
                ):
                    st.session_state.page = "Records"
                    st.rerun()

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    with status_col:

        st.markdown(
            """
            <div class="online-status">
                ● System Online
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    # --------------------------------------------------------
    # HERO
    # --------------------------------------------------------

    with st.container(key="hero"):

        st.success(
            "Healthcare Continuity Platform"
        )

        st.title(
            "Your patient's complete health story, in one place."
        )

        st.write(
            "Organize fragmented medical records, extract important "
            "clinical information and build a longitudinal view of "
            "patient care."
        )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search_col, button_col = st.columns(
        [5.5, 1]
    )

    with search_col:

        search = st.text_input(
            "Patient Search",
            placeholder="Search by patient name or patient ID...",
            label_visibility="collapsed",
            key="patient_search"
        )

    with button_col:

        if st.button(
            "Search",
            key="search_btn",
            use_container_width=True
        ):

            if search.strip():

                matches = [
                    r for r in st.session_state.records
                    if (
                        search.lower()
                        in r.get(
                            "patient_name",
                            ""
                        ).lower()
                    )
                    or
                    (
                        search.lower()
                        in r.get(
                            "patient_id",
                            ""
                        ).lower()
                    )
                ]

                if matches:

                    st.session_state["searched_patient_id"] = matches[0].get("patient_id")

                    st.session_state.pop("patients_page_selector", None)

                    st.session_state.page = "Patients"

                    st.rerun()

                else:

                    st.info(
                        "No matching patient found."
                    )

            else:

                st.warning(
                    "Enter a patient name or patient ID."
                )

    # --------------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Quick Actions</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Start working with patient information.'
        '</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(
        3,
        gap="large"
    )

    # Upload card
    with c1:

        with st.container(key="upload-card"):

            st.markdown(
                '<div class="card-symbol upload-symbol">DOC</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="card-title">'
                'Upload Medical Record'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="card-description">'
                'Upload PDF, DOCX or TXT medical documents.'
                '</div>',
                unsafe_allow_html=True
            )

            st.write("")

            if st.button(
                "Upload a record →",
                key="upload_action",
                use_container_width=True
            ):

                st.session_state.page = "Upload Record"

                st.rerun()

    # Patient card
    with c2:

        with st.container(key="patient-card"):

            st.markdown(
                '<div class="card-symbol patient-symbol">PT</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="card-title">'
                'Patient History'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="card-description">'
                'View longitudinal medical history and patient information.'
                '</div>',
                unsafe_allow_html=True
            )

            st.write("")

            if st.button(
                "View patients →",
                key="patient_action",
                use_container_width=True
            ):

                st.session_state.page = "Patients"

                st.rerun()

    # Clinical card
    with c3:

        with st.container(key="clinical-card"):

            st.markdown(
                '<div class="card-symbol clinical-symbol">LAB</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="card-title">'
                'Clinical Data'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="card-description">'
                'Review laboratory results, medications and allergies.'
                '</div>',
                unsafe_allow_html=True
            )

            st.write("")

            if st.button(
                "View clinical data →",
                key="clinical_action",
                use_container_width=True
            ):

                st.session_state.page = "Clinical Data"

                st.rerun()

    # --------------------------------------------------------
    # PATIENT OVERVIEW
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Patient Overview</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'A quick snapshot of the information available in this session.'
        '</div>',
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(
        4,
        gap="large"
    )

    # Records
    with m1:

        with st.container(key="record-metric"):

            st.metric(
                "Medical Records",
                len(st.session_state.records)
            )

            st.caption(
                "Processed documents"
            )

    # Labs
    with m2:

        with st.container(key="lab-metric"):

            lab_count = sum(
                len(
                    r.get(
                        "labs",
                        []
                    )
                )
                for r in st.session_state.records
            )

            st.metric(
                "Laboratory Tests",
                lab_count
            )

            st.caption(
                "Extracted results"
            )

    # Medications
    with m3:

        with st.container(key="med-metric"):

            medication_count = sum(
                len(
                    r.get(
                        "medications",
                        []
                    )
                )
                for r in st.session_state.records
            )

            st.metric(
                "Medications",
                medication_count
            )

            st.caption(
                "Recorded medications"
            )

    # Allergies
    with m4:

        with st.container(key="allergy-metric"):

            allergy_count = sum(
                len(
                    r.get(
                        "allergies",
                        []
                    )
                )
                for r in st.session_state.records
            )

            st.metric(
                "Allergies",
                allergy_count
            )

            st.caption(
                "Recorded allergies"
            )

    # --------------------------------------------------------
    # CARE OVERVIEW
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Care Overview</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Recent records and clinical activity.'
        '</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(
        [1.35, 1],
        gap="large"
    )

    with left:

        with st.container(key="records-panel"):

            st.markdown(
                "### Recent Medical Records"
            )

            st.caption(
                "Latest records processed in this session."
            )

            if not st.session_state.records:

                st.info(
                    "No records yet. Upload a medical record to get started."
                )

            else:

                rows = []

                for r in st.session_state.records[-5:]:

                    rows.append(
                        {
                            "Patient":
                                r.get(
                                    "patient_name",
                                    "Unknown"
                                ),

                            "Date":
                                r.get(
                                    "record_date",
                                    ""
                                ),

                            "Type":
                                  r.get("record_type") or "Medical Record",

                            "Status":
                                "Processed"
                        }
                    )

                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True
                )

    with right:

        with st.container(key="activity-panel"):

            st.markdown(
                "### Clinical Activity"
            )

            st.caption(
                "Overview of available clinical information."
            )

            a, b = st.columns(2)

            with a:

                patients_count = len(
                    set(
                        r.get(
                            "patient_name",
                            ""
                        )
                        for r in st.session_state.records
                    )
                )

                st.metric(
                    "Patients",
                    patients_count
                )

            with b:

                st.metric(
                    "Records",
                    len(
                        st.session_state.records
                    )
                )

            if st.session_state.records:

                st.success(
                    "Clinical information available."
                )

            else:

                st.info(
                    "Upload a medical record to populate the dashboard."
                )


# ============================================================
# PATIENTS
# ============================================================

elif st.session_state.page == "Patients":

    st.markdown(
        '<div class="section-title">Patients</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'View longitudinal patient information.'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.records:

        st.info(
            "No patients available yet. Upload a medical record first."
        )

    else:

        patients = sorted(
            set(
                r.get(
                    "patient_name",
                    "Unknown Patient"
                )
                for r in st.session_state.records
            )
        )

                # Check whether a patient was searched from the Dashboard
        searched_patient_id = st.session_state.pop(
            "searched_patient_id",
            None
        )

        # Find the matching patient name using their ID
        searched_patient_name = None

        if searched_patient_id:
            for r in st.session_state.records:
                if r.get("patient_id") == searched_patient_id:
                    searched_patient_name = r.get("patient_name")
                    break

        # Select the searched patient by default
        default_index = 0

        if searched_patient_name in patients:
            default_index = patients.index(searched_patient_name)

        patient = st.selectbox(
            "Select patient",
            patients,
            index=default_index,
            key="patients_page_selector"
        )

        patient_records = [
            r for r in st.session_state.records
            if r.get(
                "patient_name",
                ""
            ) == patient
        ]

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            st.metric(
                "Medical Records",
                len(patient_records)
            )

        with p2:

            st.metric(
                "Laboratory Tests",
                sum(
                    len(
                        r.get(
                            "labs",
                            []
                        )
                    )
                    for r in patient_records
                )
            )

        with p3:

            st.metric(
                "Medications",
                sum(
                    len(
                        r.get(
                            "medications",
                            []
                        )
                    )
                    for r in patient_records
                )
            )

        with p4:

            st.metric(
                "Allergies",
                sum(
                    len(
                        r.get(
                            "allergies",
                            []
                        )
                    )
                    for r in patient_records
                )
            )

        st.markdown(
            '<div class="section-title">'
            'Patient Timeline'
            '</div>',
            unsafe_allow_html=True
        )

        for r in reversed(patient_records):

            with st.container(border=True):

                st.markdown(
                     f"### {r.get('record_type') or 'Medical Record'}"
)

                st.caption(
                    f"{r.get('record_date', '')} | "
                    f"{r.get('hospital', 'Unknown')}"
                )

                st.write(
                    r.get(
                        "assessment",
                        "No assessment available."
                    )
                )

             
# ============================================================
# UPLOAD & PROCESS
# ============================================================

elif st.session_state.page == "Upload Record":

    st.markdown(
        '<div class="section-title">Upload & Process</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Convert medical documents into structured patient information.'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # PROCESSING STEPS
    #
    # IMPORTANT:
    # HTML starts directly after the triple quote.
    # It is NOT indented, so Streamlit will render it as HTML
    # instead of displaying it as a code block.
    # --------------------------------------------------------

    s1, s2, s3, s4 = st.columns(
        4,
        gap="medium"
    )

    with s1:

        st.markdown(
"""<div class="upload-step">
<div class="upload-step-number">01</div>
<div class="upload-step-title">Document</div>
<div class="upload-step-description">PDF / DOCX / TXT</div>
</div>""",
            unsafe_allow_html=True
        )

    with s2:

        st.markdown(
"""<div class="upload-step">
<div class="upload-step-number">02</div>
<div class="upload-step-title">Extraction</div>
<div class="upload-step-description">Read document</div>
</div>""",
            unsafe_allow_html=True
        )

    with s3:

        st.markdown(
"""<div class="upload-step">
<div class="upload-step-number">03</div>
<div class="upload-step-title">AI Structuring</div>
<div class="upload-step-description">Prepare information</div>
</div>""",
            unsafe_allow_html=True
        )

    with s4:

        st.markdown(
"""<div class="upload-step">
<div class="upload-step-number">04</div>
<div class="upload-step-title">Patient Record</div>
<div class="upload-step-description">Store information</div>
</div>""",
            unsafe_allow_html=True
        )

    st.write("")

    # --------------------------------------------------------
    # UPLOAD BOX
    # --------------------------------------------------------

    st.markdown(
        '<div class="upload-box">',
        unsafe_allow_html=True
    )

    uploaded = st.file_uploader(
        "Select medical document",
        type=[
            "pdf",
            "docx",
            "txt"
        ],
        help="Upload a medical PDF, DOCX or TXT document.",
        key="medical_document_upload"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    if uploaded:

        st.success(
            f"Selected: {uploaded.name}"
        )

        st.write("")

        if st.button(
            "Process Medical Record",
            type="primary",
            use_container_width=True,
            key="process_record"
        ):
        #new code adding here this is processing the extracting file but its still not complete just showing when uploaded need to maintain a record of this
            import tempfile
            from pathlib import Path
            from extraction import read_document, read_pdf, read_docx

            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = Path(temp_dir) / Path(uploaded.name).name
                file_path.write_bytes(uploaded.getvalue())

                if file_path.suffix.lower() == ".pdf":
                    extracted_text = read_pdf(file_path)
                elif file_path.suffix.lower() == ".docx":
                    extracted_text = read_docx(file_path)
                elif file_path.suffix.lower() == ".txt":
                    extracted_text = read_document(file_path)
                else:
                    extracted_text = ""

            if extracted_text.strip():
                st.success("Document text extracted successfully!")

                with st.expander("View Extracted Text"):
                    st.text(extracted_text)

                with st.spinner("AI is analyzing the medical record..."):
                    structured_data = structure_with_gemini(extracted_text)

                    if not structured_data:
                        structured_data = structure_with_python(extracted_text)

                st.subheader("Extracted Clinical Information")
                st.json(structured_data)

                # Create record using actual extracted information
                record = {
                    "patient_name": structured_data.get("patient_name"),
                    "patient_id": structured_data.get("patient_id"),
                    "record_type": structured_data.get("record_type"),
                    "record_date": structured_data.get("record_date"),
                    "hospital": structured_data.get("hospital"),
                    "source": uploaded.name,
                    "symptoms": structured_data.get("symptoms", []),
                    "labs": structured_data.get("lab_results", []),
                    "medications": structured_data.get("medications", []),
                    "allergies": structured_data.get("allergies", []),
                    "assessment": structured_data.get("assessment")
                }

                # Prepare the extracted data for PostgreSQL
                database_record = structured_data.copy()

                database_record["record_type"] = (
                    structured_data.get("record_type") or "Medical Record"
                )

                database_record["content"] = extracted_text
                database_record["source"] = uploaded.name

                # Save the medical record to PostgreSQL
                saved = insert_medical_record(database_record) 

                if saved is True:
                    st.session_state.records.append(record)

                    st.success("Medical record processed successfully.")

                elif saved == "duplicate":
                    st.warning(
                        "This medical record has already been uploaded."
                    )

                else:
                    st.error(
                        "Unable to save the medical record. Please try again."
                    ) 
            else:
                st.error("No readable text found in the document.")
                #new code end

# ============================================================
# CLINICAL DATA
# ============================================================

elif st.session_state.page == "Clinical Data":

    st.markdown(
        '<div class="section-title">Clinical Data</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Review laboratory results, medications and allergies.'
        '</div>',
        unsafe_allow_html=True
    )

    labs_tab, medications_tab, allergies_tab = st.tabs(
        [
            "Laboratory Results",
            "Medications",
            "Allergies"
        ]
    )

    # --------------------------------------------------------
    # LABS
    # --------------------------------------------------------

    with labs_tab:

        # Get all unique patients
        patients = {}

        for r in st.session_state.records:
            patient_id = r.get("patient_id")
            patient_name = r.get("patient_name") or "Unknown Patient"

            if patient_id:
                patients[patient_id] = patient_name

        if patients:

            # Choose which patient's labs to view
            selected_patient_id = st.selectbox(
                "Select Patient",
                options=list(patients.keys()),
                format_func=lambda pid: f"{patients[pid]} ({pid})",
                key="labs_patient_selector"
            )

            lab_rows = []

            # Collect lab results from ALL records of this patient
            for r in st.session_state.records:

                if r.get("patient_id") != selected_patient_id:
                    continue

                for lab in r.get("labs", []):

                    if isinstance(lab, dict):

                        lab_rows.append(
                            {
                                "Date": r.get("record_date") or "Unknown",
                                "Test": (
                                    lab.get("lab_name")
                                    or lab.get("name")
                                    or "Unknown Test"
                                ),
                                "Value": lab.get("value", ""),
                                "Unit": lab.get("unit", "")
                            }
                        )

            st.subheader("Cumulative Laboratory Results")

            if lab_rows:

                df = pd.DataFrame(lab_rows)

                df["_sort_date"] = pd.to_datetime(
                    df["Date"],
                    errors="coerce"
                )

                df = df.sort_values(
                    "_sort_date",
                    ascending=True
                ).drop(columns=["_sort_date"])

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info(
                    "No laboratory results found for this patient."
                )
            # Automatic Laboratory Trends
            st.subheader("Laboratory Trends")

            if lab_rows:

                trends_df = pd.DataFrame(lab_rows)

                # Convert values and dates into usable formats
                trends_df["Numeric Value"] = pd.to_numeric(
                    trends_df["Value"],
                    errors="coerce"
                )

                trends_df["Date"] = pd.to_datetime(
                    trends_df["Date"],
                    errors="coerce"
                )

                # Only use results with valid dates and numeric values
                trends_df = trends_df.dropna(
                    subset=["Date", "Numeric Value"]
                )

                # Count results for each test and unit
                test_counts = trends_df.groupby(
                    ["Test", "Unit"]
                ).size()

                available_tests = [
                    (test, unit)
                    for (test, unit), count in test_counts.items()
                    if count >= 2
                ]

                if available_tests:

                    selected_test = st.selectbox(
                        "Select Laboratory Test",
                        available_tests,
                        format_func=lambda item: (
                            f"{item[0]} ({item[1]})"
                            if item[1] else item[0]
                        ),
                        key="laboratory_trend_selector"
                    )

                    test_name, test_unit = selected_test

                    trend_data = trends_df[
                        (trends_df["Test"] == test_name) &
                        (trends_df["Unit"] == test_unit)
                    ].sort_values("Date")

                    # Display the trend chart
                    chart_data = trend_data.set_index("Date")[
                        ["Numeric Value"]
                    ]

                    st.line_chart(chart_data)

                    # Describe the change in measured values
                    first_value = trend_data["Numeric Value"].iloc[0]
                    last_value = trend_data["Numeric Value"].iloc[-1]

                    if last_value > first_value:
                        direction = "increased"
                    elif last_value < first_value:
                        direction = "decreased"
                    else:
                        direction = "remained unchanged"

                    st.info(
                        f"{test_name} has {direction} "
                        f"from {first_value:g} to {last_value:g} "
                        f"{test_unit}."
                    )

                    st.caption(
                        "Trends use medical record dates. "
                        "Changes in values do not necessarily indicate "
                        "improvement or deterioration."
                    )

                else:
                    st.info(
                        "At least two numeric results for the same "
                        "laboratory test and unit are needed to show a trend."
                    )

            else:
                st.info(
                    "No laboratory results available for trend analysis."
                )
        else:
            st.info("No patient records available.")

    # --------------------------------------------------------
    # MEDICATIONS
    # --------------------------------------------------------

    with medications_tab:

        st.subheader("Cumulative Medication History")

        if "selected_patient_id" not in locals():
            st.info("Please select a patient in Laboratory Results first.")

        elif selected_patient_id is None:
            st.info("No patient selected.")

        else:
            medication_rows = []

            # Collect medications from ALL records
            # belonging to the selected patient
            for r in st.session_state.records:

                if r.get("patient_id") != selected_patient_id:
                    continue

                for medication in r.get("medications", []):

                    if isinstance(medication, dict):
                        medication_name = (
                            medication.get("name")
                            or medication.get("medication_name")
                            or str(medication)
                        )
                    else:
                        medication_name = str(medication)

                    medication_rows.append(
                        {
                            "Record Date": r.get("record_date") or "Unknown",
                            "Medication": medication_name,
                            "Hospital": r.get("hospital") or "Unknown"
                        }
                    )

            if medication_rows:

                df_medications = pd.DataFrame(medication_rows)

                df_medications["_sort_date"] = pd.to_datetime(
                    df_medications["Record Date"],
                    errors="coerce"
                )

                df_medications = df_medications.sort_values(
                    "_sort_date",
                    ascending=True,
                    na_position="last"
                ).drop(columns=["_sort_date"])

                st.dataframe(
                    df_medications,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info(
                    "No medications found for the selected patient."
                )
    # --------------------------------------------------------
    # ALLERGIES
    # --------------------------------------------------------

    with allergies_tab:

        st.subheader("Cumulative Allergy History")

        if "selected_patient_id" not in locals():
            st.info("Please select a patient in Laboratory Results first.")

        elif selected_patient_id is None:
            st.info("No patient selected.")

        else:
            allergy_rows = []

            # Collect allergies from ALL records
            # belonging to the selected patient
            for r in st.session_state.records:

                if r.get("patient_id") != selected_patient_id:
                    continue

                for allergy in r.get("allergies", []):

                    if isinstance(allergy, dict):
                        allergy_name = (
                            allergy.get("name")
                            or allergy.get("allergen")
                            or allergy.get("allergy_name")
                            or str(allergy)
                        )
                    else:
                        allergy_name = str(allergy)

                    allergy_rows.append(
                        {
                            "Record Date": r.get("record_date") or "Unknown",
                            "Allergy": allergy_name,
                            "Hospital": r.get("hospital") or "Unknown"
                        }
                    )

            if allergy_rows:

                df_allergies = pd.DataFrame(allergy_rows)

                df_allergies["_sort_date"] = pd.to_datetime(
                    df_allergies["Record Date"],
                    errors="coerce"
                )

                df_allergies = df_allergies.sort_values(
                    "_sort_date",
                    ascending=True,
                    na_position="last"
                ).drop(columns=["_sort_date"])

                st.dataframe(
                    df_allergies,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info(
                    "No allergies found for the selected patient."
                )

# ============================================================
# RECORDS
# ============================================================

elif st.session_state.page == "Records":

    st.markdown(
        '<div class="section-title">Medical Records</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Review processed medical documents.'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.records:

        st.info(
            "No medical records available."
        )

    else:

        rows = []

        for r in st.session_state.records:

            rows.append(
                {
                    "Patient":
                        r.get(
                            "patient_name",
                            ""
                        ),

                    "Patient ID":
                        r.get(
                            "patient_id",
                            ""
                        ),

                    "Date":
                        r.get(
                            "record_date",
                            ""
                        ),

                    "Type":
                         r.get("record_type") or "Medical Record",

                    "Source":
                        r.get(
                            "source",
                            ""
                        )
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

        st.markdown(
            '<div class="section-title">'
            'Record Details'
            '</div>',
            unsafe_allow_html=True
        )

        options = [
            f"{i + 1}. {r.get('source', 'Medical Record')}"
            for i, r
            in enumerate(
                st.session_state.records
            )
        ]

        selected = st.selectbox(
            "Select record",
            options
        )

        index = options.index(
            selected
        )

        selected_record = (
            st.session_state.records[index]
        )

        x1, x2, x3 = st.columns(3)

        with x1:

            st.metric(
                "Patient",
                selected_record.get(
                    "patient_name",
                    "Unknown"
                )
            )

        with x2:

            st.metric(
                "Patient ID",
                selected_record.get(
                    "patient_id",
                    "Unknown"
                )
            )

        with x3:

            st.metric(
                "Date",
                selected_record.get(
                    "record_date",
                    "Unknown"
                )
            )

        with st.container(
            border=True
        ):

            st.markdown(
                "### Clinical Assessment"
            )

            st.write(
                selected_record.get(
                    "assessment",
                    "No assessment available."
                )
            )

        st.markdown("### Delete Medical Record")

        confirm_delete = st.checkbox(
            "I understand that deleting this record is permanent.",
            key=f"confirm_delete_{index}"
        )

        if st.button(
            "Delete Record",
            disabled=not confirm_delete
        ):
            record_id = selected_record.get("id")

            if record_id is None:
                st.error(
                    "Database ID missing. Restart the app and try again."
                )

            elif delete_medical_record(record_id):
                st.session_state.records = get_all_medical_records()
                st.success("Medical record deleted successfully.")
                st.rerun()

            else:
                st.error("Could not delete the medical record.")

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Care Continuity AI  |  Connected healthcare information platform"
)

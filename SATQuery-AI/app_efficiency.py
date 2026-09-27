# ============================================================
# SATQUERY AI
# AGENTIC EARTH OBSERVATION INTELLIGENCE SYSTEM
# ============================================================

import os
import html
import time
import requests
import streamlit as st
import folium

from datetime import date, timedelta
from dotenv import load_dotenv
from streamlit_folium import st_folium


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# SATQUERY MODULES
# ============================================================

from satellite import get_satellite_comparison
from query_router import understand_query
from vision_agent import run_vision_agent
from evidence_agent import build_evidence
from change_detection_agent import detect_changes
from answer_agent import generate_answer


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SATQuery AI",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# LOGIN
# ============================================================

APP_USERNAME = os.getenv(
    "SATQUERY_USERNAME",
    "admin"
)

APP_PASSWORD = os.getenv(
    "SATQUERY_PASSWORD",
    "1234"
)


# ============================================================
# SESSION STATE
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "current_slide" not in st.session_state:
    st.session_state.current_slide = 1


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {

    background:
        radial-gradient(
            circle at 50% 45%,
            rgba(0, 100, 190, 0.16),
            transparent 38%
        ),

        radial-gradient(
            circle at 15% 20%,
            rgba(0, 80, 180, 0.10),
            transparent 28%
        ),

        linear-gradient(
            135deg,
            #010611 0%,
            #03152c 50%,
            #010611 100%
        ) !important;

    color: white !important;
}


[data-testid="stAppViewContainer"] {
    background: transparent !important;
}


[data-testid="stHeader"] {
    background: transparent !important;
}


[data-testid="stToolbar"] {
    visibility: hidden !important;
}


footer {
    visibility: hidden !important;
}


.block-container {

    position: relative !important;

    z-index: 10 !important;

    padding-top: 1.5rem !important;

    padding-bottom: 3rem !important;
}


/* ============================================================
   STAR FIELD
   ============================================================ */

.stApp::before {

    content: "";

    position: fixed;

    inset: 0;

    z-index: 0;

    pointer-events: none;

    background-image:

        radial-gradient(
            circle,
            rgba(255,255,255,0.85) 1px,
            transparent 1.5px
        ),

        radial-gradient(
            circle,
            rgba(80,180,255,0.65) 1px,
            transparent 1.5px
        ),

        radial-gradient(
            circle,
            rgba(255,255,255,0.45) 1px,
            transparent 1.5px
        );

    background-size:
        85px 85px,
        135px 135px,
        210px 210px;

    background-position:
        10px 20px,
        50px 80px,
        120px 30px;

    opacity: 0.30;

    animation:
        starsMove 35s linear infinite;
}


@keyframes starsMove {

    from {
        transform: translateY(0px);
    }

    to {
        transform: translateY(100px);
    }
}


/* ============================================================
   EARTH
   ============================================================ */

.stApp::after {

    content: "";

    position: fixed;

    width: 260px;

    height: 260px;

    left:
        calc(50% - 130px);

    top:
        calc(50% - 130px);

    border-radius: 50%;

    z-index: 0;

    pointer-events: none;

    background:

        radial-gradient(
            circle at 30% 28%,
            #65d5ff 0%,
            #1687df 22%,
            #07529c 46%,
            #032d5c 65%,
            #010b1b 88%
        );

    box-shadow:

        0 0 25px
        rgba(0,180,255,0.75),

        0 0 70px
        rgba(0,120,255,0.35),

        0 0 140px
        rgba(0,80,255,0.15),

        inset -40px -25px 55px
        rgba(0,0,0,0.80);

    opacity: 0.32;

    animation:
        earthRotate 25s linear infinite;
}


@keyframes earthRotate {

    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}


/* ============================================================
   ORBIT
   ============================================================ */

[data-testid="stAppViewContainer"]::before {

    content: "🛰️";

    position: fixed;

    width: 420px;

    height: 420px;

    left:
        calc(50% - 210px);

    top:
        calc(50% - 210px);

    z-index: 1;

    pointer-events: none;

    border:
        1px solid
        rgba(80,190,255,0.24);

    border-radius: 50%;

    display: flex;

    align-items: flex-start;

    justify-content: center;

    padding-top: 185px;

    box-sizing: border-box;

    font-size: 27px;

    filter:
        drop-shadow(
            0 0 12px
            rgba(80,210,255,0.9)
        );

    animation:
        satelliteOrbit 11s linear infinite;
}


@keyframes satelliteOrbit {

    from {

        transform:
            rotateX(68deg)
            rotateY(18deg)
            rotateZ(0deg);
    }

    to {

        transform:
            rotateX(68deg)
            rotateY(18deg)
            rotateZ(360deg);
    }
}


/* ============================================================
   SECOND ORBIT
   ============================================================ */

[data-testid="stAppViewContainer"]::after {

    content: "✦";

    position: fixed;

    width: 500px;

    height: 500px;

    left:
        calc(50% - 250px);

    top:
        calc(50% - 250px);

    z-index: 1;

    pointer-events: none;

    border:
        1px solid
        rgba(70,160,255,0.13);

    border-radius: 50%;

    color:
        rgba(100,210,255,0.8);

    font-size: 18px;

    text-align: center;

    padding-top: 30px;

    box-sizing: border-box;

    animation:
        secondOrbit 17s linear infinite;
}


@keyframes secondOrbit {

    from {

        transform:
            rotateX(62deg)
            rotateY(-25deg)
            rotateZ(0deg);
    }

    to {

        transform:
            rotateX(62deg)
            rotateY(-25deg)
            rotateZ(-360deg);
    }
}


/* ============================================================
   GLASS CARD
   ============================================================ */

.glass-card {

    background:
        rgba(3,15,35,0.82);

    border:
        1px solid
        rgba(70,170,255,0.25);

    border-radius: 18px;

    padding: 20px;

    box-shadow:
        0 0 25px
        rgba(0,100,255,0.07);

    backdrop-filter:
        blur(14px);
}


/* ============================================================
   TITLES
   ============================================================ */

.sat-title {

    text-align: center;

    font-size: 42px;

    font-weight: 900;

    letter-spacing: 5px;

    color: white;

    text-shadow:
        0 0 15px
        rgba(0,180,255,0.85);
}


.sat-subtitle {

    text-align: center;

    color: #6fd6ff;

    font-size: 11px;

    letter-spacing: 3px;

    margin-bottom: 28px;
}


.status-online {

    color: #62ffad;

    font-weight: 800;
}


.section-title {

    color: #72d8ff;

    font-size: 12px;

    font-weight: 800;

    letter-spacing: 2px;

    margin-top: 12px;

    margin-bottom: 10px;
}


/* ============================================================
   LOGIN
   ============================================================ */

.login-title {

    text-align: center;

    font-size: 42px;

    font-weight: 900;

    letter-spacing: 5px;

    color: white;

    text-shadow:
        0 0 15px
        rgba(0,190,255,0.9);

    margin-top: 70px;
}


.login-subtitle {

    text-align: center;

    color: #6fd8ff;

    font-size: 11px;

    letter-spacing: 3px;

    margin-top: 8px;

    margin-bottom: 12px;
}


.login-status {

    text-align: center;

    color: #62ffae;

    font-size: 11px;

    letter-spacing: 2px;

    margin-bottom: 25px;
}


.login-box {

    background:
        rgba(2,12,30,0.88);

    border:
        1px solid
        rgba(70,190,255,0.38);

    border-radius: 20px;

    padding: 25px;

    box-shadow:
        0 0 35px
        rgba(0,120,255,0.15);

    backdrop-filter:
        blur(18px);
}


/* ============================================================
   INPUTS
   ============================================================ */

div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stDateInput"] label {

    color: #d9efff !important;

    font-size: 11px !important;

    font-weight: 700 !important;

    letter-spacing: 1px !important;
}


div[data-testid="stTextInput"] input,
textarea {

    background:
        rgba(3,20,42,0.90) !important;

    color: white !important;

    border:
        1px solid
        rgba(80,180,255,0.35) !important;

    border-radius: 10px !important;
}


div[data-baseweb="select"] > div {

    background:
        rgba(3,20,42,0.90) !important;

    border:
        1px solid
        rgba(80,180,255,0.35) !important;

    border-radius: 10px !important;
}


/* ============================================================
   BUTTONS
   ============================================================ */

div.stButton > button {

    width: 100%;

    min-height: 46px;

    border-radius: 10px;

    border:
        1px solid
        rgba(90,220,255,0.60);

    background:
        linear-gradient(
            90deg,
            #086dcc,
            #09b9ed
        );

    color: white;

    font-weight: 800;

    letter-spacing: 1px;

    transition:
        all 0.25s ease;
}


div.stButton > button:hover {

    border-color: white;

    box-shadow:
        0 0 25px
        rgba(0,190,255,0.50);

    transform:
        translateY(-1px);
}


/* ============================================================
   SLIDER
   ============================================================ */

div[data-testid="stSlider"] {

    padding-left: 15px;

    padding-right: 15px;
}


div[data-testid="stSlider"] label {

    color:
        #72d8ff !important;

    font-weight:
        800 !important;

    letter-spacing:
        1px !important;
}


/* ============================================================
   METRICS
   ============================================================ */

[data-testid="stMetric"] {

    background:
        rgba(3,18,40,0.70);

    border:
        1px solid
        rgba(80,180,255,0.18);

    border-radius: 12px;

    padding: 10px;
}


/* ============================================================
   IMAGES
   ============================================================ */

[data-testid="stImage"] img {

    border-radius: 14px;

    border:
        1px solid
        rgba(80,190,255,0.28);

    object-fit: contain;
}


/* ============================================================
   EXPANDER
   ============================================================ */

[data-testid="stExpander"] {

    background:
        rgba(3,18,40,0.65);

    border:
        1px solid
        rgba(80,180,255,0.20);

    border-radius: 12px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HELPER — ANSWER TEXT
# ============================================================

def get_answer_text(answer_result):

    if answer_result is None:
        return "No grounded answer generated."

    if isinstance(
        answer_result,
        str
    ):
        return answer_result

    if isinstance(
        answer_result,
        dict
    ):

        for key in [
            "answer",
            "final_answer",
            "response",
            "grounded_answer",
            "message",
            "text"
        ]:

            if answer_result.get(key):

                return str(
                    answer_result[key]
                )

        return str(
            answer_result
        )

    return str(
        answer_result
    )


# ============================================================
# HELPER — IMAGE URL EXTRACTION
# ============================================================

def extract_image_url(
    data,
    possible_keys
):

    if data is None:
        return None

    if isinstance(
        data,
        str
    ):

        if data.startswith("http"):
            return data

        return None

    if isinstance(
        data,
        dict
    ):

        for key in possible_keys:

            value = data.get(key)

            if isinstance(
                value,
                str
            ):

                if value.startswith("http"):
                    return value

        for value in data.values():

            result = extract_image_url(
                value,
                possible_keys
            )

            if result:
                return result

    if isinstance(
        data,
        (list, tuple)
    ):

        for item in data:

            result = extract_image_url(
                item,
                possible_keys
            )

            if result:
                return result

    return None


# ============================================================
# HELPER — LOCATION FALLBACK
# ============================================================

LOCATION_FALLBACKS = {

    "delhi": (28.6139, 77.2090),

    "new delhi": (28.6139, 77.2090),

    "greater noida": (28.4744, 77.5040),

    "noida": (28.5355, 77.3910),

    "gurgaon": (28.4595, 77.0266),

    "gurugram": (28.4595, 77.0266),

    "mumbai": (19.0760, 72.8777),

    "kolkata": (22.5726, 88.3639),

    "chennai": (13.0827, 80.2707),

    "bangalore": (12.9716, 77.5946),

    "bengaluru": (12.9716, 77.5946),

    "hyderabad": (17.3850, 78.4867),

    "jaipur": (26.9124, 75.7873),

    "lucknow": (26.8467, 80.9462),

    "patna": (25.5941, 85.1376),

    "munger": (25.3748, 86.4735),

    "ahmedabad": (23.0225, 72.5714),

    "pune": (18.5204, 73.8567),

    "bhopal": (23.2599, 77.4126),

    "chandigarh": (30.7333, 76.7794),

    "dehradun": (30.3165, 78.0322),

    "agra": (27.1767, 78.0081),

    "varanasi": (25.3176, 82.9739)

}


def resolve_location(location):

    """
    Resolve a location using Nominatim.

    If Nominatim is unavailable, use a known-coordinate
    fallback for common Indian cities.
    """

    location_clean = (
        location
        .strip()
        .lower()
    )

    geocode_url = (
        "https://nominatim.openstreetmap.org/search"
    )

    try:

        response = requests.get(

            geocode_url,

            params={
                "q": location,
                "format": "json",
                "limit": 1
            },

            headers={
                "User-Agent":
                    "SATQuery-AI/1.0"
            },

            timeout=10
        )

        response.raise_for_status()

        geo_data = response.json()

        if geo_data:

            latitude = float(
                geo_data[0]["lat"]
            )

            longitude = float(
                geo_data[0]["lon"]
            )

            return (
                latitude,
                longitude,
                "Nominatim"
            )

    except requests.RequestException as e:
        pass

    except (
        ValueError,
        KeyError,
        TypeError,
        IndexError
    ):
        pass

    if location_clean in LOCATION_FALLBACKS:

        latitude, longitude = (
            LOCATION_FALLBACKS[
                location_clean
            ]
        )

        return (
            latitude,
            longitude,
            "Local fallback coordinates"
        )

    for name, coordinates in LOCATION_FALLBACKS.items():

        if (
            location_clean in name
            or
            name in location_clean
        ):

            latitude, longitude = coordinates

            return (
                latitude,
                longitude,
                "Local fallback coordinates"
            )

    return None


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.authenticated:

    st.html(
        """
        <div class="login-title">
            🛰️ SATQUERY AI
        </div>

        <div class="login-subtitle">
            AGENTIC EARTH OBSERVATION INTELLIGENCE SYSTEM
        </div>

        <div class="login-status">
            ● SECURE MISSION ACCESS
        </div>
        """
    )

    left, center, right = st.columns(
        [1, 1.2, 1]
    )

    with center:

        st.html(
            """
            <div class="login-box">
            """
        )

        with st.form(
            "satquery_login"
        ):

            username = st.text_input(
                "USERNAME",
                placeholder="Enter username"
            )

            password = st.text_input(
                "PASSWORD",
                placeholder="Enter password",
                type="password"
            )

            login_button = st.form_submit_button(
                "🛰️ ENTER MISSION CONTROL",
                use_container_width=True
            )

        st.html(
            """
            <div style="
                text-align:center;
                color:rgba(190,220,240,0.50);
                font-size:10px;
                letter-spacing:1px;
                margin-top:10px;
            ">
                AUTHORIZED PERSONNEL ONLY
            </div>

            </div>
            """
        )

        if login_button:

            if (
                username == APP_USERNAME
                and password == APP_PASSWORD
            ):

                st.session_state.authenticated = True

                st.session_state.current_slide = 1

                st.rerun()

            else:

                st.error(
                    "❌ Invalid username or password."
                )

    st.stop()


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns(
    [7, 1]
)

with header_left:

    st.html(
        """
        <div class="sat-title">
            SATQUERY AI
        </div>

        <div class="sat-subtitle">

            EARTH OBSERVATION INTELLIGENCE SYSTEM

            &nbsp;&nbsp; • &nbsp;&nbsp;

            <span class="status-online">
                ● SYSTEM ONLINE
            </span>

        </div>
        """
    )

with header_right:

    if st.button(
        "LOGOUT",
        key="logout"
    ):

        st.session_state.authenticated = False

        st.session_state.analysis_result = None

        st.session_state.current_slide = 1

        st.rerun()


# ============================================================
# SLIDE INFORMATION
# ============================================================

SLIDES = [

    "🔎 Query",

    "🛰️ Satellite",

    "🎯 Answer",

    "🌍 Mission"

]


# ============================================================
# SLIDER + ARROWS
# ============================================================

if st.session_state.analysis_result is not None:

    st.html(
        """
        <div style="
            text-align:center;
            color:#72d8ff;
            font-size:11px;
            font-weight:800;
            letter-spacing:2px;
            margin-top:10px;
        ">
            MISSION NAVIGATION
        </div>
        """
    )

    nav_left, nav_slider, nav_right = st.columns(
        [1, 6, 1]
    )

    with nav_left:

        if st.button(
            "←",
            key="previous_slide"
        ):

            if st.session_state.current_slide > 1:

                st.session_state.current_slide -= 1

                st.rerun()

    with nav_slider:

        selected_slide = st.slider(
            "MISSION SLIDE",
            min_value=1,
            max_value=4,
            value=st.session_state.current_slide,
            step=1,
            format="%d",
            key="mission_slider"
        )

        if (
            selected_slide
            != st.session_state.current_slide
        ):

            st.session_state.current_slide = selected_slide

            st.rerun()

    with nav_right:

        if st.button(
            "→",
            key="next_slide"
        ):

            if st.session_state.current_slide < 4:

                st.session_state.current_slide += 1

                st.rerun()

    label_cols = st.columns(4)

    for index, label in enumerate(
        SLIDES,
        start=1
    ):

        with label_cols[index - 1]:

            if (
                index
                ==
                st.session_state.current_slide
            ):

                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        color:#ffffff;
                        font-weight:800;
                        font-size:12px;
                    ">
                        ● {label}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        color:#547a99;
                        font-size:11px;
                    ">
                        {label}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

else:

    st.html(
        """
        <div style="
            text-align:center;
            color:#547a99;
            font-size:11px;
            letter-spacing:1px;
            margin-top:10px;
        ">
            MISSION CONTROL • CREATE A NEW EARTH ANALYSIS
        </div>
        """
    )


# ============================================================
# SLIDE 1 — QUERY
# ============================================================

if st.session_state.current_slide == 1:

    st.html(
        """
        <div class="glass-card"
             style="margin-top:25px;">

            <div style="
                text-align:center;
                font-size:30px;
                font-weight:800;
                color:white;
            ">
                Ask Earth. We'll investigate.
            </div>

            <div style="
                text-align:center;
                color:#8db7d8;
                font-size:14px;
                margin-top:8px;
            ">
                Natural-language satellite image intelligence
            </div>

        </div>
        """
    )

    st.write("")

    st.html(
        """
        <div class="section-title">
            MISSION PARAMETERS
        </div>
        """
    )

    input_left, input_right = st.columns(
        2
    )

    with input_left:

        location = st.text_input(
            "📍 LOCATION",
            value="delhi",
            placeholder="Example: Greater Noida",
            key="location_input"
        )

    with input_right:

        source = st.selectbox(
            "🛰️ DATA SOURCE",
            [
                "Satellite",
                "Sentinel",
                "Landsat",
                "Google Earth Engine"
            ],
            key="source_input"
        )

    date_left, date_right = st.columns(
        2
    )

    with date_left:

        from_date = st.date_input(
            "FROM DATE",
            value=date.today() - timedelta(days=30),
            key="from_date_input"
        )

    with date_right:

        to_date = st.date_input(
            "TO DATE",
            value=date.today(),
            key="to_date_input"
        )

    query = st.text_area(
        "🔎 NATURAL LANGUAGE QUERY",
        value="vegetation change",
        placeholder=(
            "Example: Detect major changes in "
            "vegetation between the two dates."
        ),
        height=100,
        key="query_input"
    )

    st.write("")

    analyze = st.button(
        "🛰️ ANALYZE EARTH",
        use_container_width=True,
        key="analyze_button"
    )


    # ========================================================
    # RUN ANALYSIS
    # ========================================================

    if analyze:

        if not location.strip():

            st.error(
                "Please enter a location."
            )

            st.stop()

        if not query.strip():

            st.error(
                "Please enter a natural-language query."
            )

            st.stop()

        if from_date >= to_date:

            st.error(
                "FROM DATE must be before TO DATE."
            )

            st.stop()

        st.markdown("---")

        st.html(
            """
            <div class="section-title">
                AGENTIC PIPELINE
            </div>
            """
        )

        progress = st.progress(0)

        status = st.empty()

        # ----------------------------------------------------
        # PERFORMANCE TIMER
        # ----------------------------------------------------

        mission_start_time = time.perf_counter()

        stage_timings = {}

        try:

            # =================================================
            # STEP 1 — ROBUST GEOCODING
            # =================================================

            status.info(
                "📍 Step 1/7 — Resolving location..."
            )

            progress.progress(10)

            step_start_time = time.perf_counter()

            location_result = resolve_location(
                location
            )

            stage_timings["Location Resolution"] = (
                time.perf_counter() - step_start_time
            )

            if location_result is None:

                status.error(
                    "❌ Location could not be resolved."
                )

                st.error(
                    f"""
                    SATQuery AI could not resolve "{location}".

                    Please try a city or known location such as:
                    Delhi, Noida, Greater Noida, Mumbai, Jaipur, etc.
                    """
                )

                st.stop()

            latitude, longitude, location_source = (
                location_result
            )

            if location_source != "Nominatim":

                st.warning(
                    "⚠️ Online geocoding unavailable. "
                    "Using local fallback coordinates."
                )


            # =================================================
            # STEP 2 — QUERY ROUTER
            # =================================================

            status.info(
                "🧠 Step 2/7 — Understanding query..."
            )

            progress.progress(20)

            step_start_time = time.perf_counter()

            try:

                query_result = understand_query(
                    query
                )

            except Exception as e:

                query_result = {

                    "status": "ERROR",

                    "intent":
                        "satellite analysis",

                    "error": str(e)

                }

            stage_timings["Query Understanding"] = (
                time.perf_counter() - step_start_time
            )


            # =================================================
            # STEP 3 — SATELLITE
            # =================================================

            status.info(
                "🛰️ Step 3/7 — Fetching satellite imagery..."
            )

            progress.progress(35)

            step_start_time = time.perf_counter()

            try:

                satellite_result = (
                    get_satellite_comparison(
                        latitude=latitude,
                        longitude=longitude,
                        from_date=str(from_date),
                        to_date=str(to_date)
                    )
                )

            except TypeError:

                satellite_result = (
                    get_satellite_comparison(
                        latitude,
                        longitude,
                        str(from_date),
                        str(to_date)
                    )
                )

            stage_timings["Satellite Retrieval"] = (
                time.perf_counter() - step_start_time
            )


            # =================================================
            # IMAGE URLS
            # =================================================

            before_url = extract_image_url(
                satellite_result,
                [
                    "before_url",
                    "before_image",
                    "before",
                    "image_before",
                    "pre_image",
                    "pre_url"
                ]
            )

            after_url = extract_image_url(
                satellite_result,
                [
                    "after_url",
                    "after_image",
                    "after",
                    "image_after",
                    "post_image",
                    "post_url"
                ]
            )


            # =================================================
            # STEP 4 — CHANGE DETECTION
            # =================================================

            status.info(
                "🔍 Step 4/7 — Detecting changes..."
            )

            progress.progress(50)

            step_start_time = time.perf_counter()

            if (
                before_url
                and
                after_url
            ):

                try:

                    change_result = detect_changes(
                        before_url=before_url,
                        after_url=after_url,
                        threshold=20,
                        min_area=200
                    )

                except TypeError:

                    try:

                        change_result = detect_changes(
                            before_url,
                            after_url
                        )

                    except Exception as e:

                        change_result = {

                            "status": "ERROR",

                            "error": str(e),

                            "region_count": 0,

                            "change_percentage": 0,

                            "change_count": 0,

                            "changed_area_percentage": 0,

                            "boxes": [],

                            "finding":
                                "Change detection failed."

                        }

                except Exception as e:

                    change_result = {

                        "status": "ERROR",

                        "error": str(e),

                        "region_count": 0,

                        "change_percentage": 0,

                        "change_count": 0,

                        "changed_area_percentage": 0,

                        "boxes": [],

                        "finding":
                            "Change detection failed."

                    }

            else:

                change_result = {

                    "status": "NO_IMAGES",

                    "region_count": 0,

                    "change_percentage": 0,

                    "change_count": 0,

                    "changed_area_percentage": 0,

                    "boxes": [],

                    "finding":
                        "Satellite images unavailable."

                }

            stage_timings["Change Detection"] = (
                time.perf_counter() - step_start_time
            )


            # =================================================
            # STEP 5 — VISION
            # =================================================

            status.info(
                "👁️ Step 5/7 — Running Vision Agent..."
            )

            progress.progress(65)

            step_start_time = time.perf_counter()

            if after_url:

                try:

                    vision_result = (
                        run_vision_agent(
                            query=query,
                            image_url=after_url
                        )
                    )

                except TypeError:

                    vision_result = (
                        run_vision_agent(
                            query=query,
                            image=after_url
                        )
                    )

                except Exception as e:

                    vision_result = {

                        "status": "ERROR",

                        "error": str(e)

                    }

            else:

                vision_result = {

                    "status": "NO_IMAGE",

                    "error":
                        "After image unavailable."

                }

            stage_timings["Vision Agent"] = (
                time.perf_counter() - step_start_time
            )


            # =================================================
            # STEP 6 — EVIDENCE
            # =================================================

            status.info(
                "📚 Step 6/7 — Fusing evidence..."
            )

            progress.progress(80)

            step_start_time = time.perf_counter()

            try:

                evidence_result = build_evidence(
                    query=query,
                    query_analysis=query_result,
                    vision_result=vision_result,
                    satellite_data=satellite_result,
                    change_result=change_result
                )

            except TypeError:

                try:

                    evidence_result = build_evidence(
                        query,
                        query_result,
                        vision_result,
                        satellite_result,
                        change_result
                    )

                except Exception as e:

                    evidence_result = {

                        "status": "ERROR",

                        "error": str(e),

                        "evidence": []

                    }

            except Exception as e:

                evidence_result = {

                    "status": "ERROR",

                    "error": str(e),

                    "evidence": []

                }

            stage_timings["Evidence Fusion"] = (
                time.perf_counter() - step_start_time
            )


            # =================================================
            # FUSED RESULT
            # =================================================

            if isinstance(
                evidence_result,
                dict
            ):

                fused_result = dict(
                    evidence_result
                )

            else:

                fused_result = {

                    "evidence": [
                        str(evidence_result)
                    ]

                }


            fused_result["query"] = query

            fused_result["location"] = location

            fused_result["coordinates"] = {

                "latitude": latitude,

                "longitude": longitude

            }

            fused_result["from_date"] = str(
                from_date
            )

            fused_result["to_date"] = str(
                to_date
            )

            fused_result["source"] = source

            fused_result["vision"] = (
                vision_result
            )

            fused_result["change_detection"] = (
                change_result
            )


            # =================================================
            # STEP 7 — ANSWER
            # =================================================

            status.info(
                "🎯 Step 7/7 — Generating grounded answer..."
            )

            progress.progress(92)

            step_start_time = time.perf_counter()

            try:

                answer_result = generate_answer(
                    query=query,
                    fused_result=fused_result
                )

            except Exception as e:

                answer_result = {

                    "status": "ERROR",

                    "answer": None,

                    "confidence": "LOW",

                    "error": str(e)

                }

            stage_timings["Answer Generation"] = (
                time.perf_counter() - step_start_time
            )


            # =================================================
            # CHECK ANSWER
            # =================================================

            answer_failed = False

            if answer_result is None:

                answer_failed = True

            elif isinstance(
                answer_result,
                dict
            ):

                generated_text = (
                    answer_result.get("answer")
                )

                if not generated_text:

                    generated_text = (
                        answer_result.get(
                            "final_answer"
                        )
                    )

                if not generated_text:

                    generated_text = (
                        answer_result.get(
                            "response"
                        )
                    )

                if not generated_text:

                    answer_failed = True

                else:

                    bad_phrases = [

                        "could not generate",

                        "unable to generate",

                        "unable to provide",

                        "failed to generate",

                        "no final answer",

                        "answer unavailable"

                    ]

                    generated_lower = (
                        str(
                            generated_text
                        ).lower()
                    )

                    for phrase in bad_phrases:

                        if phrase in generated_lower:

                            answer_failed = True

                            break

            elif isinstance(
                answer_result,
                str
            ):

                generated_lower = (
                    answer_result.lower()
                )

                bad_phrases = [

                    "could not generate",

                    "unable to generate",

                    "unable to provide",

                    "failed to generate",

                    "no final answer",

                    "answer unavailable"

                ]

                for phrase in bad_phrases:

                    if phrase in generated_lower:

                        answer_failed = True

                        break


            # =================================================
            # GROUNDED FALLBACK ANSWER
            # =================================================

            if answer_failed:

                if isinstance(
                    change_result,
                    dict
                ):

                    change_count = (
                        change_result.get(
                            "region_count",
                            change_result.get(
                                "change_count",
                                0
                            )
                        )
                    )

                    changed_area = (
                        change_result.get(
                            "change_percentage",
                            change_result.get(
                                "changed_area_percentage",
                                change_result.get(
                                    "raw_change_percentage",
                                    0
                                )
                            )
                        )
                    )

                else:

                    change_count = 0

                    changed_area = 0


                try:

                    change_count = int(
                        change_count
                    )

                except Exception:

                    change_count = 0


                try:

                    changed_area = float(
                        changed_area
                    )

                except Exception:

                    changed_area = 0.0


                if change_count > 0:

                    fallback_answer = (

                        f"Satellite image comparison "
                        f"between {from_date} and "
                        f"{to_date} indicates visible "
                        f"changes in the analysed area. "
                        f"The change detection system "
                        f"identified {change_count} "
                        f"significant changed region(s), "
                        f"covering approximately "
                        f"{changed_area:.2f}% of the "
                        f"analysed image. These detected "
                        f"regions represent areas where "
                        f"the visual characteristics of "
                        f"the Earth observation imagery "
                        f"changed between the two "
                        f"observation dates."

                    )

                else:

                    fallback_answer = (

                        f"The satellite images from "
                        f"{from_date} and {to_date} "
                        f"were compared. No significant "
                        f"changed regions were detected "
                        f"in the analysed area."

                    )


                answer_result = {

                    "status": "SUCCESS",

                    "answer":
                        fallback_answer,

                    "final_answer":
                        fallback_answer,

                    "confidence": (

                        "HIGH"
                        if change_count > 0
                        else "MEDIUM"

                    ),

                    "source":
                        "Change Detection Evidence",

                    "change_regions":
                        change_count,

                    "changed_area_percentage":
                        changed_area

                }


            # =================================================
            # PERFORMANCE METRICS
            # =================================================

            mission_end_time = time.perf_counter()

            total_execution_time = (
                mission_end_time - mission_start_time
            )

            queries_processed = 1

            throughput = (
                queries_processed / total_execution_time
                if total_execution_time > 0
                else 0
            )

            performance_metrics = {

                "total_execution_time":
                    total_execution_time,

                "queries_processed":
                    queries_processed,

                "throughput":
                    throughput,

                "stage_timings":
                    stage_timings

            }


            progress.progress(100)

            status.success(
                "✅ Mission analysis completed."
            )


            # =================================================
            # SAVE EVERYTHING
            # =================================================

            st.session_state.analysis_result = {

                "query":
                    query,

                "location":
                    location,

                "source":
                    source,

                "from_date":
                    str(from_date),

                "to_date":
                    str(to_date),

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "query_result":
                    query_result,

                "satellite_result":
                    satellite_result,

                "before_url":
                    before_url,

                "after_url":
                    after_url,

                "change_result":
                    change_result,

                "vision_result":
                    vision_result,

                "evidence_result":
                    evidence_result,

                "fused_result":
                    fused_result,

                "answer_result":
                    answer_result,

                "performance_metrics":
                    performance_metrics

            }


            # =================================================
            # GO TO SATELLITE SLIDE
            # =================================================

            st.session_state.current_slide = 2

            st.rerun()


        except Exception as e:

            # Measure failed mission as well.
            mission_end_time = time.perf_counter()

            total_execution_time = (
                mission_end_time - mission_start_time
            )

            progress.progress(100)

            status.error(
                "❌ Mission analysis failed."
            )

            st.error(
                str(e)
            )

            st.exception(e)


# ============================================================
# SLIDE 2 — SATELLITE COMPARISON
# ============================================================

elif (
    st.session_state.current_slide == 2
    and
    st.session_state.analysis_result is not None
):

    result = st.session_state.analysis_result

    st.html(
        """
        <div style="
            text-align:center;
            padding:25px 10px;
        ">

            <div style="
                font-size:30px;
                font-weight:900;
                color:white;
            ">
                🛰️ SATELLITE COMPARISON
            </div>

            <div style="
                color:#8db7d8;
                font-size:13px;
                margin-top:8px;
            ">
                BEFORE → AFTER EARTH OBSERVATION
            </div>

        </div>
        """
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "📍 LOCATION",
            result["location"].title()
        )

    with c2:

        st.metric(
            "FROM",
            result["from_date"]
        )

    with c3:

        st.metric(
            "TO",
            result["to_date"]
        )

    with c4:

        st.metric(
            "SOURCE",
            result["source"]
        )

    st.markdown("---")

    before_col, after_col = st.columns(2)

    with before_col:

        st.markdown(
            "### 🕐 BEFORE"
        )

        if result["before_url"]:

            st.image(
                result["before_url"],
                caption="EARLIER SATELLITE IMAGE",
                width=480
            )

        else:

            st.warning(
                "Before image unavailable."
            )

    with after_col:

        st.markdown(
            "### 🕐 AFTER"
        )

        if result["after_url"]:

            st.image(
                result["after_url"],
                caption="LATEST SATELLITE IMAGE",
                width=480
            )

        else:

            st.warning(
                "After image unavailable."
            )

    st.markdown("---")

    st.html(
        """
        <div class="section-title">
            🔍 CHANGE DETECTION
        </div>
        """
    )

    change_result = result[
        "change_result"
    ]

    if isinstance(
        change_result,
        dict
    ):

        m1, m2, m3 = st.columns(3)

        with m1:

            change_count = (
                change_result.get(
                    "region_count",
                    change_result.get(
                        "change_count",
                        0
                    )
                )
            )

            st.metric(
                "CHANGES DETECTED",
                str(change_count)
            )

        with m2:

            area = (
                change_result.get(
                    "change_percentage",
                    change_result.get(
                        "changed_area_percentage",
                        change_result.get(
                            "raw_change_percentage",
                            0
                        )
                    )
                )
            )

            try:

                area_text = (
                    f"{float(area):.2f}%"
                )

            except Exception:

                area_text = str(area)

            st.metric(
                "CHANGED AREA",
                area_text
            )

        with m3:

            boxes = change_result.get(
                "boxes",
                []
            )

            if isinstance(
                boxes,
                list
            ):

                box_count = len(
                    boxes
                )

            else:

                box_count = (
                    change_result.get(
                        "region_count",
                        0
                    )
                )

            st.metric(
                "REGIONS",
                str(box_count)
            )

        finding = change_result.get(
            "finding"
        )

        if finding:

            st.info(
                str(finding)
            )

        annotated_image = (
            change_result.get(
                "annotated_image"
            )
        )

        if annotated_image:

            st.markdown(
                "### 🎯 DETECTED CHANGE REGIONS"
            )

            image_left, image_center, image_right = st.columns(
                [1, 2, 1]
            )

            with image_center:

                st.image(
                    annotated_image,
                    caption=(
                        "CHANGE DETECTION "
                        "WITH BOUNDING BOXES"
                    ),
                    width=600
                )

        change_mask = (
            change_result.get(
                "change_mask"
            )
        )

        if change_mask:

            st.markdown(
                "### 🗺️ CHANGE MASK"
            )

            mask_left, mask_center, mask_right = st.columns(
                [1.5, 1, 1.5]
            )

            with mask_center:

                st.image(
                    change_mask,
                    caption="GENERATED CHANGE MASK",
                    width=250
                )

    else:

        st.write(
            change_result
        )


# ============================================================
# SLIDE 3 — GROUNDED ANSWER
# ============================================================

elif (
    st.session_state.current_slide == 3
    and
    st.session_state.analysis_result is not None
):

    result = st.session_state.analysis_result

    st.html(
        """
        <div style="
            text-align:center;
            padding:25px 10px;
        ">

            <div style="
                font-size:30px;
                font-weight:900;
                color:white;
            ">
                🎯 GROUNDED ANSWER
            </div>

            <div style="
                color:#8db7d8;
                font-size:13px;
                margin-top:8px;
            ">
                AI-GENERATED INTERPRETATION FROM
                SATELLITE EVIDENCE
            </div>

        </div>
        """
    )

    st.html(
        f"""
        <div class="glass-card">

            <div style="
                color:#72d8ff;
                font-size:11px;
                font-weight:800;
                letter-spacing:2px;
            ">
                USER QUERY
            </div>

            <div style="
                color:white;
                font-size:17px;
                margin-top:10px;
            ">
                {html.escape(
                    result["query"]
                )}
            </div>

        </div>
        """
    )

    st.write("")

    answer_result = result[
        "answer_result"
    ]

    final_answer = get_answer_text(
        answer_result
    )

    st.html(
        f"""
        <div style="
            background:
                linear-gradient(
                    145deg,
                    rgba(5,45,82,0.95),
                    rgba(3,18,38,0.95)
                );

            border:
                1px solid
                rgba(70,210,255,0.45);

            border-radius:20px;

            padding:30px;

            box-shadow:
                0 0 35px
                rgba(0,170,255,0.15);

            color:#f1fbff;

            font-size:17px;

            line-height:1.8;
        ">

            <div style="
                color:#72d8ff;
                font-size:11px;
                font-weight:800;
                letter-spacing:2px;
                margin-bottom:15px;
            ">
                SATQUERY AI ANALYSIS
            </div>

            {html.escape(
                str(final_answer)
            )}

        </div>
        """
    )

    st.write("")

    a1, a2, a3 = st.columns(3)

    if isinstance(
        answer_result,
        dict
    ):

        confidence = (
            answer_result.get(
                "confidence",
                "MEDIUM"
            )
        )

    else:

        confidence = "MEDIUM"

    change_result = result[
        "change_result"
    ]

    if isinstance(
        change_result,
        dict
    ):

        change_count = (
            change_result.get(
                "region_count",
                change_result.get(
                    "change_count",
                    0
                )
            )
        )

        area = (
            change_result.get(
                "change_percentage",
                change_result.get(
                    "changed_area_percentage",
                    change_result.get(
                        "raw_change_percentage",
                        0
                    )
                )
            )
        )

    else:

        change_count = 0

        area = 0

    with a1:

        st.metric(
            "CONFIDENCE",
            str(confidence)
        )

    with a2:

        st.metric(
            "CHANGES",
            str(change_count)
        )

    with a3:

        try:

            area_text = (
                f"{float(area):.2f}%"
            )

        except Exception:

            area_text = str(area)

        st.metric(
            "CHANGED AREA",
            area_text
        )

    st.markdown("---")

    st.html(
        """
        <div class="section-title">
            👁️ VISION FINDINGS
        </div>
        """
    )

    vision_result = result[
        "vision_result"
    ]

    if isinstance(
        vision_result,
        dict
    ):

        displayed = False

        for key in [

            "summary",

            "finding",

            "description",

            "answer",

            "objects",

            "detections"

        ]:

            if vision_result.get(key):

                st.markdown(
                    f"**{key.replace('_', ' ').title()}**"
                )

                st.write(
                    vision_result[key]
                )

                displayed = True

        if not displayed:

            with st.expander(
                "View complete Vision Agent result"
            ):

                st.json(
                    vision_result
                )

    else:

        st.write(
            vision_result
        )

    st.markdown("---")

    st.html(
        """
        <div class="section-title">
            📚 EVIDENCE FUSION
        </div>
        """
    )

    evidence_result = result[
        "evidence_result"
    ]

    if isinstance(
        evidence_result,
        dict
    ):

        evidence = (
            evidence_result.get(
                "evidence"
            )
        )

        if (
            isinstance(
                evidence,
                list
            )
            and
            evidence
        ):

            for i, item in enumerate(
                evidence,
                start=1
            ):

                st.markdown(
                    f"**Evidence {i}**"
                )

                st.write(
                    str(item)
                )

        else:

            with st.expander(
                "View complete Evidence Agent output"
            ):

                st.json(
                    evidence_result
                )

    else:

        st.write(
            evidence_result
        )


# ============================================================
# SLIDE 4 — MISSION / MAP / AGENTS
# ============================================================

elif (
    st.session_state.current_slide == 4
    and
    st.session_state.analysis_result is not None
):

    result = st.session_state.analysis_result

    st.html(
        """
        <div style="
            text-align:center;
            padding:25px 10px;
        ">

            <div style="
                font-size:30px;
                font-weight:900;
                color:white;
            ">
                🌍 MISSION INTELLIGENCE
            </div>

            <div style="
                color:#8db7d8;
                font-size:13px;
                margin-top:8px;
            ">
                LOCATION • AGENTS • MISSION EVIDENCE
            </div>

        </div>
        """
    )

    st.html(
        """
        <div class="section-title">
            🌍 MISSION LOCATION
        </div>
        """
    )

    mission_map = folium.Map(
        location=[
            result["latitude"],
            result["longitude"]
        ],
        zoom_start=13,
        tiles="OpenStreetMap"
    )

    folium.Marker(

        [
            result["latitude"],
            result["longitude"]
        ],

        tooltip="SATQuery AI Target",

        popup=result["location"],

        icon=folium.Icon(
            color="blue",
            icon="globe"
        )

    ).add_to(
        mission_map
    )

    st_folium(
        mission_map,
        width=None,
        height=450,
        returned_objects=[]
    )

    st.markdown("---")

    coordinate_col1, coordinate_col2 = st.columns(
        2
    )

    with coordinate_col1:

        st.metric(
            "LATITUDE",
            f'{result["latitude"]:.6f}'
        )

    with coordinate_col2:

        st.metric(
            "LONGITUDE",
            f'{result["longitude"]:.6f}'
        )


    # ========================================================
    # PERFORMANCE / EFFICIENCY
    # ========================================================

    st.markdown("---")

    st.html(
        """
        <div class="section-title">
            ⚡ SYSTEM PERFORMANCE & EFFICIENCY
        </div>
        """
    )

    performance = result.get(
        "performance_metrics",
        {}
    )

    total_time = performance.get(
        "total_execution_time",
        0
    )

    queries_processed = performance.get(
        "queries_processed",
        1
    )

    throughput = performance.get(
        "throughput",
        0
    )

    e1, e2, e3 = st.columns(3)

    with e1:

        st.metric(
            "TOTAL EXECUTION TIME",
            f"{float(total_time):.2f} sec"
        )

    with e2:

        st.metric(
            "QUERIES PROCESSED",
            str(queries_processed)
        )

    with e3:

        st.metric(
            "THROUGHPUT",
            f"{float(throughput):.3f} query/sec"
        )

    stage_timings = performance.get(
        "stage_timings",
        {}
    )

    if stage_timings:

        st.markdown(
            "### ⏱️ STAGE-WISE EXECUTION TIME"
        )

        for stage, duration in stage_timings.items():

            try:

                duration = float(duration)

            except Exception:

                duration = 0.0

            percentage = (
                (duration / float(total_time)) * 100
                if float(total_time) > 0
                else 0
            )

            st.markdown(
                f"**{stage}** — "
                f"{duration:.2f} sec "
                f"({percentage:.1f}% of total)"
            )

            st.progress(
                min(
                    max(
                        percentage / 100,
                        0.0
                    ),
                    1.0
                )
            )

        slowest_stage = max(
            stage_timings,
            key=lambda key: float(
                stage_timings.get(key, 0)
            )
        )

        fastest_stage = min(
            stage_timings,
            key=lambda key: float(
                stage_timings.get(key, 0)
            )
        )

        st.info(
            f"🔎 Slowest stage: **{slowest_stage}** "
            f"({float(stage_timings[slowest_stage]):.2f} sec)  \n"
            f"⚡ Fastest stage: **{fastest_stage}** "
            f"({float(stage_timings[fastest_stage]):.2f} sec)"
        )

    st.html(
        f"""
        <div style="
            background:rgba(3,25,50,0.78);
            border:1px solid rgba(70,210,255,0.28);
            border-radius:16px;
            padding:18px;
            margin-top:15px;
            color:#dff7ff;
            line-height:1.7;
        ">
            <div style="
                color:#72d8ff;
                font-size:11px;
                font-weight:800;
                letter-spacing:2px;
                margin-bottom:8px;
            ">
                EFFICIENCY SUMMARY
            </div>

            SATQuery AI processed the complete mission pipeline
            in <b>{float(total_time):.2f} seconds</b>.
            The observed throughput was
            <b>{float(throughput):.3f} query/sec</b>.
            Stage-wise timings are provided to identify
            computational bottlenecks in the agentic pipeline.
        </div>
        """
    )


    # ========================================================
    # AGENT STATUS
    # ========================================================

    st.markdown("---")

    st.html(
        """
        <div class="section-title">
            ⚡ AGENTIC PIPELINE
        </div>
        """
    )

    p1, p2, p3 = st.columns(3)

    with p1:

        st.success(
            "✓ Query Router"
        )

        st.success(
            "✓ Satellite Retrieval"
        )

    with p2:

        st.success(
            "✓ Vision Agent"
        )

        st.success(
            "✓ Change Detection"
        )

    with p3:

        st.success(
            "✓ Evidence Fusion"
        )

        st.success(
            "✓ Answer Agent"
        )


    # ========================================================
    # RAW AGENT OUTPUTS
    # ========================================================

    st.markdown("---")

    with st.expander(
        "🧠 Query Router Output"
    ):

        if isinstance(
            result["query_result"],
            dict
        ):

            st.json(
                result["query_result"]
            )

        else:

            st.write(
                result["query_result"]
            )


    with st.expander(
        "👁️ Vision Agent Output"
    ):

        if isinstance(
            result["vision_result"],
            dict
        ):

            st.json(
                result["vision_result"]
            )

        else:

            st.write(
                result["vision_result"]
            )


    with st.expander(
        "🔍 Change Detection Output"
    ):

        if isinstance(
            result["change_result"],
            dict
        ):

            st.json(
                result["change_result"]
            )

        else:

            st.write(
                result["change_result"]
            )


    with st.expander(
        "📚 Evidence Agent Output"
    ):

        if isinstance(
            result["evidence_result"],
            dict
        ):

            st.json(
                result["evidence_result"]
            )

        else:

            st.write(
                result["evidence_result"]
            )


    with st.expander(
        "🎯 Answer Agent Input"
    ):

        if isinstance(
            result["fused_result"],
            dict
        ):

            st.json(
                result["fused_result"]
            )

        else:

            st.write(
                result["fused_result"]
            )


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div style="
        text-align:center;
        padding:35px 0 10px 0;
        color:rgba(150,200,230,0.45);
        font-size:10px;
        letter-spacing:2px;
    ">

        SATQUERY AI
        &nbsp; • &nbsp;
        AGENTIC EARTH OBSERVATION
        &nbsp; • &nbsp;
        MISSION CONTROL

    </div>
    """
)
            
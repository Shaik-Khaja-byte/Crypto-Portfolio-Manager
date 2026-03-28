def get_css():
    return """
<style>

/* ---------- FONT ---------- */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}


/* ---------- BACKGROUND ---------- */

.stApp{
    background:
        radial-gradient(circle at 20% 20%, #0f172a 0%, #020617 60%),
        radial-gradient(circle at 80% 80%, #1e293b 0%, transparent 40%);
    color:#e2e8f0;
}


/* ---------- LAYOUT WIDTH ---------- */

.block-container{
    max-width:1500px;
    padding-top:2rem;
    padding-bottom:3rem;
}


/* ---------- SIDEBAR ---------- */

[data-testid="stSidebar"]{
    background: rgba(2,6,23,0.75);
    backdrop-filter: blur(20px);
    border-right:1px solid rgba(255,255,255,0.05);
}

[data-testid="stSidebar"] *{
    color:#cbd5f5;
}


/* ---------- HEADINGS ---------- */

h1{
    font-size:2.5rem;
    font-weight:700;
    letter-spacing:-0.4px;
    color:#f8fafc;
}

h2{
    font-size:1.6rem;
    font-weight:600;
    color:#e2e8f0;
}


/* ---------- GLASS PANELS ---------- */

[data-testid="stVerticalBlock"] > div{
    background: rgba(15,23,42,0.45);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);

    border:1px solid rgba(255,255,255,0.06);
    border-radius:14px;

    padding:18px;
    margin-bottom:18px;

    box-shadow:
        0 4px 30px rgba(0,0,0,0.35),
        inset 0 1px 0 rgba(255,255,255,0.03);
}


/* ---------- KPI METRICS ---------- */

[data-testid="stMetric"]{
    background: transparent;
    border:none;
}

[data-testid="stMetricLabel"]{
    font-size:0.8rem;
    text-transform:uppercase;
    letter-spacing:1px;
    color:#94a3b8;
}

[data-testid="stMetricValue"]{
    font-size:2.8rem;
    font-weight:700;
    color:#34d399;
}


/* ---------- CHART AREA ---------- */

.js-plotly-plot{
    background:transparent !important;
}


/* ---------- INPUTS ---------- */

.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"]{
    background: rgba(15,23,42,0.55);
    backdrop-filter: blur(12px);

    border:1px solid rgba(255,255,255,0.08);
    border-radius:8px;

    color:#f1f5f9;
}


/* ---------- BUTTONS ---------- */

.stButton > button{

    background: rgba(59,130,246,0.18);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);

    border:1px solid rgba(96,165,250,0.45);

    color:#e2e8f0;
    font-weight:600;

    border-radius:10px;

    padding:6px 16px;

    min-width:110px;
    white-space:nowrap;

    transition:all .25s ease;
}


/* hover glow */

.stButton > button:hover{

    background: rgba(59,130,246,0.35);

    border:1px solid rgba(96,165,250,0.7);

    box-shadow:
        0 0 10px rgba(96,165,250,0.45),
        inset 0 1px 0 rgba(255,255,255,0.08);

    transform:translateY(-1px);
}


/* press */

.stButton > button:active{
    transform:scale(0.96);
}


/* ---------- TABLE ---------- */

[data-testid="stDataFrame"]{
    background: rgba(15,23,42,0.35);
    backdrop-filter: blur(14px);
    border-radius:10px;
}


/* ---------- TABLE HEADER ---------- */

thead tr th{
    background: rgba(2,6,23,0.6) !important;
    border-bottom:1px solid rgba(255,255,255,0.08);
}


/* ---------- DIVIDER ---------- */

hr{
    border:none;
    height:1px;
    background:rgba(255,255,255,0.08);
}


/* ---------- SCROLLBAR ---------- */

::-webkit-scrollbar{
    width:8px;
}

::-webkit-scrollbar-track{
    background:transparent;
}

::-webkit-scrollbar-thumb{
    background:rgba(148,163,184,0.35);
    border-radius:10px;
}


/* ---------- REMOVE STREAMLIT PADDING ---------- */

section.main > div{
    padding-left:1rem;
    padding-right:1rem;
}

</style>
"""
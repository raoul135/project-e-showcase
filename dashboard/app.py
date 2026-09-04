import base64
import json
import math
import re
from html import escape
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

try:
    from data_source import (
        IS_DEMO_MODE, get_human_review_history, get_latest_reports,
        get_report_archive, get_report_archive_count, get_report_html,
        set_human_review_status, test_connection,
    )
except ModuleNotFoundError:  # Supports module-based test runners.
    from dashboard.data_source import (
        IS_DEMO_MODE, get_human_review_history, get_latest_reports,
        get_report_archive, get_report_archive_count, get_report_html,
        set_human_review_status, test_connection,
    )


st.set_page_config(
    page_title="Project-E Control Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# VISUAL SYSTEM — V5.1
# =============================================================================

st.markdown(
    """
<style>
:root{
    --bg:#050b15;
    --bg2:#07101d;
    --sidebar:#06101d;
    --text:#f8fafc;
    --muted:#94a3b8;
    --line:rgba(148,163,184,.16);

    --violet:#8b5cf6;
    --purple:#c026d3;
    --blue:#2563eb;
    --cyan:#0891b2;
    --green:#22c55e;
    --amber:#f59e0b;
    --red:#f43f5e;
}

html,body,[data-testid="stAppViewContainer"],.stApp{
    background:
        radial-gradient(circle at 70% -10%, rgba(37,99,235,.10), transparent 31%),
        linear-gradient(180deg,var(--bg) 0%,var(--bg2) 100%);
    color:var(--text);
}

[data-testid="stHeader"]{display:none;}
#MainMenu,footer{visibility:hidden;}

.block-container{
    max-width:1660px;
    padding:1.05rem 1.6rem 2rem;
}

/* ---------------- Sidebar — V5.4 custom navigation ---------------- */

[data-testid="stSidebar"]{
    background:
        radial-gradient(circle at 16% 0%, rgba(124,58,237,.18), transparent 27%),
        linear-gradient(180deg,#06111f 0%,#050b15 100%);
    border-right:1px solid rgba(99,102,241,.25);
    box-shadow:12px 0 38px rgba(0,0,0,.20);
    min-width:292px !important;
    width:292px !important;
}

[data-testid="stSidebar"] > div:first-child{
    width:292px !important;
}

[data-testid="stSidebar"] .block-container{
    padding:1.15rem 1rem 1rem;
}

.brand{
    display:flex;
    align-items:center;
    gap:13px;
    margin-bottom:4px;
}

.brand-mark{
    width:50px;
    height:50px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:15px;
    font-size:1.45rem;
    background:
        radial-gradient(circle at 35% 25%,rgba(255,255,255,.18),transparent 30%),
        linear-gradient(145deg,#7c3aed,#4f46e5);
    border:1px solid rgba(216,180,254,.34);
    box-shadow:
        0 0 0 1px rgba(196,181,253,.16),
        0 0 22px rgba(124,58,237,.34),
        0 12px 26px rgba(79,70,229,.30);
}

.brand-name{
    font-size:1.38rem;
    font-weight:950;
    color:#fff;
    letter-spacing:-.032em;
}

.brand-sub{
    color:#8fa1b9;
    font-size:.78rem;
    margin:0 0 22px 63px;
}

.side-heading{
    color:#91a0b7;
    font-size:.66rem;
    font-weight:950;
    letter-spacing:.18em;
    text-transform:uppercase;
    margin:18px 0 8px;
}

/* Custom navigation shell */
.sidebar-nav-panel{
    border:1px solid rgba(96,165,250,.14);
    border-radius:13px;
    overflow:hidden;
    background:rgba(6,15,27,.54);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.02);
}

.sidebar-nav-panel.workspace{
    border-color:rgba(139,92,246,.12);
    background:transparent;
}

.sidebar-link{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    min-height:44px;
    padding:10px 11px;
    color:#d9e3ef !important;
    text-decoration:none !important;
    border-bottom:1px solid rgba(148,163,184,.075);
    background:rgba(9,18,32,.38);
    transition:all .14s ease;
}

.sidebar-link:last-child{
    border-bottom:none;
}

.sidebar-link:hover{
    transform:translateX(2px);
    background:rgba(30,41,59,.76);
}

.sidebar-link.selected{
    color:#fff !important;
    background:
        radial-gradient(circle at 100% 50%,rgba(168,85,247,.16),transparent 35%),
        linear-gradient(90deg,rgba(109,40,217,.58),rgba(79,70,229,.24));
    border-color:rgba(167,139,250,.34);
    box-shadow:
        inset 4px 0 0 #a855f7,
        inset 0 0 24px rgba(124,58,237,.08);
}

.sidebar-link-main{
    display:flex;
    align-items:center;
    gap:10px;
    min-width:0;
}

.sidebar-icon{
    width:22px;
    height:22px;
    display:flex;
    align-items:center;
    justify-content:center;
    flex:0 0 auto;
    font-size:.96rem;
    font-weight:900;
    filter:drop-shadow(0 0 7px currentColor);
}

.sidebar-label{
    font-size:.81rem;
    font-weight:820;
    white-space:nowrap;
}

.sidebar-count{
    min-width:24px;
    height:24px;
    padding:0 7px;
    border-radius:999px;
    display:flex;
    align-items:center;
    justify-content:center;
    flex:0 0 auto;
    font-size:.69rem;
    line-height:1;
    font-weight:900;
    color:#dce5f1;
    background:#18243a;
    border:1px solid rgba(148,163,184,.13);
}

.sidebar-link.selected .sidebar-count{
    color:#fff;
    background:linear-gradient(180deg,#7c3aed,#5b21b6);
    border-color:rgba(196,181,253,.30);
    box-shadow:0 0 11px rgba(124,58,237,.30);
}

/* Icon colors */
.i-purple{color:#c084fc;}
.i-green{color:#4ade80;}
.i-amber{color:#fbbf24;}
.i-red{color:#fb7185;}
.i-yellow{color:#facc15;}
.i-cyan{color:#38bdf8;}
.i-white{color:#e2e8f0;}

/* Selected filter variants keep their semantic color */
.sidebar-link.sel-green{
    background:linear-gradient(90deg,rgba(21,128,61,.30),rgba(5,46,22,.12));
    box-shadow:inset 4px 0 0 #4ade80;
}
.sidebar-link.sel-amber{
    background:linear-gradient(90deg,rgba(180,83,9,.31),rgba(69,26,3,.12));
    box-shadow:inset 4px 0 0 #fbbf24;
}
.sidebar-link.sel-red{
    background:linear-gradient(90deg,rgba(190,24,93,.30),rgba(76,5,25,.12));
    box-shadow:inset 4px 0 0 #fb7185;
}
.sidebar-link.sel-cyan{
    background:linear-gradient(90deg,rgba(2,132,199,.28),rgba(8,47,73,.12));
    box-shadow:inset 4px 0 0 #38bdf8;
}
.sidebar-link.sel-slate{
    background:linear-gradient(90deg,rgba(71,85,105,.30),rgba(15,23,42,.12));
    box-shadow:inset 4px 0 0 #94a3b8;
}

/* Section separator */
.sidebar-separator{
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(148,163,184,.18),transparent);
    margin:17px 0 4px;
}

/* System panel */
.system-card{
    margin-top:2px;
    padding:12px 13px;
    border-radius:12px;
    border:1px solid rgba(34,197,94,.28);
    background:
        radial-gradient(circle at 100% 0%,rgba(34,197,94,.08),transparent 35%),
        linear-gradient(180deg,rgba(22,101,52,.22),rgba(7,39,24,.28));
    color:#7ef3a5;
    font-size:.77rem;
    font-weight:900;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.03),
        0 10px 25px rgba(0,0,0,.14);
}

.system-sub{
    border-top:1px solid rgba(34,197,94,.16);
    margin-top:9px;
    padding-top:8px;
    color:#76d99a;
    font-size:.66rem;
    font-weight:720;
    line-height:1.8;
}

.system-meta{
    margin-top:10px;
    color:#73839a;
    font-size:.65rem;
    line-height:1.65;
}

/* Animated activity strip */
.version-chip{
    margin-top:15px;
    min-height:70px;
    padding:10px 11px;
    border-radius:11px;
    border:1px solid rgba(99,102,241,.18);
    background:
        radial-gradient(circle at 0% 0%,rgba(124,58,237,.13),transparent 40%),
        linear-gradient(180deg,rgba(30,41,59,.64),rgba(15,23,42,.52));
    color:#a1aec0;
    font-size:.63rem;
}

.version-sub{
    margin-top:3px;
    color:#afc0d5;
}

.pulse-dots{
    display:flex;
    gap:5px;
    margin-bottom:8px;
    align-items:center;
}

.pulse-dots span{
    width:6px;
    height:6px;
    border-radius:50%;
    background:#8b5cf6;
    box-shadow:0 0 9px rgba(139,92,246,.65);
    animation:dotPulse 1.2s infinite ease-in-out;
}
.pulse-dots span:nth-child(2){animation-delay:.12s;background:#a855f7;}
.pulse-dots span:nth-child(3){animation-delay:.24s;background:#c084fc;}
.pulse-dots span:nth-child(4){animation-delay:.36s;background:#8b5cf6;}
.pulse-dots span:nth-child(5){animation-delay:.48s;background:#6366f1;}
.pulse-dots span:nth-child(6){animation-delay:.60s;background:#38bdf8;}

@keyframes dotPulse{
    0%,100%{transform:translateY(0) scale(.85);opacity:.42;}
    50%{transform:translateY(-3px) scale(1.18);opacity:1;}
}


/* ---------------- Main heading ---------------- */

.eyebrow{
    color:#a78bfa;
    font-size:.64rem;
    font-weight:950;
    letter-spacing:.16em;
    text-transform:uppercase;
    margin-bottom:4px;
}

.page-title{
    margin:0;
    font-size:2.15rem;
    font-weight:950;
    line-height:1;
    letter-spacing:-.052em;
}

.page-sub{
    margin:7px 0 12px;
    color:#98a6b8;
    font-size:.86rem;
}

/* ---------------- KPI cards ---------------- */

.kpi{
    min-height:82px;
    border-radius:14px;
    padding:12px 14px;
    display:flex;
    align-items:center;
    gap:12px;
    border:1px solid rgba(148,163,184,.14);
    box-shadow:0 10px 26px rgba(0,0,0,.16);
    overflow:hidden;
    position:relative;
}

.kpi::after{
    content:"";
    position:absolute;
    width:76px;
    height:76px;
    right:-29px;
    top:-30px;
    border-radius:50%;
    background:currentColor;
    opacity:.05;
}

.kpi-icon{
    width:42px;
    height:42px;
    border-radius:11px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:1.16rem;
    font-weight:900;
    flex:0 0 auto;
}

.kpi-label{
    color:#dbe4ef;
    font-size:.68rem;
    font-weight:800;
}

.kpi-value{
    margin-top:1px;
    font-size:1.5rem;
    line-height:1;
    font-weight:950;
    color:#fff;
}

.kpi-sub{
    margin-top:3px;
    font-size:.57rem;
    color:#8b9aaf;
}

.kpi-blue{
    color:#60a5fa;
    background:linear-gradient(135deg,rgba(30,64,175,.42),rgba(10,22,43,.94));
    border-color:rgba(59,130,246,.46);
}
.kpi-blue .kpi-icon{
    background:rgba(37,99,235,.27);
    border:1px solid rgba(96,165,250,.30);
}

.kpi-green{
    color:#4ade80;
    background:linear-gradient(135deg,rgba(6,95,70,.40),rgba(10,24,33,.94));
    border-color:rgba(34,197,94,.42);
}
.kpi-green .kpi-icon{
    background:rgba(34,197,94,.18);
    border:1px solid rgba(74,222,128,.28);
}

.kpi-amber{
    color:#fbbf24;
    background:linear-gradient(135deg,rgba(120,53,15,.44),rgba(25,20,13,.94));
    border-color:rgba(245,158,11,.44);
}
.kpi-amber .kpi-icon{
    background:rgba(245,158,11,.19);
    border:1px solid rgba(251,191,36,.30);
}

.kpi-red{
    color:#fb7185;
    background:linear-gradient(135deg,rgba(136,19,55,.37),rgba(30,12,20,.94));
    border-color:rgba(244,63,94,.42);
}
.kpi-red .kpi-icon{
    background:rgba(244,63,94,.18);
    border:1px solid rgba(251,113,133,.28);
}

/* ---------------- Controls ---------------- */

[data-testid="stTextInput"] input,
[data-baseweb="select"]>div{
    min-height:38px;
    background:#091423 !important;
    border:1px solid rgba(148,163,184,.24) !important;
    color:white !important;
    border-radius:9px !important;
}
[data-testid="stTextInput"] input::placeholder{color:#b9c9dc !important;opacity:1;}
[data-testid="stTextInput"] label,[data-testid="stSelectbox"] label{color:#c8d6e5 !important;}

.stButton>button{
    min-height:38px;
    border-radius:9px;
    border:1px solid rgba(59,130,246,.42);
    background:linear-gradient(180deg,#152644,#11203a);
    color:white;
    font-size:.72rem;
    font-weight:850;
    transition:.14s ease;
}

.stButton>button:hover{
    transform:translateY(-1px);
    background:linear-gradient(180deg,#1a3156,#142744);
    border-color:rgba(96,165,250,.72);
    color:white;
}
[data-testid="stDownloadButton"] button{min-height:38px;border-radius:9px;border:1px solid rgba(59,130,246,.55);background:linear-gradient(180deg,#1b4264,#12304d);color:#eef8ff;font-size:.72rem;font-weight:850;}
[data-testid="stDownloadButton"] button:hover{background:linear-gradient(180deg,#24577f,#173d61);border-color:rgba(125,211,252,.8);color:#fff;}

.page-info{
    color:#7d8ca3;
    font-size:.65rem;
    text-align:right;
    padding-top:7px;
}
.context-row{
    display:flex;
    flex-wrap:wrap;
    gap:6px;
    margin:2px 0 10px;
}
.context-chip{
    display:inline-flex;
    align-items:center;
    min-height:24px;
    padding:3px 9px;
    border-radius:999px;
    color:#a9bad0;
    background:#0d1a2c;
    border:1px solid rgba(96,165,250,.20);
    font-size:.66rem;
    font-weight:800;
}
.empty-state{
    margin:.65rem 0;
    padding:18px 16px;
    border-radius:12px;
    color:#cbd5e1;
    background:#0a1525;
    border:1px solid rgba(96,165,250,.18);
    font-size:.82rem;
    line-height:1.55;
}
.empty-state strong{
    display:block;
    color:#e5edf7;
    font-size:.9rem;
    margin-bottom:3px;
}

/* ---------------- Job cards ---------------- */

.job-card{
    min-height:318px;
    padding:14px 14px 12px;
    border-radius:17px;
    background:
        radial-gradient(circle at 93% 5%,rgba(37,99,235,.09),transparent 25%),
        linear-gradient(180deg,#0e1b2f,#091523 72%,#08121f);
    border:1.5px solid rgba(59,130,246,.78);
    box-shadow:
        0 0 0 1px rgba(37,99,235,.08),
        0 13px 28px rgba(0,0,0,.27),
        inset 0 1px 0 rgba(255,255,255,.025);
    position:relative;
    overflow:hidden;
}

.job-card.rich{
    background:
        radial-gradient(circle at 90% 6%,rgba(126,34,206,.14),transparent 30%),
        linear-gradient(180deg,#17142a,#0d1424 68%,#09111f);
    border-color:rgba(192,38,211,.92);
    box-shadow:
        0 0 0 1px rgba(168,85,247,.13),
        0 0 20px rgba(147,51,234,.11),
        0 15px 30px rgba(0,0,0,.30);
}

.job-card.selected{
    border-color:#e879f9;
    box-shadow:
        0 0 0 1px rgba(232,121,249,.28),
        0 0 26px rgba(168,85,247,.22),
        0 17px 34px rgba(0,0,0,.33);
}

.card-head{
    display:flex;
    justify-content:space-between;
    gap:11px;
    align-items:flex-start;
    padding-bottom:9px;
    border-bottom:1px solid rgba(148,163,184,.13);
}

.title-wrap{
    display:flex;
    gap:9px;
    align-items:flex-start;
    min-width:0;
}

.card-icon{
    width:32px;
    height:32px;
    border-radius:9px;
    display:flex;
    align-items:center;
    justify-content:center;
    flex:0 0 auto;
    font-size:.87rem;
    background:linear-gradient(145deg,#7c3aed,#9333ea);
    border:1px solid rgba(216,180,254,.28);
}

.card-icon.legacy{
    background:linear-gradient(145deg,#0369a1,#2563eb);
    border-color:rgba(125,211,252,.28);
}

.job-title{
    font-size:1.04rem;
    line-height:1.2;
    font-weight:930;
    letter-spacing:-.025em;
    color:#fff;
}

.job-sub{
    margin-top:2px;
    color:#9aa8bc;
    font-size:.66rem;
    text-transform:capitalize;
}

.badge{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    padding:6px 8px;
    border-radius:999px;
    font-size:.57rem;
    font-weight:900;
    letter-spacing:.045em;
    white-space:nowrap;
}

.b-strong{color:#bbf7d0;background:rgba(34,197,94,.13);border:1px solid rgba(34,197,94,.32);}
.b-apply{color:#bfdbfe;background:rgba(59,130,246,.13);border:1px solid rgba(59,130,246,.34);}
.b-cautious{color:#fde68a;background:rgba(245,158,11,.14);border:1px solid rgba(245,158,11,.36);}
.b-low{color:#e9d5ff;background:rgba(168,85,247,.14);border:1px solid rgba(168,85,247,.32);}
.b-skip{color:#fecaca;background:rgba(239,68,68,.13);border:1px solid rgba(239,68,68,.34);}
.b-legacy{color:#bfdbfe;background:rgba(37,99,235,.13);border:1px solid rgba(96,165,250,.30);}

.score-row{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:7px;
    margin-top:10px;
}

.score{
    min-width:0;
    border:1px solid rgba(148,163,184,.13);
    background:rgba(8,18,32,.62);
    border-radius:9px;
    padding:8px 9px 7px;
}

.score-label{
    color:#8f9db2;
    font-size:.50rem;
    font-weight:900;
    letter-spacing:.11em;
    text-transform:uppercase;
}

.score-num{
    margin-top:2px;
    font-size:1.85rem;
    line-height:1;
    font-weight:950;
    letter-spacing:-.06em;
}

.score-num small{
    font-size:.62rem;
    color:#93a1b5;
    font-weight:800;
}

.score-purple{color:#d946ef;}
.score-blue{color:#60a5fa;}
.score-green{color:#4ade80;}

.bar{
    height:4px;
    margin-top:7px;
    border-radius:999px;
    background:#1d293c;
    overflow:hidden;
}

.bar span{
    display:block;
    height:100%;
    border-radius:999px;
}

.pill-row{
    display:flex;
    flex-wrap:wrap;
    gap:5px;
    margin-top:8px;
    min-height:23px;
}

.pill{
    font-size:.54rem;
    font-weight:850;
    padding:4px 6px;
    border-radius:999px;
}

.p-ok{
    color:#86efac;
    background:rgba(34,197,94,.08);
    border:1px solid rgba(34,197,94,.21);
}

.p-warn{
    color:#fde68a;
    background:rgba(245,158,11,.08);
    border:1px solid rgba(245,158,11,.22);
}
.p-applied{
    color:#67e8f9;
    background:rgba(8,145,178,.12);
    border:1px solid rgba(34,211,238,.26);
}

.fact-grid{
    display:grid;
    grid-template-columns:repeat(5,1fr);
    gap:6px;
    margin-top:8px;
}

.fact-box{
    min-width:0;
    min-height:56px;
    border-radius:8px;
    padding:7px 7px;
    background:#091423;
    border:1px solid rgba(148,163,184,.14);
}

.fact-box.budget{
    background:linear-gradient(180deg,rgba(16,185,129,.08),rgba(8,20,31,.85));
    border-color:rgba(52,211,153,.25);
}
.fact-box.rating{
    background:linear-gradient(180deg,rgba(245,158,11,.08),rgba(8,20,31,.85));
    border-color:rgba(251,191,36,.25);
}
.fact-box.hires{
    background:linear-gradient(180deg,rgba(168,85,247,.08),rgba(8,20,31,.85));
    border-color:rgba(192,132,252,.24);
}
.fact-box.proposals{
    background:linear-gradient(180deg,rgba(59,130,246,.08),rgba(8,20,31,.85));
    border-color:rgba(96,165,250,.24);
}
.fact-box.posted{
    background:linear-gradient(180deg,rgba(236,72,153,.065),rgba(8,20,31,.85));
    border-color:rgba(244,114,182,.20);
}

.fact-label{
    color:#8493aa;
    font-size:.45rem;
    font-weight:900;
    letter-spacing:.08em;
    text-transform:uppercase;
}

.fact-value{
    color:white;
    font-size:.86rem;
    font-weight:930;
    margin-top:2px;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.fact-box.budget .fact-value{color:#5ee6b4;}
.fact-box.rating .fact-value{color:#ffd166;}
.fact-box.hires .fact-value{color:#c4b5fd;}
.fact-box.proposals .fact-value{color:#7dd3fc;}
.fact-box.posted .fact-value{color:#f9a8d4;}

.fact-sub{
    margin-top:1px;
    color:#6f8097;
    font-size:.50rem;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}

.legacy-note{
    margin-top:10px;
    min-height:80px;
    display:flex;
    align-items:center;
    padding:11px 12px;
    border-radius:10px;
    color:#d6deea;
    font-size:.64rem;
    line-height:1.46;
    background:
        linear-gradient(180deg,rgba(30,64,175,.08),rgba(11,23,39,.78));
    border:1px solid rgba(96,165,250,.16);
}

.card-foot{
    margin-top:8px;
    display:flex;
    justify-content:space-between;
    gap:8px;
    color:#8191a8;
    font-size:.51rem;
}

.report-shell{
    margin-top:8px;
    padding:3px;
    border-radius:16px;
    background:rgba(99,102,241,.18);
}

.section-kicker{
    color:#8b8efc;
    font-size:.65rem;
    font-weight:900;
    letter-spacing:.14em;
    text-transform:uppercase;
}

.section-title{
    margin:4px 0 0;
    font-size:1.35rem;
    font-weight:900;
    letter-spacing:-.035em;
}

.section-desc{
    color:#94a3b8;
    margin-top:5px;
    font-size:.78rem;
}

/* ===================== V5.5 RESPONSIVE POLISH ===================== */

/* Main canvas grows with the browser instead of feeling fixed */
.block-container{
    width:min(100%, 1780px);
    max-width:none;
    padding-left:clamp(1rem,2vw,2.25rem);
    padding-right:clamp(1rem,2vw,2.25rem);
}

/* Sidebar scales with viewport while staying usable */
[data-testid="stSidebar"]{
    min-width:clamp(250px,16vw,315px) !important;
    width:clamp(250px,16vw,315px) !important;
}

[data-testid="stSidebar"] > div:first-child{
    width:clamp(250px,16vw,315px) !important;
}

/* Typography and spacing scale smoothly */
.brand-name{
    font-size:clamp(1.12rem,1.25vw,1.46rem);
}

.brand-mark{
    width:clamp(42px,2.8vw,52px);
    height:clamp(42px,2.8vw,52px);
}

.page-title{
    font-size:clamp(1.85rem,2.2vw,2.65rem);
}

.page-sub{
    font-size:clamp(.78rem,.9vw,.96rem);
}

.kpi{
    min-height:clamp(76px,7.5vw,102px);
    padding:clamp(10px,1vw,15px);
}

.kpi-icon{
    width:clamp(38px,2.7vw,50px);
    height:clamp(38px,2.7vw,50px);
}

.kpi-value{
    font-size:clamp(1.35rem,1.7vw,1.85rem);
}

/* Job cards use available screen space */
.job-card{
    min-height:clamp(280px,31vh,350px);
    padding:clamp(12px,1vw,16px);
    display:flex;
    flex-direction:column;
}

.job-title{
    font-size:clamp(.96rem,1.05vw,1.2rem);
}

.score-num{
    font-size:clamp(1.6rem,1.85vw,2.15rem);
}

.fact-value{
    font-size:clamp(.77rem,.9vw,.98rem);
}

.card-foot{
    margin-top:auto;
    padding-top:8px;
}

/* Ensure paired cards stay visually equal */
[data-testid="stHorizontalBlock"]{
    align-items:stretch;
}

[data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    display:flex;
    flex-direction:column;
}

[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > div{
    flex:1;
}

/* Keep the card action button visually anchored below the card */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] .stButton{
    margin-top:auto;
}

/* Make metric facts gracefully reflow */
.fact-grid{
    grid-template-columns:repeat(5,minmax(0,1fr));
}

/* Top KPI row becomes 2x2 at medium widths */
@media (max-width: 1180px){
    .block-container{
        padding-left:1rem;
        padding-right:1rem;
    }

    .fact-grid{
        grid-template-columns:repeat(3,minmax(0,1fr));
    }

    .score-row{
        gap:6px;
    }

    .job-card{
        min-height:auto;
    }
}

/* On narrower desktop/tablet, sidebar gets slimmer and content breathes */
@media (max-width: 980px){
    [data-testid="stSidebar"]{
        min-width:235px !important;
        width:235px !important;
    }

    [data-testid="stSidebar"] > div:first-child{
        width:235px !important;
    }

    .fact-grid{
        grid-template-columns:repeat(2,minmax(0,1fr));
    }

    .page-title{
        font-size:1.9rem;
    }
}

/* Phone-ish widths: let Streamlit stack columns naturally */
@media (max-width: 760px){
    .block-container{
        padding:.85rem .75rem 2rem;
    }

    .kpi{
        min-height:72px;
    }

    .fact-grid{
        grid-template-columns:repeat(2,minmax(0,1fr));
    }

    .score-row{
        grid-template-columns:1fr;
    }

    .score{
        min-height:auto;
    }

    .card-head{
        gap:8px;
    }

    .sidebar-link{
        min-height:40px;
    }
}


/* ===================== V6 READABLE REPORT SECTIONS ===================== */
.report-section-note{
    color:#8fa0b7;
    font-size:.73rem;
    margin-bottom:.7rem;
}
.report-group{
    border:1px solid rgba(148,163,184,.13);
    background:rgba(9,20,35,.58);
    border-radius:11px;
    padding:11px 12px;
    margin:.45rem 0;
}
.report-group-title{
    color:#c7d2fe;
    font-size:.72rem;
    font-weight:900;
    letter-spacing:.08em;
    text-transform:uppercase;
    margin-bottom:.5rem;
}
.report-kv{
    display:grid;
    grid-template-columns:minmax(150px, 28%) 1fr;
    gap:10px;
    padding:6px 0;
    border-bottom:1px solid rgba(148,163,184,.08);
}
.report-kv:last-child{
    border-bottom:none;
}
.report-key{
    color:#8fa0b7;
    font-size:.72rem;
    font-weight:800;
}
.report-value{
    color:#eef2ff;
    font-size:.76rem;
    line-height:1.55;
    overflow-wrap:anywhere;
}
.report-yes{
    color:#86efac;
    font-weight:850;
}
.report-no{
    color:#fda4af;
    font-weight:850;
}
.report-list{
    margin:.2rem 0 .2rem 1.1rem;
    color:#eef2ff;
    font-size:.76rem;
    line-height:1.55;
}
.report-list li{
    margin:.2rem 0;
}
.report-proposal{
    white-space:pre-wrap;
    color:#f8fafc;
    font-size:.85rem;
    line-height:1.7;
    padding:14px;
    border-radius:11px;
    background:#091423;
    border:1px solid rgba(96,165,250,.17);
}


/* ===================== V7 REVIEW WORKSPACE ===================== */
.review-heading{
    font-size:clamp(1.25rem,1.55vw,1.8rem);
    font-weight:950;
    line-height:1.1;
    letter-spacing:-.045em;
    margin:0;
}
.review-subtitle{
    margin-top:5px;
    color:#94a3b8;
    font-size:.78rem;
}
.review-summary-grid{
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:10px;
    margin:7px 0 8px;
}
.review-summary-card{
    border-radius:12px;
    padding:8px 11px;
    background:#0b1627;
    border:1px solid rgba(148,163,184,.15);
}
.review-summary-label{
    color:#8392a8;
    font-size:.56rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.11em;
}
.review-summary-value{
    margin-top:3px;
    color:#fff;
    font-size:1.15rem;
    font-weight:930;
}
.review-callout{
    border-radius:12px;
    padding:12px 13px;
    margin:.45rem 0;
    border:1px solid rgba(148,163,184,.14);
    background:#0a1525;
}
.review-callout.good{
    border-color:rgba(34,197,94,.20);
    background:linear-gradient(180deg,rgba(34,197,94,.055),rgba(10,21,37,.92));
}
.review-callout.warn{
    border-color:rgba(245,158,11,.22);
    background:linear-gradient(180deg,rgba(245,158,11,.055),rgba(10,21,37,.92));
}
.review-callout-title{
    font-size:.68rem;
    font-weight:900;
    letter-spacing:.08em;
    text-transform:uppercase;
    margin-bottom:6px;
}
.review-callout.good .review-callout-title{color:#86efac;}
.review-callout.warn .review-callout-title{color:#fde68a;}
.review-callout-body{
    color:#e5e7eb;
    font-size:.78rem;
    line-height:1.55;
}
.system-warning-summary{
    margin:.45rem 0 .8rem;
    padding:15px 16px;
    border-radius:12px;
    border:1px solid rgba(245,158,11,.46);
    background:linear-gradient(180deg,rgba(120,72,10,.30),rgba(10,21,37,.96));
    box-shadow:inset 3px 0 0 #f59e0b;
}
.system-warning-summary-title{
    color:#fbbf24;
    font-size:.72rem;
    font-weight:950;
    letter-spacing:.10em;
    text-transform:uppercase;
}
.system-warning-summary-count{
    margin-top:6px;
    color:#fde68a;
    font-size:1rem;
    font-weight:950;
}
.system-warning-summary-body{
    margin-top:5px;
    color:#e5e7eb;
    font-size:.8rem;
    line-height:1.55;
}
.system-warning-summary-detail{
    margin-top:3px;
    color:#aab7c9;
    font-size:.73rem;
}
[data-testid="stTabPanel"] [data-testid="stExpander"]
[data-testid="stExpander"] > details{
    background:#091423;
    border-color:rgba(96,165,250,.20);
}
[data-testid="stTabPanel"] [data-testid="stExpander"]
[data-testid="stExpander"] > details > summary{
    background-color:#0b1627;
    color:#dbe4ef;
}
[data-testid="stTabPanel"] [data-testid="stExpander"]
[data-testid="stExpander"] > details > summary:hover,
[data-testid="stTabPanel"] [data-testid="stExpander"]
[data-testid="stExpander"] > details > summary:focus-visible{
    background-color:#14243b;
    color:#f1f5f9;
}
[data-testid="stTabPanel"] [data-testid="stExpander"]
[data-testid="stExpander"] > details[open] > summary,
[data-testid="stTabPanel"] [data-testid="stExpander"]
[data-testid="stExpander"] > details > summary:active{
    background-color:#102039;
    color:#f8fafc;
}
[data-testid="stTabPanel"] [data-testid="stExpander"]
[data-testid="stExpander"] > details > summary :where(p,svg,span){
    color:inherit;
    fill:currentColor;
}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="false"]{
    color:#94a3b8;
}
[data-testid="stTabs"] [data-testid="stTab"]{position:relative;color:#b8c7d9;padding-bottom:8px;}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"]{color:#f2f7ff !important;font-weight:850;}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"]::after{content:"";position:absolute;left:12px;right:12px;bottom:0;height:3px;border-radius:3px;background:linear-gradient(90deg,#a855f7,#38bdf8);box-shadow:0 0 12px rgba(168,85,247,.55);}
[data-testid="stTabs"] [data-testid="stTabHighlight"]{display:none !important;}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{display:none !important;}
[data-testid="stTabs"] [role="tablist"] > div:not([role="tab"]){display:none !important;}
[data-testid="stTabs"] .react-aria-SelectionIndicator{display:none !important;}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,[data-testid="stSidebar"] [data-testid="stExpander"] summary :where(p,span,svg){color:#c8d9ea !important;fill:#c8d9ea !important;}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="false"] p{
    color:inherit;
}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="false"]:hover{
    color:#cbd5e1;
}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="false"]:focus-visible{
    color:#dbeafe;
    outline:2px solid rgba(96,165,250,.48);
    outline-offset:-2px;
}
.st-key-application_actions :where(
    [data-testid="stLinkButton"] a,
    [data-testid="stButton"] button,
    [data-testid="stExpander"] > details > summary
){
    background:linear-gradient(180deg,#152844,#11203a);
    border:1px solid rgba(59,130,246,.42);
    color:#eaf2ff;
    border-radius:8px;
}
.st-key-application_actions :where(
    [data-testid="stLinkButton"] a,
    [data-testid="stButton"] button,
    [data-testid="stExpander"] > details > summary
):hover{
    background:linear-gradient(180deg,#1a3156,#142744);
    border-color:rgba(96,165,250,.72);
    color:#fff;
}
.st-key-application_actions :where(
    [data-testid="stLinkButton"] a,
    [data-testid="stButton"] button,
    [data-testid="stExpander"] > details > summary
):focus-visible{
    background:linear-gradient(180deg,#1a3156,#142744);
    border-color:#60a5fa;
    color:#fff;
    outline:2px solid rgba(96,165,250,.46);
    outline-offset:2px;
}
.st-key-application_actions :where(
    [data-testid="stLinkButton"] a,
    [data-testid="stButton"] button,
    [data-testid="stExpander"] > details > summary
):active{
    background:#0f1f36;
    border-color:#3b82f6;
    color:#fff;
}
.st-key-application_actions :where(a,button,summary) :where(p,span,svg){
    color:inherit;
    fill:currentColor;
}
.st-key-application_actions [data-testid="stLinkButton"] a,
.st-key-application_actions [data-testid="stLinkButton"] a:visited,
.st-key-application_actions [data-testid="stLinkButton"] a:hover,
.st-key-application_actions [data-testid="stLinkButton"] a:focus-visible,
.st-key-application_actions [data-testid="stLinkButton"] a:active{
    color:#f8fafc;
}
.st-key-application_actions [data-testid="stLinkButton"] a :where(div,p,span,svg){
    color:inherit;
    fill:currentColor;
}
.review-proposal{
    white-space:pre-wrap;
    border-radius:12px;
    padding:16px;
    background:#091423;
    border:1px solid rgba(96,165,250,.18);
    color:#f8fafc;
    font-size:.88rem;
    line-height:1.72;
}
.review-meta-row{
    display:grid;
    grid-template-columns:repeat(5,minmax(0,1fr));
    gap:8px;
    margin:10px 0 14px;
}
.review-meta-box{
    border-radius:10px;
    padding:9px 10px;
    background:#0a1525;
    border:1px solid rgba(148,163,184,.13);
}
.review-meta-label{
    color:#7f8ea5;
    font-size:.52rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.09em;
}
.review-meta-value{
    margin-top:3px;
    color:#fff;
    font-size:.88rem;
    font-weight:900;
    overflow-wrap:anywhere;
}
@media(max-width:950px){
    .review-summary-grid{grid-template-columns:1fr;}
    .review-meta-row{grid-template-columns:repeat(2,minmax(0,1fr));}
}


/* ===================== V8 HUMAN DECISION STATE ===================== */
.human-decision-label{
    color:#8fa0b7;
    font-size:.64rem;
    font-weight:900;
    letter-spacing:.12em;
    text-transform:uppercase;
    margin:14px 0 7px;
}
.human-state{
    display:inline-flex;
    align-items:center;
    padding:6px 9px;
    border-radius:999px;
    font-size:.66rem;
    font-weight:900;
    margin-bottom:8px;
}
.state-unreviewed{color:#cbd5e1;background:rgba(100,116,139,.12);border:1px solid rgba(148,163,184,.20);}
.state-reviewing{color:#fde68a;background:rgba(245,158,11,.11);border:1px solid rgba(245,158,11,.24);}
.state-approved{color:#86efac;background:rgba(34,197,94,.11);border:1px solid rgba(34,197,94,.24);}
.state-applied{color:#67e8f9;background:rgba(8,145,178,.12);border:1px solid rgba(34,211,238,.26);}
.state-skipped{color:#fda4af;background:rgba(244,63,94,.10);border:1px solid rgba(244,63,94,.22);}

/* ===================== PUBLIC DEMO SHOWCASE ===================== */
.demo-safety-ribbon{display:flex;align-items:center;justify-content:space-between;gap:14px;margin:2px 0 18px;padding:9px 13px;border:1px solid rgba(56,189,248,.35);border-radius:10px;background:linear-gradient(90deg,rgba(14,116,144,.22),rgba(30,41,59,.36));color:#d9f5ff;font-size:.76rem;}
.demo-safety-ribbon strong{color:#7dd3fc;letter-spacing:.06em;font-size:.67rem;}
.demo-hero{position:relative;overflow:hidden;border:1px solid rgba(56,189,248,.3);border-radius:18px;padding:17px 20px;margin:7px 0 10px;background:radial-gradient(circle at 88% 5%,rgba(168,85,247,.25),transparent 30%),linear-gradient(120deg,#0a1d34,#102f4d 52%,#172342);box-shadow:0 18px 45px rgba(0,0,0,.22);}
.demo-hero:after{content:"";position:absolute;right:-42px;bottom:-82px;width:250px;height:250px;border:1px solid rgba(125,211,252,.22);border-radius:50%;box-shadow:0 0 0 22px rgba(125,211,252,.05),0 0 0 45px rgba(125,211,252,.03);}
.demo-eyebrow{position:relative;z-index:1;color:#8bd9ff;text-transform:uppercase;font-size:.65rem;font-weight:900;letter-spacing:.14em;}
.demo-hero-title{position:relative;z-index:1;margin:6px 0 2px;color:#fff;font-size:1.58rem;font-weight:900;letter-spacing:-.025em;}.demo-hero-sub{position:relative;z-index:1;color:#b8cbe0;font-size:.87rem;}
.demo-hero-grid{position:relative;z-index:1;display:grid;grid-template-columns:1.45fr repeat(3,minmax(110px,.55fr));gap:10px;margin-top:12px;max-width:940px;}.demo-decision,.demo-metric{border-radius:12px;padding:10px 13px;border:1px solid rgba(255,255,255,.14);background:rgba(2,12,27,.38);}.demo-decision{background:linear-gradient(135deg,rgba(16,185,129,.32),rgba(6,78,59,.48));border-color:rgba(110,231,183,.55);}.demo-label{font-size:.6rem;text-transform:uppercase;letter-spacing:.11em;color:#c0d2e6;font-weight:900;}.demo-decision .demo-value{color:#b8f5d4;font-size:1.32rem;letter-spacing:.035em;}.demo-value{color:#fff;font-size:1.3rem;font-weight:900;margin-top:2px;}.demo-detail{color:#c0d0e2;font-size:.65rem;margin-top:2px;}
.pipeline-label{margin:10px 0 7px;color:#b4c7db;font-size:.64rem;font-weight:900;text-transform:uppercase;letter-spacing:.13em;}.pipeline-strip{display:grid;grid-template-columns:repeat(10,minmax(0,1fr));gap:6px;margin-bottom:10px;}.pipeline-stage{min-height:48px;padding:7px 7px;border:1px solid rgba(74,222,128,.30);border-radius:9px;background:linear-gradient(145deg,rgba(12,57,50,.54),rgba(12,30,45,.7));}.pipeline-index{color:#86efac;font-size:.58rem;font-weight:900;letter-spacing:.07em;}.pipeline-index:before{content:"✓ ";}.pipeline-name{color:#eefbf5;font-size:.65rem;font-weight:800;line-height:1.12;margin-top:2px;}.pipeline-stage.is-highlight{border-color:rgba(125,211,252,.7);background:linear-gradient(145deg,rgba(7,78,103,.65),rgba(22,78,99,.34));box-shadow:inset 0 0 18px rgba(56,189,248,.12);}.pipeline-stage.is-highlight .pipeline-index{color:#7dd3fc;}
.evidence-intro{margin:3px 0 10px;color:#c1d2e3;font-size:.8rem;}.evidence-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;}.evidence-card{min-height:190px;border:1px solid rgba(96,165,250,.28);border-radius:13px;padding:13px;background:linear-gradient(145deg,rgba(16,34,59,.78),rgba(9,19,34,.9));}.evidence-card-top{display:flex;justify-content:space-between;gap:7px;align-items:center;}.evidence-id{color:#7dd3fc;font-size:.61rem;font-weight:900;letter-spacing:.1em;}.evidence-score{color:#bbf7d0;font-size:.61rem;font-weight:900;padding:4px 6px;border-radius:999px;background:rgba(22,163,74,.15);}.evidence-field{margin-top:8px;color:#8fb1d2;font-size:.57rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase;}.evidence-title{margin:3px 0 0;color:#f2f7fc;font-size:.78rem;font-weight:850;line-height:1.25;}.evidence-claim{margin-top:3px;color:#d3e0ef;font-size:.71rem;line-height:1.38;}.evidence-link{margin-top:8px;padding-top:8px;border-top:1px solid rgba(148,163,184,.16);color:#a7f3d0;font-size:.67rem;line-height:1.3;}
.compact-statuses{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0 10px;}.compact-status{padding:5px 8px;border-radius:999px;border:1px solid rgba(110,231,183,.28);background:rgba(6,78,59,.2);color:#c5f6dc;font-size:.66rem;font-weight:850;}.compact-status.warn{border-color:rgba(251,191,36,.3);background:rgba(120,53,15,.18);color:#fde68a;}.proposal-evidence{display:flex;flex-wrap:wrap;gap:6px;margin:9px 0;}.proposal-evidence span{padding:4px 7px;border-radius:999px;background:rgba(14,116,144,.25);border:1px solid rgba(125,211,252,.28);color:#bae6fd;font-size:.62rem;font-weight:850;}.audit-panel{height:100%;box-sizing:border-box;border:1px solid rgba(110,231,183,.38);border-radius:14px;padding:15px;background:linear-gradient(150deg,rgba(6,78,59,.31),rgba(9,25,36,.78));}.audit-result{margin:7px 0 8px;color:#bbf7d0;font-size:1.1rem;font-weight:950;letter-spacing:.01em;}.audit-zero{display:inline-block;color:#d9f7e8;font-size:.71rem;padding:4px 7px;border-radius:999px;background:rgba(6,78,59,.28);border:1px solid rgba(110,231,183,.23);}.audit-check{display:flex;gap:8px;color:#d9f7e8;font-size:.72rem;margin:7px 0;line-height:1.3;}.audit-check span{color:#6ee7b7;font-weight:900;}.report-focus{border:1px solid rgba(96,165,250,.32);border-radius:14px;padding:16px 18px;background:linear-gradient(145deg,rgba(16,48,79,.82),rgba(9,20,35,.96));}.report-focus h2{margin:2px 0 5px;color:#fff;font-size:1.35rem;}.report-focus p{margin:0;color:#d0dfed;font-size:.82rem;line-height:1.5;}.report-focus-grid{display:grid;grid-template-columns:1.1fr .9fr .9fr;gap:10px;margin-top:13px;}.report-focus-card{padding:11px;border:1px solid rgba(148,163,184,.18);border-radius:10px;background:rgba(4,15,29,.45);}.report-focus-card strong{display:block;color:#e9f6ff;font-size:.72rem;margin-bottom:5px;}.report-focus-card span{color:#bed4e6;font-size:.7rem;line-height:1.35;}.report-actions{display:flex;gap:8px;margin:9px 0;}
@media(max-width:1100px){.pipeline-strip{grid-template-columns:repeat(5,minmax(0,1fr));}.demo-hero-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.demo-decision{grid-column:span 2;}.evidence-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}@media(max-width:700px){.demo-safety-ribbon{align-items:flex-start;flex-direction:column;}.pipeline-strip,.evidence-grid,.report-focus-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.demo-hero-grid{grid-template-columns:1fr;}.demo-decision{grid-column:auto;}}
@media(max-width:1100px){.pipeline-strip{grid-template-columns:repeat(5,minmax(0,1fr));}.demo-hero-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.demo-decision{grid-column:span 2;}}@media(max-width:700px){.demo-safety-ribbon{align-items:flex-start;flex-direction:column;}.pipeline-strip,.evidence-grid{grid-template-columns:repeat(2,minmax(0,1fr));}.demo-hero-grid{grid-template-columns:1fr;}.demo-decision{grid-column:auto;}}
</style>

""",
    unsafe_allow_html=True,
)


# =============================================================================
# HELPERS
# =============================================================================

def safe(value, fallback="—"):
    if value is None:
        return fallback
    try:
        if pd.isna(value):
            return fallback
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return escape(text) if text else fallback


def clean_title(value):
    title = str(value or "").strip()
    if "seotitlefromjob" in title.lower() and ".result" in title.lower():
        title = re.sub(r"^.*?\.result\s*", "", title, count=1, flags=re.I)
    return title.strip() or "Untitled Upwork opportunity"


def as_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def nested(data, *keys, default=None):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


VALID_RECOMMENDATIONS = {
    "strong_apply", "apply", "cautious_apply", "low_priority_apply", "skip"
}


def is_structured_stage5_report(data):
    """Require the minimum current Stage 5 shape used by the review workflow."""
    if not isinstance(data, dict):
        return False
    recommendation = nested(data, "recommendation", "data", "final_recommendation")
    return (
        str(recommendation or "").strip().lower() in VALID_RECOMMENDATIONS
        and isinstance(data.get("executive_summary"), dict)
        and isinstance(nested(data, "opportunity_assessment", "data"), dict)
        and isinstance(nested(data, "personal_fit", "data"), dict)
    )


def extract_system_warnings(report_data):
    """Normalize all supported Stage 5 system-warning shapes into one list."""
    if not isinstance(report_data, dict):
        return []

    rows = []
    seen = set()

    def add(value, severity="warning"):
        if value in (None, "", [], {}):
            return
        if isinstance(value, list):
            for item in value:
                add(item, severity)
            return
        if isinstance(value, dict):
            severity_keys = ("critical", "major", "minor", "warning", "warnings")
            if any(key in value for key in severity_keys):
                for key in severity_keys:
                    if key in value:
                        add(value[key], "warning" if key == "warnings" else key)
                return
            item_severity = str(value.get("severity") or severity).strip().lower()
            code = str(value.get("code") or "").strip()
            field = str(value.get("field") or "").strip()
            message = str(value.get("message") or value.get("description") or "").strip()
            if not message:
                message = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            item_severity, code, field, message = severity, "", "", str(value).strip()

        key = (item_severity, code, field, message)
        if message and key not in seen:
            seen.add(key)
            rows.append({
                "severity": item_severity.upper(),
                "code": code,
                "field": field,
                "message": message,
            })

    add(report_data.get("warnings"))
    add(report_data.get("report_warnings"))
    validation = report_data.get("validation")
    if isinstance(validation, dict):
        add(validation.get("warnings"))
    executive = report_data.get("executive_summary")
    if isinstance(executive, dict):
        add(executive.get("warnings"))
        present = {row["severity"].lower() for row in rows}
        for severity in ("critical", "major", "minor"):
            try:
                count = max(0, int(executive.get(f"{severity}_warning_count") or 0))
            except (TypeError, ValueError):
                count = 0
            if count and severity not in present:
                add(f"{count} {severity} system warning(s) recorded.", severity)
    return rows


def validated_upwork_url(row):
    """Return a safe Upwork HTTPS URL, preferring the original job URL."""
    for candidate in (getattr(row, "url", None), getattr(row, "canonical_url", None)):
        if candidate is None:
            continue
        try:
            if pd.isna(candidate):
                continue
            parsed = urlparse(str(candidate).strip())
            host = (parsed.hostname or "").lower().rstrip(".")
            if (
                parsed.scheme.lower() == "https"
                and not parsed.username
                and not parsed.password
                and (host == "upwork.com" or host.endswith(".upwork.com"))
            ):
                return parsed.geturl()
        except (TypeError, ValueError):
            continue
    return None


def fmt_time(value):
    try:
        return pd.to_datetime(value).strftime("%d %b %Y · %H:%M")
    except Exception:
        return safe(value)


def rec_meta(value):
    raw = str(value or "").lower().strip()
    return {
        "strong_apply": ("STRONG APPLY", "b-strong"),
        "apply": ("APPLY", "b-apply"),
        "cautious_apply": ("CAUTIOUS APPLY", "b-cautious"),
        "low_priority_apply": ("LOW PRIORITY", "b-low"),
        "skip": ("SKIP", "b-skip"),
    }.get(raw, ("LEGACY REPORT", "b-legacy"))


def score_num(value):
    try:
        return max(0, min(100, int(round(float(value)))))
    except Exception:
        return None


def money_label(row):
    if row.fixed_price is not None and not pd.isna(row.fixed_price):
        try:
            value = float(row.fixed_price)
            shown = f"${int(value):,}" if value.is_integer() else f"${value:,.2f}"
            return shown, "Fixed price"
        except Exception:
            pass

    if (
        row.hourly_min is not None and not pd.isna(row.hourly_min)
        and row.hourly_max is not None and not pd.isna(row.hourly_max)
    ):
        return f"${row.hourly_min}–${row.hourly_max}", "Hourly"

    if row.hourly_raw:
        return str(row.hourly_raw), "Hourly"

    return "—", "Unknown"


def kpi_card(icon, label, value, sub, css):
    html = (
        f'<div class="kpi {css}">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div>'
        f'<div class="kpi-label">{safe(label)}</div>'
        f'<div class="kpi-value">{safe(value)}</div>'
        f'<div class="kpi-sub">{safe(sub)}</div>'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def fact_box(css, label, value, sub):
    return (
        f'<div class="fact-box {css}">'
        f'<div class="fact-label">{label}</div>'
        f'<div class="fact-value">{safe(value)}</div>'
        f'<div class="fact-sub">{safe(sub)}</div>'
        f'</div>'
    )


def score_box(label, value, css, color):
    shown = "—" if value is None else str(value)
    width = 0 if value is None else value

    return (
        f'<div class="score">'
        f'<div class="score-label">{label}</div>'
        f'<div class="score-num {css}">{shown}<small>/100</small></div>'
        f'<div class="bar"><span style="width:{width}%;background:{color};"></span></div>'
        f'</div>'
    )


def render_demo_showcase_hero(row):
    """A compact visual orientation layer for the public fixture-backed demo."""
    data = as_dict(row.report_json)
    decision = score_num(nested(data, "recommendation", "data", "decision_score")) or 0
    opportunity = score_num(nested(data, "opportunity_assessment", "data", "score")) or 0
    fit = score_num(nested(data, "personal_fit", "data", "score")) or 0
    stages = ["Intake", "Extract", "Qualify", "Score", "Retrieve", "Decide", "Strategy", "Proposal", "Audit", "Report"]
    pipeline = "".join(
        f'<div class="pipeline-stage{" is-highlight" if stage in {"Retrieve", "Audit", "Report"} else ""}">'
        f'<div class="pipeline-index">{index:02d}</div><div class="pipeline-name">{stage}</div></div>'
        for index, stage in enumerate(stages, start=1)
    )
    st.markdown(
        '<div class="demo-safety-ribbon"><span><strong>SAFE DEMO ENVIRONMENT</strong> · local fixtures only · no database, external services, customer data, or marketplace access</span><span>Public showcase view</span></div>'
        '<section class="demo-hero">'
        '<div class="demo-eyebrow">Project-E · AI operations intelligence</div>'
        f'<div class="demo-hero-title">{escape(clean_title(row.title))}</div>'
        '<div class="demo-hero-sub">One opportunity, evaluated from intake through an evidence-linked, auditable proposal.</div>'
        '<div class="demo-hero-grid">'
        '<div class="demo-decision"><div class="demo-label">Final decision</div><div class="demo-value">STRONG APPLY</div><div class="demo-detail">Evidence-supported · ready for human review</div></div>'
        f'<div class="demo-metric"><div class="demo-label">Decision</div><div class="demo-value">{decision}<span style="font-size:.65rem;color:#9fb5cc"> / 100</span></div><div class="demo-detail">Composite confidence</div></div>'
        f'<div class="demo-metric"><div class="demo-label">Opportunity</div><div class="demo-value">{opportunity}<span style="font-size:.65rem;color:#9fb5cc"> / 100</span></div><div class="demo-detail">Commercial signal</div></div>'
        f'<div class="demo-metric"><div class="demo-label">Personal fit</div><div class="demo-value">{fit}<span style="font-size:.65rem;color:#9fb5cc"> / 100</span></div><div class="demo-detail">Delivery alignment</div></div>'
        '</div></section>'
        '<div class="pipeline-label">Ten-stage decision pipeline</div>'
        f'<div class="pipeline-strip">{pipeline}</div>',
        unsafe_allow_html=True,
    )


def make_card(row, selected_id):
    data = as_dict(row.report_json)
    rich = is_structured_stage5_report(data)

    selected_class = " selected" if selected_id == int(row.id) else ""
    rich_class = " rich" if rich else ""

    title = clean_title(
        nested(data, "job_summary", "data", "title", default=row.title)
        if rich else row.title
    )

    budget, budget_sub = money_label(row)

    rating = "—"
    if row.client_rating is not None and not pd.isna(row.client_rating):
        rating = f"{float(row.client_rating):.1f} ★"

    hires = (
        "—"
        if row.client_hires is None or pd.isna(row.client_hires)
        else str(int(row.client_hires))
    )

    proposals = safe(row.proposals)
    posted = safe(row.posted_time)
    human_status = str(
        getattr(row, "human_review_status", "unreviewed") or "unreviewed"
    ).lower()
    applied_at = getattr(row, "human_review_updated_at", None)

    facts = (
        fact_box("budget", "💰 Budget", budget, budget_sub)
        + fact_box("rating", "★ Client rating", rating, safe(row.client_country, ""))
        + fact_box("hires", "♟ Hires", hires, "Client history")
        + fact_box("proposals", "↗ Proposals", proposals, "Competition")
        + fact_box("posted", "▣ Posted", posted, "Upwork")
    )

    if rich:
        recommendation = nested(
            data, "recommendation", "data", "final_recommendation"
        )
        rec_label, rec_class = rec_meta(recommendation)

        decision = score_num(
            nested(data, "recommendation", "data", "decision_score")
        )
        opportunity = score_num(
            nested(data, "opportunity_assessment", "data", "score")
        )
        fit = score_num(
            nested(data, "personal_fit", "data", "score")
        )

        executive = nested(data, "executive_summary", default={}) or {}
        system_warnings = extract_system_warnings(data)
        warning_counts = {
            severity: sum(
                warning["severity"] == severity.upper()
                for warning in system_warnings
            )
            for severity in ("critical", "major", "minor")
        }

        pills = []
        if human_status == "applied":
            pills.append('<span class="pill p-applied">● APPLIED</span>')
        if executive.get("proposal_passed") is True:
            pills.append('<span class="pill p-ok">✓ Proposal passed</span>')
        if executive.get("ready_to_send") is True:
            pills.append('<span class="pill p-ok">✓ Ready to review</span>')
        if (
            executive.get("honesty_boundary_respected") is True
            and executive.get("must_not_claim_respected") is True
        ):
            pills.append('<span class="pill p-ok">✓ Honesty checks passed</span>')

        for severity in ("critical", "major", "minor"):
            if warning_counts[severity]:
                pills.append(
                    f'<span class="pill p-warn">⚠ '
                    f'{warning_counts[severity]} {severity}</span>'
                )
                break
        if system_warnings and not any(warning_counts.values()):
            pills.append(
                f'<span class="pill p-warn">⚠ {len(system_warnings)} warning(s)</span>'
            )
        applied_footer = (
            f'<span>↗ Applied {safe(fmt_time(applied_at))}</span>'
            if human_status == "applied"
            and applied_at is not None
            and not pd.isna(applied_at)
            else ""
        )

        html = (
            f'<div class="job-card{rich_class}{selected_class}">'
            f'<div class="card-head">'
            f'<div class="title-wrap">'
            f'<div class="card-icon">★</div>'
            f'<div><div class="job-title">{safe(title)}</div>'
            f'<div class="job-sub">{safe(row.experience_level, "")}</div></div>'
            f'</div>'
            f'<span class="badge {rec_class}">{rec_label}</span>'
            f'</div>'

            f'<div class="score-row">'
            f'{score_box("Decision", decision, "score-purple", "#d946ef")}'
            f'{score_box("Opportunity", opportunity, "score-blue", "#3b82f6")}'
            f'{score_box("Personal fit", fit, "score-green", "#22c55e")}'
            f'</div>'

            f'<div class="pill-row">{"".join(pills)}</div>'
            f'<div class="fact-grid">{facts}</div>'
            f'<div class="card-foot">'
            f'<span>◷ Analyzed {safe(fmt_time(row.created_at))}</span>'
            f'<span>▧ Report version {safe(row.version_number)}</span>'
            f'{applied_footer}'
            f'</div>'
            f'</div>'
        )
        return html, True

    html = (
        f'<div class="job-card{selected_class}">'
        f'<div class="card-head">'
        f'<div class="title-wrap">'
        f'<div class="card-icon legacy">▤</div>'
        f'<div><div class="job-title">{safe(title)}</div>'
        f'<div class="job-sub">{safe(row.experience_level, "")}</div></div>'
        f'</div>'
        f'<span class="badge b-legacy">LEGACY REPORT</span>'
        f'</div>'

        f'<div class="legacy-note">'
        f'ⓘ&nbsp;&nbsp;This report was created before structured Stage 5 JSON was stored. '
        f'The full Client Intelligence Report is still available.'
        f'</div>'

        f'<div class="fact-grid">{facts}</div>'
        f'<div class="card-foot">'
        f'<span>◷ Analyzed {safe(fmt_time(row.created_at))}</span>'
        f'<span>▧ Report version {safe(row.version_number)}</span>'
        f'</div>'
        f'</div>'
    )
    return html, False



def pretty_label(key):
    return str(key).replace("_", " ").strip().title()


def render_scalar(value):
    if isinstance(value, bool):
        css = "report-yes" if value else "report-no"
        label = "Yes" if value else "No"
        st.markdown(
            f'<div class="report-value {css}">{label}</div>',
            unsafe_allow_html=True,
        )
        return

    if value is None:
        st.markdown(
            '<div class="report-value">—</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="report-value">{escape(str(value))}</div>',
        unsafe_allow_html=True,
    )


def render_mapping(data, depth=0):
    """Render report JSON as readable human sections, not raw JSON."""
    if not isinstance(data, dict):
        render_report_value(data, depth)
        return

    for key, value in data.items():
        if value in (None, "", [], {}):
            continue

        label = pretty_label(key)

        if isinstance(value, dict):
            st.markdown(
                f'<div class="report-group">'
                f'<div class="report-group-title">{escape(label)}</div>',
                unsafe_allow_html=True,
            )
            render_mapping(value, depth + 1)
            st.markdown("</div>", unsafe_allow_html=True)

        elif isinstance(value, list):
            st.markdown(
                f'<div class="report-group">'
                f'<div class="report-group-title">{escape(label)}</div>',
                unsafe_allow_html=True,
            )
            render_report_value(value, depth + 1)
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            left, right = st.columns([1.35, 3.65])
            with left:
                st.markdown(
                    f'<div class="report-key">{escape(label)}</div>',
                    unsafe_allow_html=True,
                )
            with right:
                render_scalar(value)


def render_report_value(value, depth=0):
    if isinstance(value, dict):
        render_mapping(value, depth)
        return

    if isinstance(value, list):
        if not value:
            st.caption("None")
            return

        simple_items = all(
            not isinstance(item, (dict, list))
            for item in value
        )

        if simple_items:
            items = "".join(
                f"<li>{escape(str(item))}</li>"
                for item in value
            )
            st.markdown(
                f'<ul class="report-list">{items}</ul>',
                unsafe_allow_html=True,
            )
        else:
            for index, item in enumerate(value, start=1):
                st.markdown(
                    f'<div class="report-group-title">Item {index}</div>',
                    unsafe_allow_html=True,
                )
                render_report_value(item, depth + 1)
        return

    render_scalar(value)


def make_full_intelligence_report_readable(html_report):
    """Isolate and theme the saved Stage 5 report inside its review tab."""
    return (
        '<style>'
        '.full-intelligence-report{color:#e5edf7;background:#07111f;'
        'border:1px solid #24344d;border-radius:12px;padding:14px;}'
        '.full-intelligence-report :where('
        'h1,h2,h3,h4,h5,h6,p,div,span,li,td,th,dt,dd,a'
        '){color:inherit;}'
        '.full-intelligence-report .report-header{background:#0b1627;'
        'border-color:#334b70;padding:20px;}'
        '.full-intelligence-report .report-header h1,'
        '.full-intelligence-report .section h2{color:#eef2ff;}'
        '.full-intelligence-report .report-subtitle,'
        '.full-intelligence-report .header-label{color:#9fb0c7;}'
        '.full-intelligence-report .header-value{color:#e5edf7;}'
        '.full-intelligence-report .card{background:#0b1627;'
        'border-color:#2b3e5c;padding:16px;}'
        '.full-intelligence-report .nested-card{background:#0e1b2e;'
        'border-color:#334b70;padding:12px;}'
        '.full-intelligence-report .header-item{background:#0e1b2e;'
        'border-color:#334b70;padding:10px 12px;}'
        '.full-intelligence-report .proposal-full-text{background:#091525;'
        'border-color:#334b70;color:#e5edf7;padding:14px;}'
        '.full-intelligence-report .data-table>tbody>tr>td{'
        'background:#0b1627;color:#e5edf7;border-color:#263852;'
        'padding:7px 9px;}'
        '.full-intelligence-report .data-table>tbody>tr>th{'
        'background:#111f34;color:#c7d2fe;border-color:#334b70;'
        'padding:7px 9px;}'
        '.full-intelligence-report :where(ul,ol){padding-left:1.35rem;}'
        '</style>'
        f'<div class="full-intelligence-report">{html_report}</div>'
    )


def render_proposal_section(section_data):
    """Give proposal text a clean reading view when available."""
    if not isinstance(section_data, dict):
        render_report_value(section_data)
        return

    proposal_data = section_data.get("data")
    if isinstance(proposal_data, dict):
        full_text = proposal_data.get("full_text")
        if full_text:
            st.markdown(
                f'<div class="report-proposal">{escape(str(full_text))}</div>',
                unsafe_allow_html=True,
            )

            remaining = {
                key: value
                for key, value in proposal_data.items()
                if key != "full_text"
            }

            if remaining:
                st.markdown(
                    '<div class="report-section-note">'
                    'Additional generated-proposal details'
                    '</div>',
                    unsafe_allow_html=True,
                )
                render_mapping(remaining)
            return

    render_mapping(section_data)



def first_present(data, paths, default=None):
    for path in paths:
        current = data
        valid = True
        for key in path:
            if not isinstance(current, dict) or key not in current:
                valid = False
                break
            current = current[key]
        if valid and current not in (None, "", [], {}):
            return current
    return default


def normalize_list(value):
    if value in (None, "", {}):
        return []
    if isinstance(value, list):
        return value
    return [value]


def extract_review_data(report_data):
    executive = report_data.get("executive_summary") or {}

    return {
        "recommendation": first_present(
            report_data,
            [
                ("recommendation", "data", "final_recommendation"),
                ("recommendation", "final_recommendation"),
                ("executive_summary", "final_recommendation"),
            ],
        ),
        "decision_score": first_present(
            report_data,
            [
                ("recommendation", "data", "decision_score"),
                ("recommendation", "decision_score"),
                ("executive_summary", "decision_score"),
            ],
        ),
        "opportunity_score": first_present(
            report_data,
            [
                ("opportunity_assessment", "data", "score"),
                ("opportunity_assessment", "score"),
            ],
        ),
        "fit_score": first_present(
            report_data,
            [
                ("personal_fit", "data", "score"),
                ("personal_fit", "score"),
            ],
        ),
        "strengths": normalize_list(
            first_present(
                report_data,
                [
                    ("personal_fit", "data", "strengths"),
                    ("personal_fit", "strengths"),
                    ("executive_summary", "strengths"),
                ],
                [],
            )
        ),
        "concerns": normalize_list(
            first_present(
                report_data,
                [
                    ("personal_fit", "data", "concerns"),
                    ("personal_fit", "concerns"),
                    ("recommendation", "data", "concerns"),
                    ("executive_summary", "concerns"),
                ],
                [],
            )
        ),
        "system_warnings": extract_system_warnings(report_data),
        "proposal_text": str(
            first_present(
                report_data,
                [
                    ("generated_proposal", "data", "full_text"),
                    ("generated_proposal", "full_text"),
                    ("proposal_output", "proposal", "full_text"),
                    ("proposal_output", "full_text"),
                    ("proposal", "full_text"),
                ],
                "",
            )
            or ""
        ),
        "must_not_claim": normalize_list(
            first_present(
                report_data,
                [
                    ("proposal_strategy", "data", "must_not_claim"),
                    ("proposal_strategy", "must_not_claim"),
                    ("personal_fit", "data", "must_not_claim"),
                    ("personal_fit", "must_not_claim"),
                ],
                [],
            )
        ),
        "ready_to_send": executive.get("ready_to_send") is True,
        "proposal_passed": executive.get("proposal_passed") is True,
        "honesty_ok": (
            executive.get("honesty_boundary_respected") is True
            and executive.get("must_not_claim_respected") is True
        ),
    }


def render_bullet_callout(title, items, css_class):
    items = [item for item in normalize_list(items) if item not in (None, "")]

    if not items:
        body = "None recorded."
    else:
        body = "<ul style='margin:.2rem 0 .1rem 1.05rem;padding:0;'>"
        for item in items:
            if isinstance(item, dict):
                body += f"<li>{escape(json.dumps(item, ensure_ascii=False))}</li>"
            else:
                body += f"<li>{escape(str(item))}</li>"
        body += "</ul>"

    st.markdown(
        f'<div class="review-callout {css_class}">'
        f'<div class="review-callout-title">{escape(title)}</div>'
        f'<div class="review-callout-body">{body}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_review_workspace(row):
    report_data = as_dict(row.report_json)
    review = extract_review_data(report_data)

    title = clean_title(
        first_present(
            report_data,
            [
                ("job_summary", "data", "title"),
                ("job_summary", "title"),
            ],
            row.title,
        )
    )

    recommendation_label, recommendation_class = rec_meta(
        review["recommendation"]
    )

    top_left, top_right = st.columns([5, 1])

    with top_left:
        st.markdown(
            f'<div class="eyebrow">Project-E · Review workspace</div>'
            f'<h1 class="review-heading">{escape(title)}</h1>'
            f'<div class="review-subtitle">Job {escape(str(row.job_id))} · Report version {escape(str(row.version_number))}</div>',
            unsafe_allow_html=True,
        )

    with top_right:
        if st.button(
            "← Back to inbox",
            use_container_width=True,
            key="back_to_inbox_v7",
        ):
            st.session_state.review_mode = False
            st.session_state.selected_report_id = None
            st.rerun()

    st.markdown(
        f'<span class="badge {recommendation_class}">'
        f'{escape(recommendation_label)}'
        f'</span>',
        unsafe_allow_html=True,
    )

    current_human_status = str(
        getattr(row, "human_review_status", "unreviewed") or "unreviewed"
    ).lower()

    upwork_url = validated_upwork_url(row)
    if upwork_url and current_human_status != "approved":
        st.link_button(
            "↗ Open Upwork Job",
            upwork_url,
            use_container_width=False,
        )
    elif not upwork_url and not IS_DEMO_MODE:
        st.caption(
            "No marketplace URL is included in this safe demo."
            if IS_DEMO_MODE
            else "No validated Upwork job URL is available for this report."
        )

    human_label, human_class = human_status_meta(current_human_status)

    st.markdown(f'<span class="human-state {human_class}">{human_label}</span>', unsafe_allow_html=True)
    if current_human_status == "applied":
        applied_at = getattr(row, "human_review_updated_at", None)
        if applied_at is not None and not pd.isna(applied_at):
            st.caption(f"Applied at: {fmt_time(applied_at)}")

    def save_decision(status, destination):
        try:
            set_human_review_status(row.job_id, status)
        except Exception:
            st.error("Decision could not be saved. No change was recorded. Please retry.")
            return False
        st.session_state.review_mode = False
        st.session_state.selected_report_id = None
        st.query_params["view"] = destination
        feedback_labels = {
            "approved": "Job marked as Approved.",
            "reviewing": "Job moved to Reviewing.",
            "skipped": "Job marked as Skipped.",
            "applied": "Job marked as Applied.",
        }
        st.session_state._action_feedback = feedback_labels.get(
            status,
            "Decision saved.",
        )
        return True

    with st.expander("Human decision controls", expanded=False):
        d1, d2, d3 = st.columns(3)
        with d1:
            if st.button("✓ APPROVE", use_container_width=True, type="primary", key=f"approve_{row.job_id}"):
                if save_decision("approved", "approved"):
                    st.rerun()
        with d2:
            if st.button("◷ KEEP REVIEWING", use_container_width=True, key=f"reviewing_{row.job_id}"):
                if save_decision("reviewing", "reviewing"):
                    st.rerun()
        with d3:
            if st.button("✕ SKIP", use_container_width=True, key=f"skip_{row.job_id}"):
                if save_decision("skipped", "skipped"):
                    st.rerun()

    if current_human_status == "approved":
        with st.container(key="application_actions"):
            st.markdown(
                '<div class="section-kicker">Application actions</div>',
                unsafe_allow_html=True,
            )
            action_copy, action_open, action_applied = st.columns(3)

            with action_copy:
                if review["proposal_text"]:
                    with st.expander("COPY PROPOSAL", expanded=False):
                        st.code(
                            review["proposal_text"],
                            language=None,
                            wrap_lines=True,
                        )
                else:
                    st.info("No proposal is available to copy.")

            with action_open:
                if upwork_url:
                    st.link_button(
                        "↗ OPEN UPWORK JOB",
                        upwork_url,
                        use_container_width=True,
                    )
                elif not IS_DEMO_MODE:
                    st.caption(
                        "No validated Upwork job URL is available."
                    )

            with action_applied:
                if st.button(
                    "✓ MARK AS APPLIED",
                    use_container_width=True,
                    key=f"applied_{row.job_id}",
                ):
                    if save_decision("applied", "applied"):
                        st.rerun()

    decision = score_num(review["decision_score"])
    opportunity = score_num(review["opportunity_score"])
    fit = score_num(review["fit_score"])

    st.markdown(
        '<div class="review-summary-grid">'
        f'<div class="review-summary-card">'
        f'<div class="review-summary-label">Decision score</div>'
        f'<div class="review-summary-value">'
        f'{decision if decision is not None else "—"}/100'
        f'</div></div>'
        f'<div class="review-summary-card">'
        f'<div class="review-summary-label">Opportunity</div>'
        f'<div class="review-summary-value">'
        f'{opportunity if opportunity is not None else "—"}/100'
        f'</div></div>'
        f'<div class="review-summary-card">'
        f'<div class="review-summary-label">Personal fit</div>'
        f'<div class="review-summary-value">'
        f'{fit if fit is not None else "—"}/100'
        f'</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    statuses = [
        ("✓ Proposal passed" if review["proposal_passed"] else "Proposal needs review", review["proposal_passed"]),
        ("✓ Honesty checks passed" if review["honesty_ok"] else "Check honesty boundaries", review["honesty_ok"]),
        ("✓ Ready for review" if review["ready_to_send"] else "Not ready to send", review["ready_to_send"]),
    ]
    st.markdown(
        '<div class="compact-statuses">'
        + "".join(f'<span class="compact-status{"" if okay else " warn"}">{escape(label)}</span>' for label, okay in statuses)
        + '</div>',
        unsafe_allow_html=True,
    )

    tab_summary, tab_evidence, tab_proposal, tab_history, tab_report = st.tabs(
        [
            "Decision Summary",
            "Evidence",
            "Proposal & Audit",
            "Decision History",
            "Full Intelligence Report",
        ]
    )

    with tab_summary:
        system_warning_rows = review["system_warnings"]

        if system_warning_rows:
            severity_counts = {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0}
            for item in system_warning_rows:
                severity = str(item.get("severity") or "MINOR").upper()
                if severity not in severity_counts:
                    severity = "MINOR"
                message = str(item.get("message") or "")
                aggregate = re.match(
                    r"^\s*(\d+)\s+(critical|major|minor)\s+"
                    r"(?:system\s+)?warning",
                    message,
                    flags=re.IGNORECASE,
                )
                represented_count = int(aggregate.group(1)) if aggregate else 1
                severity_counts[severity] += represented_count

            count_parts = []
            for severity in ("CRITICAL", "MAJOR", "MINOR"):
                count = severity_counts[severity]
                if count:
                    noun = "WARNING" if count == 1 else "WARNINGS"
                    count_parts.append(f"{count} {severity} {noun}")

            total_warnings = sum(severity_counts.values())
            total_noun = "warning" if total_warnings == 1 else "warnings"
            st.markdown(
                '<div class="system-warning-summary">'
                '<div class="system-warning-summary-title">⚠ SYSTEM WARNINGS</div>'
                f'<div class="system-warning-summary-count">'
                f'{escape(" · ".join(count_parts))}</div>'
                f'<div class="system-warning-summary-body">Project-E recorded '
                f'{total_warnings} validation {total_noun}.</div>'
                '<div class="system-warning-summary-detail">'
                'See Full Intelligence Report for details.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.success("✓ No Project-E system warnings recorded for this job.")

        left, right = st.columns(2, gap="medium")

        with left:
            render_bullet_callout(
                "Why this job may fit",
                review["strengths"],
                "good",
            )

        with right:
            render_bullet_callout(
                "Job / fit concerns",
                review["concerns"],
                "warn",
            )

        if review["must_not_claim"]:
            render_bullet_callout(
                "Must not claim",
                review["must_not_claim"],
                "warn",
            )

        if report_data:
            with st.expander(
                "Structured intelligence details",
                expanded=False,
            ):
                sections = [
                    ("Executive Summary", report_data.get("executive_summary")),
                    ("Job Summary", report_data.get("job_summary")),
                    ("Opportunity Assessment", report_data.get("opportunity_assessment")),
                    ("Personal Fit", report_data.get("personal_fit")),
                    ("Retrieved Evidence", report_data.get("retrieved_evidence")),
                    ("Recommendation", report_data.get("recommendation")),
                    ("Proposal Strategy", report_data.get("proposal_strategy")),
                    ("Proposal Audit", report_data.get("proposal_audit")),
                    ("Validation", report_data.get("validation")),
                    ("Report Warnings", report_data.get("report_warnings")),
                ]

                for section_title, section_data in sections:
                    if section_data in (None, {}, [], ""):
                        continue

                    with st.expander(
                        section_title,
                        expanded=False,
                    ):
                        render_report_value(section_data)

    with tab_evidence:
        evidence_data = nested(report_data, "retrieved_evidence", "data", default={}) or {}
        evidence_items = evidence_data.get("items", []) if isinstance(evidence_data, dict) else []
        if evidence_items:
            cards = []
            for item in evidence_items:
                if not isinstance(item, dict):
                    continue
                relevance = score_num(item.get("relevance_score"))
                cards.append(
                    '<article class="evidence-card">'
                    '<div class="evidence-card-top">'
                    f'<span class="evidence-id">{escape(str(item.get("evidence_id") or "EVIDENCE"))}</span>'
                    f'<span class="evidence-score">{escape(str(relevance if relevance is not None else "—"))}% RELEVANCE</span>'
                    '</div>'
                    '<div class="evidence-field">Evidence source</div>'
                    f'<div class="evidence-title">{escape(str(item.get("source") or item.get("section_title") or "Evidence"))}</div>'
                    '<div class="evidence-field">Supported claim</div>'
                    f'<div class="evidence-claim">{escape(str(item.get("claim") or item.get("excerpt") or ""))}</div>'
                    '<div class="evidence-field">Proposal influence</div>'
                    f'<div class="evidence-link">↳ {escape(str(item.get("proposal_link") or "Connected to the proposal strategy."))}</div>'
                    '</article>'
                )
            st.markdown(
                '<div class="evidence-intro">Each retrieved source is traceable to a supported claim and its practical influence on the proposed response.</div>'
                f'<div class="evidence-grid">{"".join(cards)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No retrieved evidence was stored with this report.")

    with tab_proposal:
        audit_data = nested(report_data, "proposal_audit", "data", default={}) or {}
        proposal_col, audit_col = st.columns([1.45, 0.8], gap="large")
        with proposal_col:
            st.markdown('<div class="section-kicker">Generated proposal</div>', unsafe_allow_html=True)
            if review["proposal_text"]:
                evidence_badges = nested(report_data, "retrieved_evidence", "data", "items", default=[]) or []
                badge_html = "".join(
                    f'<span>{escape(str(item.get("evidence_id") or "EV"))} · {escape(str(item.get("proposal_link") or "Evidence-supported"))}</span>'
                    for item in evidence_badges[:3] if isinstance(item, dict)
                )
                st.markdown(f'<div class="proposal-evidence">{badge_html}</div>', unsafe_allow_html=True)
                copy_payload = json.dumps(review["proposal_text"])
                copy_document = (
                    '<!doctype html><html><body style="margin:0;background:transparent">'
                    '<button id="copy-proposal" style="background:linear-gradient(180deg,#1d4f75,#163755);border:1px solid #4da3d9;color:#f0f9ff;border-radius:8px;padding:8px 13px;font:700 12px Inter,Segoe UI,sans-serif;cursor:pointer" '
                    f'onclick="navigator.clipboard.writeText({escape(copy_payload, quote=True)}).then(() => this.textContent=\'✓ Proposal copied\').catch(() => this.textContent=\'Copy unavailable\')">Copy Proposal</button>'
                    '</body></html>'
                )
                copy_url = "data:text/html;base64," + base64.b64encode(copy_document.encode("utf-8")).decode("ascii")
                st.iframe(copy_url, height=42)
                st.markdown(
                    f'<div class="review-proposal">'
                    f'{escape(review["proposal_text"])}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    f'{len(review["proposal_text"].split())} words · '
                    f'Generated proposal · Read-only · Use the copy icon below'
                )
                with st.expander("View proposal text for manual copy", expanded=False):
                    st.code(review["proposal_text"], language=None, wrap_lines=True)
            else:
                st.info("No structured proposal text was found in this saved report.")

        with audit_col:
            audit_passed = audit_data.get("passed") is True
            checks = audit_data.get("checks", []) if isinstance(audit_data, dict) else []
            check_html = "".join(
                f'<div class="audit-check"><span>✓</span><div>{escape(str(check))}</div></div>'
                for check in checks
            ) or '<div class="audit-check"><span>•</span><div>Audit detail unavailable.</div></div>'
            st.markdown(
                '<aside class="audit-panel">'
                '<div class="demo-label">Proposal audit</div>'
                f'<div class="audit-result">{"PASSED — 6/6 checks" if audit_passed else "REVIEW REQUIRED"}</div>'
                '<span class="audit-zero">0 unsupported claims</span>'
                '<div class="demo-detail" style="margin-top:9px">Evidence-linked trust and validation gate</div>'
                f'{check_html}'
                '</aside>',
                unsafe_allow_html=True,
            )

    with tab_history:
        history_load_failed = False
        try:
            history = get_human_review_history(row.job_id)
        except Exception:
            history = pd.DataFrame()
            history_load_failed = True
            st.error("Decision history could not be loaded. Please retry.")

        if history.empty and not history_load_failed:
            st.info("No human decision changes recorded yet.")
        elif not history.empty:
            display_history = history.copy()

            display_history["previous_status"] = (
                display_history["previous_status"]
                .astype(str)
                .str.replace("_", " ")
                .str.title()
            )

            display_history["new_status"] = (
                display_history["new_status"]
                .astype(str)
                .str.replace("_", " ")
                .str.title()
            )

            display_history["changed_at"] = pd.to_datetime(
                display_history["changed_at"]
            ).dt.strftime("%d %b %Y · %H:%M:%S")

            display_history = display_history.rename(
                columns={
                    "previous_status": "From",
                    "new_status": "To",
                    "changed_at": "Changed at",
                }
            )

            st.dataframe(
                display_history[["Changed at", "From", "To"]],
                use_container_width=True,
                hide_index=True,
            )

    with tab_report:
        html_load_failed = False
        try:
            html_report = get_report_html(int(row.id))
        except Exception:
            html_report = ""
            html_load_failed = True
            st.error("The saved HTML report could not be loaded. Please retry.")

        if html_report and IS_DEMO_MODE:
            executive = report_data.get("executive_summary", {}) or {}
            recommendation = nested(report_data, "recommendation", "data", default={}) or {}
            opportunity_data = nested(report_data, "opportunity_assessment", "data", default={}) or {}
            fit_data = nested(report_data, "personal_fit", "data", default={}) or {}
            reasons = recommendation.get("rationale", []) or opportunity_data.get("rationale", []) or []
            risks = fit_data.get("concerns", []) or []
            evidence = nested(report_data, "retrieved_evidence", "data", "items", default=[]) or []
            evidence_summary = "; ".join(
                str(item.get("proposal_link") or item.get("claim") or "")
                for item in evidence[:2] if isinstance(item, dict)
            )
            st.markdown(
                '<section class="report-focus">'
                '<div class="demo-eyebrow">Executive intelligence report</div>'
                f'<h2>{escape(title)}</h2>'
                f'<p>{escape(str(executive.get("summary") or recommendation.get("next_step") or "Decision-ready opportunity intelligence."))}</p>'
                '<div class="report-focus-grid">'
                f'<div class="report-focus-card"><strong>Recommendation</strong><span>{escape(str(recommendation.get("final_recommendation") or "Strong apply")).replace("_", " ").upper()} · {escape(str(recommendation.get("next_step") or "Ready for human review."))}</span></div>'
                f'<div class="report-focus-card"><strong>Key reasons</strong><span>{escape(" · ".join(str(item) for item in reasons[:2]) or "Clear opportunity and delivery fit.")}</span></div>'
                f'<div class="report-focus-card"><strong>Risks & evidence-backed fit</strong><span>{escape(" · ".join(str(item) for item in risks[:1]) or "No material risks recorded.")} {escape(evidence_summary)}</span></div>'
                '</div></section>',
                unsafe_allow_html=True,
            )
            action_one, action_two = st.columns([1, 1.4])
            with action_one:
                st.download_button(
                    "Download report HTML",
                    data=html_report,
                    file_name="project-e-demo-intelligence-report.html",
                    mime="text/html",
                    use_container_width=True,
                )
            with action_two:
                st.download_button(
                    "Download structured report JSON",
                    data=json.dumps(report_data, indent=2),
                    file_name="project-e-demo-intelligence-report.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with st.expander("Open full report detail", expanded=False):
                st.html(make_full_intelligence_report_readable(html_report))
        elif html_report:
            st.html(make_full_intelligence_report_readable(html_report))
        elif not html_load_failed:
            st.error("No saved HTML report found.")


def human_status_meta(status):
    status = str(status or "unreviewed").strip().lower()
    return {
        "unreviewed": ("UNREVIEWED", "state-unreviewed"),
        "reviewing": ("REVIEWING", "state-reviewing"),
        "approved": ("APPROVED", "state-approved"),
        "applied": ("APPLIED", "state-applied"),
        "skipped": ("SKIPPED", "state-skipped"),
    }.get(status, ("UNREVIEWED", "state-unreviewed"))


# =============================================================================
# STATE
# =============================================================================

if "selected_report_id" not in st.session_state:
    st.session_state.selected_report_id = None

if "review_mode" not in st.session_state:
    st.session_state.review_mode = False

if "page" not in st.session_state:
    st.session_state.page = 1

if "quick_filter" not in st.session_state:
    st.session_state.quick_filter = "All jobs"

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "page_size" not in st.session_state:
    st.session_state.page_size = 4

if "sort_choice" not in st.session_state:
    st.session_state.sort_choice = "Newest analyzed"

if "_action_feedback" not in st.session_state:
    st.session_state._action_feedback = None

if "archive_page" not in st.session_state:
    st.session_state.archive_page = 1


# =============================================================================
# APP
# =============================================================================

try:
    action_feedback = st.session_state.pop("_action_feedback", None)
    if action_feedback:
        st.toast(action_feedback, icon="✅")

    if not test_connection():
        st.error("Project-E demo fixtures could not be loaded." if IS_DEMO_MODE else "Project-E cannot reach PostgreSQL.")
        st.stop()

    reports = get_latest_reports()

    if reports.empty:
        st.info("No reports saved yet.")
        st.stop()

    inbox = (
        reports
        .sort_values(["created_at", "id"], ascending=[False, False])
        .drop_duplicates(subset=["job_id"], keep="first")
        .reset_index(drop=True)
    )

    inbox["_data"] = inbox["report_json"].apply(as_dict)
    inbox["_rich"] = inbox["_data"].apply(is_structured_stage5_report)

    # V8.3 rule:
    # Legacy reports remain available in Report Archive only.
    # Only structured Stage 5 jobs participate in the human review workflow.
    inbox["_actionable"] = inbox["_rich"]

    inbox["human_review_status"] = (
        inbox["human_review_status"]
        .fillna("unreviewed")
        .astype(str)
        .str.lower()
    )

    def ex(data):
        return nested(data, "executive_summary", default={}) or {}

    inbox["_ready"] = inbox["_data"].apply(
        lambda d: ex(d).get("ready_to_send") is True
    )

    inbox["_warnings"] = inbox["_data"].apply(
        lambda d: bool(extract_system_warnings(d))
    )

    inbox["_high_opportunity"] = inbox["_data"].apply(
        lambda d: (
            score_num(
                nested(d, "opportunity_assessment", "data", "score")
            ) or 0
        ) >= 70
    )
    inbox["_decision_score"] = inbox["_data"].apply(
        lambda d: score_num(
            nested(d, "recommendation", "data", "decision_score")
        )
    )
    inbox["_opportunity_score"] = inbox["_data"].apply(
        lambda d: score_num(
            nested(d, "opportunity_assessment", "data", "score")
        )
    )
    inbox["_fit_score"] = inbox["_data"].apply(
        lambda d: score_num(
            nested(d, "personal_fit", "data", "score")
        )
    )

    archive_reports = pd.DataFrame()

    # -------------------------------------------------------------------------
    # Sidebar — custom navigation / quick filters
    # -------------------------------------------------------------------------

    def qp_value(name, default):
        try:
            value = st.query_params.get(name, default)
            if isinstance(value, list):
                return value[0] if value else default
            return value or default
        except Exception:
            return default

    view_slug = qp_value("view", "inbox")
    filter_slug = qp_value("filter", "all")

    workspace_map = {
        "inbox": "Job Inbox",
        "approved": "Approved",
        "reviewing": "Reviewing",
        "applied": "Applied",
        "skipped": "Skipped",
        "archive": "Report Archive",
    }
    workspace = workspace_map.get(view_slug, "Job Inbox")
    current_view_slug = view_slug if view_slug in workspace_map else "inbox"

    # Quick-filter counts describe only the currently selected human bucket.
    actionable_inbox = inbox.loc[inbox["_actionable"]].copy()

    if workspace == "Job Inbox":
        bucket_for_counts = actionable_inbox.loc[
            actionable_inbox["human_review_status"] == "unreviewed"
        ]
    elif workspace == "Approved":
        bucket_for_counts = actionable_inbox.loc[
            actionable_inbox["human_review_status"] == "approved"
        ]
    elif workspace == "Reviewing":
        bucket_for_counts = actionable_inbox.loc[
            actionable_inbox["human_review_status"] == "reviewing"
        ]
    elif workspace == "Applied":
        bucket_for_counts = actionable_inbox.loc[
            actionable_inbox["human_review_status"] == "applied"
        ]
    elif workspace == "Skipped":
        bucket_for_counts = actionable_inbox.loc[
            actionable_inbox["human_review_status"] == "skipped"
        ]
    else:
        bucket_for_counts = actionable_inbox

    counts = {
        "All jobs": len(bucket_for_counts),
        "Rich intelligence": int(bucket_for_counts["_rich"].sum()),
        "Ready to review": int(bucket_for_counts["_ready"].sum()),
        "System warnings": int(bucket_for_counts["_warnings"].sum()),
        "High opportunity": int(bucket_for_counts["_high_opportunity"].sum()),
        "Legacy reports": int((~bucket_for_counts["_rich"]).sum()),
    }

    filter_slug_to_name = {
        "all": "All jobs",
        "rich": "Rich intelligence",
        "ready": "Ready to review",
        "warnings": "System warnings",
        "high": "High opportunity",
        "legacy": "Legacy reports",
    }

    st.session_state.quick_filter = filter_slug_to_name.get(
        filter_slug,
        "All jobs",
    )

    nav_signature = f"{workspace}|{filter_slug}"
    if st.session_state.get("_nav_signature") != nav_signature:
        st.session_state._nav_signature = nav_signature
        st.session_state.page = 1

    def nav_row(
        href,
        icon,
        label,
        count=None,
        selected=False,
        icon_class="i-white",
        selected_class="",
    ):
        selected_css = " selected" if selected else ""
        semantic_css = f" {selected_class}" if selected and selected_class else ""
        count_html = (
            f'<span class="sidebar-count">{count}</span>'
            if count is not None else ""
        )
        return (
            f'<a class="sidebar-link{selected_css}{semantic_css}" href="{href}" target="_self">'
            f'<span class="sidebar-link-main">'
            f'<span class="sidebar-icon {icon_class}">{icon}</span>'
            f'<span class="sidebar-label">{label}</span>'
            f'</span>'
            f'{count_html}'
            f'</a>'
        )

    with st.sidebar:
        st.markdown(
            '<div class="brand">'
            '<div class="brand-mark">⚡</div>'
            '<div class="brand-name">Project-E</div>'
            '</div>'
            '<div class="brand-sub">AI Job Intelligence Platform</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="side-heading">Workspace</div>',
            unsafe_allow_html=True,
        )

        workspace_counts = {
            "Job Inbox": int(
                (
                    actionable_inbox["human_review_status"] == "unreviewed"
                ).sum()
            ),
            "Approved": int(
                (
                    actionable_inbox["human_review_status"] == "approved"
                ).sum()
            ),
            "Reviewing": int(
                (
                    actionable_inbox["human_review_status"] == "reviewing"
                ).sum()
            ),
            "Applied": int(
                (
                    actionable_inbox["human_review_status"] == "applied"
                ).sum()
            ),
            "Skipped": int(
                (
                    actionable_inbox["human_review_status"] == "skipped"
                ).sum()
            ),
        }

        workspace_html = (
            '<div class="sidebar-nav-panel workspace">'
            + nav_row(
                "?view=inbox&filter=all",
                "▣",
                "Job Inbox",
                workspace_counts["Job Inbox"],
                selected=(workspace == "Job Inbox"),
                icon_class="i-purple",
            )
            + nav_row(
                "?view=approved",
                "✓",
                "Approved",
                workspace_counts["Approved"],
                selected=(workspace == "Approved"),
                icon_class="i-green",
                selected_class="sel-green",
            )
            + nav_row(
                "?view=reviewing",
                "◷",
                "Reviewing",
                workspace_counts["Reviewing"],
                selected=(workspace == "Reviewing"),
                icon_class="i-amber",
                selected_class="sel-amber",
            )
            + nav_row(
                "?view=applied",
                "↗",
                "Applied",
                workspace_counts["Applied"],
                selected=(workspace == "Applied"),
                icon_class="i-cyan",
                selected_class="sel-cyan",
            )
            + nav_row(
                "?view=skipped",
                "✕",
                "Skipped",
                workspace_counts["Skipped"],
                selected=(workspace == "Skipped"),
                icon_class="i-red",
                selected_class="sel-red",
            )
            + nav_row(
                "?view=archive",
                "▤",
                "Report Archive",
                None,
                selected=(workspace == "Report Archive"),
                icon_class="i-white",
            )
            + '</div>'
        )

        st.markdown(workspace_html, unsafe_allow_html=True)

        if workspace in {"Job Inbox", "Approved", "Reviewing", "Applied", "Skipped"}:
            st.markdown(
                '<div class="side-heading">Quick filters</div>',
                unsafe_allow_html=True,
            )

            quick_html = (
                '<div class="sidebar-nav-panel">'
                + nav_row(
                    f"?view={current_view_slug}&filter=all",
                    "▦",
                    "All jobs",
                    counts["All jobs"],
                    selected=(filter_slug == "all"),
                    icon_class="i-purple",
                )
                + nav_row(
                    f"?view={current_view_slug}&filter=rich",
                    "☆",
                    "Rich intelligence",
                    counts["Rich intelligence"],
                    selected=(filter_slug == "rich"),
                    icon_class="i-green",
                    selected_class="sel-green",
                )
                + nav_row(
                    f"?view={current_view_slug}&filter=ready",
                    "◎",
                    "Ready to review",
                    counts["Ready to review"],
                    selected=(filter_slug == "ready"),
                    icon_class="i-amber",
                    selected_class="sel-amber",
                )
                + nav_row(
                    f"?view={current_view_slug}&filter=warnings",
                    "△",
                    "System warnings",
                    counts["System warnings"],
                    selected=(filter_slug == "warnings"),
                    icon_class="i-red",
                    selected_class="sel-red",
                )
                + nav_row(
                    f"?view={current_view_slug}&filter=high",
                    "↗",
                    "High opportunity",
                    counts["High opportunity"],
                    selected=(filter_slug == "high"),
                    icon_class="i-yellow",
                    selected_class="sel-amber",
                )
                + '</div>'
            )

            st.markdown(quick_html, unsafe_allow_html=True)

        st.markdown(
            '<div class="sidebar-separator"></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="side-heading">System status</div>',
            unsafe_allow_html=True,
        )

        with st.expander("● Local application online", expanded=False):
            st.markdown(
                '<div class="system-sub">'
                '✓ Streamlit dashboard running<br>'
                + ('✓ Local demo fixtures verified<br>✓ No database or external services used<br>✓ Marketplace access disabled' if IS_DEMO_MODE else '✓ PostgreSQL connection verified<br>✓ Report database access verified<br>– n8n: not checked')
                + '</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="version-chip">'
            '<div class="pulse-dots">'
            '<span></span><span></span><span></span>'
            '<span></span><span></span><span></span>'
            '</div>'
            '<div>Dashboard v8.7</div>'
            '<div class="version-sub">Intelligence data read-only · Human decisions enabled</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # Review Job workspace
    # -------------------------------------------------------------------------

    if (
        workspace in {"Job Inbox", "Approved", "Reviewing", "Applied", "Skipped"}
        and st.session_state.review_mode
        and st.session_state.selected_report_id is not None
    ):
        selected_matches = reports.loc[
            reports["id"] == st.session_state.selected_report_id
        ]

        if selected_matches.empty:
            st.error("The selected report could not be found.")
            st.session_state.review_mode = False
        else:
            render_review_workspace(
                next(selected_matches.itertuples())
            )

    # -------------------------------------------------------------------------
    # Inbox
    # -------------------------------------------------------------------------

    elif workspace in {"Job Inbox", "Approved", "Reviewing", "Applied", "Skipped"}:
        workspace_titles = {
            "Job Inbox": (
                "Job Intelligence Inbox",
                "New jobs waiting for your decision."
            ),
            "Approved": (
                "Approved Jobs",
                "Jobs you approved for application action."
            ),
            "Reviewing": (
                "Reviewing",
                "Jobs you want to keep considering."
            ),
            "Applied": (
                "Applied Jobs",
                "Jobs you manually applied to on Upwork."
            ),
            "Skipped": (
                "Skipped Jobs",
                "Jobs you decided not to pursue."
            ),
        }

        workspace_title, workspace_subtitle = workspace_titles[workspace]

        if not (IS_DEMO_MODE and workspace == "Job Inbox"):
            st.markdown(
                f'<div class="eyebrow">Project-E · Dashboard V8.7</div>'
                f'<h1 class="page-title">{escape(workspace_title)}</h1>'
                f'<p class="page-sub">{escape(workspace_subtitle)}</p>',
                unsafe_allow_html=True,
            )

        if IS_DEMO_MODE and workspace == "Job Inbox" and not inbox.empty:
            render_demo_showcase_hero(next(inbox.itertuples()))

        sort_options = [
            "Newest analyzed",
            "Oldest analyzed",
            "Highest decision score",
            "Highest opportunity score",
            "Highest personal fit",
            "Lowest personal fit",
        ]
        compact_demo_inbox = IS_DEMO_MODE and workspace == "Job Inbox"
        if compact_demo_inbox:
            search_value = ""
            search = ""
        else:
            k1, k2, k3, k4 = st.columns(4, gap="small")
            with k1:
                kpi_card("▣", workspace_title, len(bucket_for_counts), "Jobs in this workspace", "kpi-blue")
            with k2:
                kpi_card("✦", "Rich intelligence", counts["Rich intelligence"], "Structured Stage 5 data", "kpi-green")
            with k3:
                kpi_card("◎", "Ready to review", counts["Ready to review"], "Pending your review", "kpi-amber")
            with k4:
                kpi_card("⚠", "System warnings", counts["System warnings"], "Check before applying", "kpi-red")
            search_col, sort_col, refresh_col = st.columns([4.2, 2.1, 1])
            with search_col:
                search_value = st.text_input("Search", placeholder="Search by job title or job ID...", label_visibility="collapsed", key="search_query").strip()
                search = search_value.lower()
            with sort_col:
                selected_sort = st.selectbox("Sort jobs", sort_options, index=sort_options.index(st.session_state.sort_choice), label_visibility="collapsed", key="sort_select_v87")
                if selected_sort != st.session_state.sort_choice:
                    st.session_state.sort_choice = selected_sort
                    st.session_state.page = 1
            with refresh_col:
                if st.button("↻ Refresh", use_container_width=True):
                    st.rerun()

        # Human workflow screens contain structured jobs only.
        # Legacy reports are intentionally kept in Report Archive.
        filtered = actionable_inbox.copy()

        if workspace == "Job Inbox":
            filtered = filtered.loc[
                filtered["human_review_status"] == "unreviewed"
            ]
        elif workspace == "Approved":
            filtered = filtered.loc[
                filtered["human_review_status"] == "approved"
            ]
        elif workspace == "Reviewing":
            filtered = filtered.loc[
                filtered["human_review_status"] == "reviewing"
            ]
        elif workspace == "Applied":
            filtered = filtered.loc[
                filtered["human_review_status"] == "applied"
            ]
        elif workspace == "Skipped":
            filtered = filtered.loc[
                filtered["human_review_status"] == "skipped"
            ]

        qf = st.session_state.quick_filter

        if qf == "Rich intelligence":
            filtered = filtered.loc[filtered["_rich"]]
        elif qf == "Ready to review":
            filtered = filtered.loc[filtered["_ready"]]
        elif qf == "System warnings":
            filtered = filtered.loc[filtered["_warnings"]]
        elif qf == "High opportunity":
            filtered = filtered.loc[filtered["_high_opportunity"]]

        if search:
            mask = (
                filtered["title"]
                .astype(str)
                .str.lower()
                .str.contains(search, regex=False)
                |
                filtered["job_id"]
                .astype(str)
                .str.lower()
                .str.contains(search, regex=False)
            )
            filtered = filtered.loc[mask]

        sort_choice = st.session_state.sort_choice
        if sort_choice == "Oldest analyzed":
            filtered = filtered.sort_values(
                ["created_at", "id"],
                ascending=[True, True],
            )
        elif sort_choice == "Highest decision score":
            filtered = filtered.sort_values(
                ["_decision_score", "created_at", "id"],
                ascending=[False, False, False],
                na_position="last",
            )
        elif sort_choice == "Highest opportunity score":
            filtered = filtered.sort_values(
                ["_opportunity_score", "created_at", "id"],
                ascending=[False, False, False],
                na_position="last",
            )
        elif sort_choice == "Highest personal fit":
            filtered = filtered.sort_values(
                ["_fit_score", "created_at", "id"],
                ascending=[False, False, False],
                na_position="last",
            )
        elif sort_choice == "Lowest personal fit":
            filtered = filtered.sort_values(
                ["_fit_score", "created_at", "id"],
                ascending=[True, False, False],
                na_position="last",
            )
        else:
            filtered = filtered.sort_values(
                ["created_at", "id"],
                ascending=[False, False],
            )

        result_signature = f"{workspace}|{qf}|{search}|{sort_choice}"
        if st.session_state.get("_result_signature") != result_signature:
            st.session_state._result_signature = result_signature
            st.session_state.page = 1

        filtered = filtered.reset_index(drop=True)

        context_items = [workspace]
        if qf != "All jobs":
            context_items.append(qf)
        if search_value:
            context_items.append(f'Search: "{search_value}"')
        if len(context_items) > 1:
            context_html = "".join(
                f'<span class="context-chip">{escape(item)}</span>'
                for item in context_items
            )
            st.markdown(
                f'<div class="context-row">{context_html}</div>',
                unsafe_allow_html=True,
            )

        if compact_demo_inbox:
            page_size = len(filtered) or 1
        else:
            controls_left, controls_right = st.columns([1.1, 4.9])
            with controls_left:
                selected_page_size = st.selectbox("Jobs per page", [4, 8, 12, 16, 20], index=[4, 8, 12, 16, 20].index(st.session_state.page_size), key="page_size_select_v52")
                if selected_page_size != st.session_state.page_size:
                    st.session_state.page_size = selected_page_size
                    st.session_state.page = 1
                    st.rerun()
            page_size = st.session_state.page_size
        total_pages = max(1, math.ceil(len(filtered) / page_size))
        st.session_state.page = min(st.session_state.page, total_pages)
        if not compact_demo_inbox:
            with controls_right:
                start_display = (st.session_state.page - 1) * page_size + 1 if len(filtered) else 0
                end_display = min(st.session_state.page * page_size, len(filtered))
                st.markdown(f'<div class="page-info">Showing {start_display}–{end_display} of {len(filtered)} matching jobs · Page {st.session_state.page} of {total_pages}</div>', unsafe_allow_html=True)

        start = (st.session_state.page - 1) * page_size
        rows = list(filtered.iloc[start:start + page_size].itertuples())

        if not rows:
            if qf != "All jobs" or search_value:
                empty_title = "No matching jobs"
                empty_body = "No jobs in this workspace match the current filter or search."
            else:
                empty_messages = {
                    "Job Inbox": ("Inbox clear", "No unreviewed jobs right now."),
                    "Approved": ("No approved jobs", "No approved jobs are waiting for application."),
                    "Reviewing": ("Nothing under review", "No jobs are currently under review."),
                    "Applied": ("No applications yet", "No applications have been recorded yet."),
                    "Skipped": ("No skipped jobs", "No jobs have been skipped."),
                }
                empty_title, empty_body = empty_messages[workspace]
            st.markdown(
                '<div class="empty-state">'
                f'<strong>◇ {escape(empty_title)}</strong>'
                f'{escape(empty_body)}'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            for i in range(0, len(rows), 2):
                cols = st.columns(2, gap="medium")
                pair = rows[i:i + 2]

                for j, row in enumerate(pair):
                    with cols[j]:
                        html, rich_card = make_card(
                            row,
                            st.session_state.selected_report_id,
                        )

                        st.markdown(html, unsafe_allow_html=True)

                        label = "Review job →" if rich_card else "Open report →"

                        if st.button(
                            label,
                            key=f"open_{int(row.id)}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_report_id = int(row.id)
                            st.session_state.review_mode = bool(rich_card)
                            st.rerun()

        if total_pages > 1:
            prev_col, middle_col, next_col = st.columns([1, 4, 1])

            with prev_col:
                if st.button(
                    "← Previous",
                    disabled=st.session_state.page <= 1,
                    use_container_width=True,
                ):
                    st.session_state.page -= 1
                    st.rerun()

            with next_col:
                if st.button(
                    "Next →",
                    disabled=st.session_state.page >= total_pages,
                    use_container_width=True,
                ):
                    st.session_state.page += 1
                    st.rerun()

    # -------------------------------------------------------------------------
    # Archive
    # -------------------------------------------------------------------------

    else:
        st.markdown(
            '<div class="eyebrow">Project-E · Deep archive</div>'
            '<h1 class="page-title">Report Archive</h1>'
            '<p class="page-sub">Every saved Stage 5 report version remains available here.</p>',
            unsafe_allow_html=True,
        )

        archive_page_size = 25
        try:
            archive_total = get_report_archive_count()
            archive_total_pages = max(1, math.ceil(archive_total / archive_page_size))
            st.session_state.archive_page = min(
                max(1, st.session_state.archive_page),
                archive_total_pages,
            )
            archive_reports = get_report_archive(
                page=st.session_state.archive_page,
                page_size=archive_page_size,
            )
        except Exception:
            archive_total = 0
            archive_total_pages = 1
            st.error("The report archive could not be loaded. Please retry.")

        st.caption(
            f"{archive_total} saved report version(s) · "
            f"Page {st.session_state.archive_page} of {archive_total_pages}"
        )

        for row in archive_reports.itertuples():
            with st.container(border=True):
                left, right = st.columns([5, 1])

                with left:
                    st.markdown(
                        f"**{safe(clean_title(row.title))}**  \n"
                        f"Job {safe(row.job_id)} · "
                        f"Report #{row.id} · "
                        f"Version {row.version_number}"
                    )

                with right:
                    if st.button(
                        "Open report",
                        key=f"archive_{int(row.id)}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_report_id = int(row.id)
                        st.rerun()

        if archive_total_pages > 1:
            archive_prev, _, archive_next = st.columns([1, 4, 1])
            with archive_prev:
                if st.button(
                    "← Previous",
                    key="archive_previous",
                    disabled=st.session_state.archive_page <= 1,
                    use_container_width=True,
                ):
                    st.session_state.archive_page -= 1
                    st.session_state.selected_report_id = None
                    st.rerun()
            with archive_next:
                if st.button(
                    "Next →",
                    key="archive_next",
                    disabled=st.session_state.archive_page >= archive_total_pages,
                    use_container_width=True,
                ):
                    st.session_state.archive_page += 1
                    st.session_state.selected_report_id = None
                    st.rerun()

    # -------------------------------------------------------------------------
    # Full report
    # -------------------------------------------------------------------------

    selected_id = st.session_state.selected_report_id

    if selected_id is not None and not st.session_state.review_mode:
        st.divider()

        report_source = archive_reports if workspace == "Report Archive" else reports
        matches = report_source.loc[report_source["id"] == selected_id]

        title = (
            clean_title(matches.iloc[0]["title"])
            if not matches.empty
            else "Client Intelligence Report"
        )

        head_left, head_right = st.columns([5, 1])

        with head_left:
            st.markdown(
                f'<div class="section-kicker">Full Stage 5 report</div>'
                f'<h2 class="section-title">{safe(title)}</h2>'
                f'<p class="section-desc">Complete validated Client Intelligence Report.</p>',
                unsafe_allow_html=True,
            )

        with head_right:
            if st.button("Close report", use_container_width=True):
                st.session_state.selected_report_id = None
                st.rerun()

        selected_report_data = {}

        if not matches.empty:
            selected_report_data = as_dict(
                matches.iloc[0].get("report_json")
            )

        if selected_report_data:
            sections = [
                ("Executive Summary", selected_report_data.get("executive_summary")),
                ("Job Summary", selected_report_data.get("job_summary")),
                ("Opportunity Assessment", selected_report_data.get("opportunity_assessment")),
                ("Personal Fit", selected_report_data.get("personal_fit")),
                ("Recommendation", selected_report_data.get("recommendation")),
                ("Proposal Strategy", selected_report_data.get("proposal_strategy")),
                ("Generated Proposal", selected_report_data.get("generated_proposal")),
                ("Proposal Metadata", selected_report_data.get("proposal_metadata")),
                ("Strategy Execution", selected_report_data.get("strategy_execution")),
                ("Validation", selected_report_data.get("validation")),
                ("Report Warnings", selected_report_data.get("report_warnings")),
            ]

            for section_title, section_data in sections:
                if section_data in (None, {}, [], ""):
                    continue

                with st.expander(section_title, expanded=False):
                    st.markdown(
                        '<div class="report-section-note">'
                        'Structured Project-E report data'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    if section_title == "Generated Proposal":
                        render_proposal_section(section_data)
                    else:
                        render_report_value(section_data)

        html_load_failed = False
        try:
            html_report = get_report_html(selected_id)
        except Exception:
            html_report = ""
            html_load_failed = True
            st.error("The saved HTML report could not be loaded. Please retry.")

        if html_report:
            with st.expander("Full HTML Report", expanded=False):
                st.html(html_report)
        elif not html_load_failed:
            st.error("No saved HTML found for this report.")

except Exception:
    st.error("The dashboard encountered an error.")
    st.info("No data was changed. Check the server logs and retry.")

from __future__ import annotations
import html
import streamlit as st

def page_header(title, subtitle="", eyebrow="AI QUANT TERMINAL", right=""):
    st.markdown(
        f'<div class="q-header"><div><div class="q-eyebrow">{html.escape(eyebrow)}</div>'
        f'<div class="q-title">{html.escape(title)}</div><div class="q-sub">{html.escape(subtitle)}</div>'
        f'</div><div>{right}</div></div>',
        unsafe_allow_html=True,
    )

def status_strip(items):
    pills = []
    for label, state in items:
        state = state if state in {"ok","warn","bad","accent"} else ""
        pills.append(f'<span class="q-pill {state}">{html.escape(label)}</span>')
    st.markdown(f'<div class="q-status">{"".join(pills)}</div>', unsafe_allow_html=True)

def section_header(title, subtitle=""):
    st.markdown(
        f'<div class="q-section"><strong>{html.escape(title)}</strong>'
        f'<span>{html.escape(subtitle)}</span></div>',
        unsafe_allow_html=True,
    )

def metric_card(label, value, foot="", tone=""):
    tone = tone if tone in {"pos","neg","warn","accent"} else ""
    st.markdown(
        f'<div class="q-card"><div class="q-label">{html.escape(label)}</div>'
        f'<div class="q-value {tone}">{html.escape(str(value))}</div>'
        f'<div class="q-foot">{html.escape(foot)}</div></div>',
        unsafe_allow_html=True,
    )

# utils/header.py
import json
import streamlit as st
from streamlit.components.v1 import html

# ↓ Adjust this number to move the title DOWN inside the header bar
TOP_OFFSET_PX = 0   # e.g., 0, 6, 8, 10, 12...

def inject_top_header(title: str):
    """
    Injects the page title into Streamlit's real top header (not the content area).
    - Title stays on one line (nowrap).
    - Streamlit toolbar (File change | Rerun | Always rerun) is hidden.
    - Title can be vertically nudged down via TOP_OFFSET_PX.
    Call once per page after your left pane is rendered.
    """

    # Pure CSS (no JS here). Not an f-string -> no brace escaping needed.
    st.markdown(
        """
        <style>
          /* Make the Streamlit header a clean bar */
          header[data-testid="stHeader"] {
            display: flex !important;
            align-items: center !important;     /* center vertically; we'll nudge title with padding-top */
            justify-content: flex-start !important;
            height: 100px !important;
            background: #ffffff !important;
            border-bottom: none !important;     /* no line */
            padding: 0 0 0 30px !important;     /* small left padding */
            box-sizing: border-box !important;
          }

          /* Hide Streamlit's default right-side toolbar */
          header[data-testid="stHeader"] [data-testid="stToolbar"] {
            display: none !important;
          }

          /* Remove default content top gap so content starts right under the header */
          section.main > div.block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
          }

          /* Our injected title node */
          #dsv-top-title {
            font-size: 40px;
            font-weight: 800;
            color: #002664;         /* DSV navy */
            line-height: 1.5; /* ↑ give more vertical space */
            margin: 0;
            white-space: nowrap;    /* keep in one line */
            overflow: hidden;
            text-overflow: ellipsis;
          }

          @media (max-width: 900px) {
            #dsv-top-title { font-size: 60px; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # JS must run via components.html so we can inject into the real header.
    # We set padding-top on the title to move it down by TOP_OFFSET_PX.
    js = f"""
    <script>
      (function() {{
        try {{
          const header = window.parent.document.querySelector('header[data-testid="stHeader"]');
          if (!header) return;

          let titleEl = header.querySelector('#dsv-top-title');
          if (!titleEl) {{
            titleEl = document.createElement('div');
            titleEl.id = 'dsv-top-title';
            header.appendChild(titleEl);
          }}
          titleEl.textContent = {json.dumps(title)};
          titleEl.style.paddingTop = '{TOP_OFFSET_PX}px';   // ↓ move title down here
        }} catch (e) {{
          console.error('Header inject error:', e);
        }}
      }})();
    </script>
    """

    html(js, height=0)

import streamlit as st
import requests
import json
import pandas as pd
from pypdf import PdfReader
import io

# ── CONFIG ──────────────────────────────────────────
BACKEND_URL = "http://127.0.0.1:8000"
APP_TITLE = "QA Agent — Testing Dashboard"
APP_VERSION = "v0.1.0 (Internal)"
# ────────────────────────────────────────────────────

st.set_page_config(layout="wide", page_title=APP_TITLE, page_icon="🧪")

# --- INITIALIZE SESSION STATE ---
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None
if "requirements" not in st.session_state:
    st.session_state["requirements"] = []
if "test_cases" not in st.session_state:
    st.session_state["test_cases"] = []
if "brd_text" not in st.session_state:
    st.session_state["brd_text"] = ""
if "frd_text" not in st.session_state:
    st.session_state["frd_text"] = ""
if "github_repo_url" not in st.session_state:
    st.session_state["github_repo_url"] = ""
if "etl_files" not in st.session_state:
    st.session_state["etl_files"] = []
if "radio_page" not in st.session_state:
    st.session_state["radio_page"] = "🏠 Home / Overview"

# --- HELPER FUNCTIONS ---
def extract_text_from_pdf(file_obj):
    reader = PdfReader(file_obj)
    text = ""
    for page_num in range(len(reader.pages)):
        text += reader.pages[page_num].extract_text() + "\\n"
    return text

# --- SIDEBAR NAV ---
with st.sidebar:
    st.title(APP_TITLE)
    page = st.radio(
        "Navigation",
        [
            "🏠 Home / Overview",
            "📄 Input & Analyze",
            "🧪 Test Cases Viewer",
            "▶️ Test Runner (Coming Soon)",
            "🐛 Bug Reports (Coming Soon)",
            "📊 Metrics Dashboard (Coming Soon)"
        ],
        key="radio_page"
    )
    
    st.markdown("---")
    st.caption(APP_VERSION)
    st.caption("QA Agent Internal Testing UI — Not for production use")

# --- PAGE 1: HOME / OVERVIEW ---
if page == "🏠 Home / Overview":
    st.header("🏠 Home / Overview")
    
    st.info("Welcome to the QA Agent Testing Dashboard. This UI allows internal teams to trigger the pipeline, feed inputs to the agents, and observe the outputs while the production system is being built.")
    
    st.markdown(f"**Backend URL:** `{BACKEND_URL}`")
    
    if st.button("Test Backend Connection"):
        try:
            res = requests.get(f"{BACKEND_URL}/")
            if res.status_code == 200:
                st.success("Backend is reachable!")
            else:
                st.error(f"Backend returned status {res.status_code}")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
            
    st.divider()
    
    st.subheader("Pipeline Stage Readiness")
    status_markdown = """
| Stage | Status |
| :--- | :--- |
| Requirement Analyzer | ✅ Ready |
| Test Case Generator | ✅ Ready |
| Feature Classifier | ✅ Ready |
| Test Executor | 🔧 In Progress |
| Bug Reporter | ⏳ Coming Soon |
| JIRA Integration | ⏳ Coming Soon |
| PR Analyzer | ⏳ Coming Soon |
| QA Metrics | ⏳ Coming Soon |
| Slack Notifier | ⏳ Coming Soon |
"""
    st.markdown(status_markdown)
    st.caption("QA Agent Internal Testing UI — Not for production use")

# --- PAGE 2: INPUT & ANALYZE ---
elif page == "📄 Input & Analyze":
    st.header("📄 Input & Analyze")
    
    # ── Section 1 — BRD + FRD Documents ─────────────────────────────────────────
    st.subheader("1. BRD + FRD Documents")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 BRD — Business Requirements Document")
        brd_upload = st.file_uploader("Upload BRD", type=["txt", "pdf"], key="brd_file")
        st.caption("— or paste text below —")
        brd_text = st.text_area("BRD Text", height=200, key="brd_text_input",
            placeholder="Paste your Business Requirements Document here...")
            
        final_brd_text = brd_text
        if brd_upload:
            if brd_upload.name.endswith(".pdf"):
                final_brd_text = extract_text_from_pdf(brd_upload)
            else:
                final_brd_text = brd_upload.getvalue().decode("utf-8")
                
    with col2:
        st.subheader("📄 FRD — Functional Requirements Document")
        frd_upload = st.file_uploader("Upload FRD", type=["txt", "pdf"], key="frd_file")
        st.caption("— or paste text below —")
        frd_text = st.text_area("FRD Text", height=200, key="frd_text_input",
            placeholder="Paste your Functional Requirements Document here...")
            
        final_frd_text = frd_text
        if frd_upload:
            if frd_upload.name.endswith(".pdf"):
                final_frd_text = extract_text_from_pdf(frd_upload)
            else:
                final_frd_text = frd_upload.getvalue().decode("utf-8")
                
    st.divider()

    # ── Section 2 — Project Type Selector ─────────────────────────────────────────
    st.subheader("⚙️ What are you testing?")
    project_type = st.radio(
        "Select project type",
        options=["API / UI", "ETL Pipeline", "Both"],
        horizontal=True,
        key="project_type",
        label_visibility="collapsed"
    )
    
    st.divider()

    # ── Section 3a — GitHub Repo ─────────────────────────────────────────
    github_url = ""
    if project_type in ["API / UI", "Both"]:
        st.subheader("🔗 GitHub Repository")
        github_url = st.text_input(
            "GitHub Repo URL",
            placeholder="https://github.com/org/repo",
            key="github_url"
        )
        st.caption("Used by the PR Analyzer agent to detect missing tests in pull requests.")
        st.divider()

    # ── Section 3b — Databricks + ETL Inputs ─────────────────────────────────────────
    databricks_host = ""
    databricks_token = ""
    if project_type in ["ETL Pipeline", "Both"]:
        st.subheader("🔷 Databricks Connection")
        
        db_col1, db_col2 = st.columns(2)
        with db_col1:
            databricks_host = st.text_input(
                "Databricks Host URL",
                placeholder="https://your-workspace.azuredatabricks.net",
                key="db_host"
            )
            databricks_http_path = st.text_input(
                "HTTP Path",
                placeholder="/sql/1.0/warehouses/abc123",
                key="db_http_path"
            )
            databricks_catalog = st.text_input(
                "Catalog Name",
                placeholder="main",
                key="db_catalog"
            )
        with db_col2:
            databricks_token = st.text_input(
                "Access Token (PAT)",
                type="password",
                placeholder="dapi...",
                key="db_token"
            )
            databricks_schema = st.text_input(
                "Schema / Database",
                placeholder="silver",
                key="db_schema"
            )
            databricks_job_id = st.text_input(
                "Databricks Job ID (optional)",
                placeholder="12345",
                key="db_job_id"
            )
            
        if st.button("🔌 Test Databricks Connection", key="test_db_conn"):
            with st.spinner("Connecting..."):
                try:
                    from databricks import sql
                    conn = sql.connect(
                        server_hostname=databricks_host,
                        http_path=databricks_http_path,
                        access_token=databricks_token
                    )
                    conn.close()
                    st.success("✅ Connected to Databricks successfully")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")

        st.markdown("#### 📐 Schema Definitions")
        schema_col1, schema_col2, schema_col3 = st.columns(3)
        with schema_col1:
            bronze_schema = st.file_uploader("Bronze Schema", type=["json", "yaml"], key="bronze_schema")
        with schema_col2:
            silver_schema = st.file_uploader("Silver Schema", type=["json", "yaml"], key="silver_schema")
        with schema_col3:
            gold_schema   = st.file_uploader("Gold Schema",   type=["json", "yaml"], key="gold_schema")

        st.markdown("#### 📂 Sample Data")
        data_col1, data_col2, data_col3 = st.columns(3)
        with data_col1:
            bronze_data = st.file_uploader("Bronze Sample (.csv / .parquet)", type=["csv", "parquet"], key="bronze_data")
        with data_col2:
            silver_expected = st.file_uploader("Expected Silver Output (.csv)", type=["csv"], key="silver_expected")
        with data_col3:
            gold_expected   = st.file_uploader("Expected Gold Output (.csv)",   type=["csv"], key="gold_expected")

        st.markdown("#### 📓 Notebook Paths (optional)")
        nb_col1, nb_col2, nb_col3 = st.columns(3)
        with nb_col1:
            bronze_nb = st.text_input("Bronze Notebook", placeholder="/Repos/notebooks/bronze_ingest",  key="bronze_nb")
        with nb_col2:
            silver_nb = st.text_input("Silver Notebook", placeholder="/Repos/notebooks/silver_transform", key="silver_nb")
        with nb_col3:
            gold_nb   = st.text_input("Gold Notebook",   placeholder="/Repos/notebooks/gold_aggregate",  key="gold_nb")

        st.divider()

    # ── Section 4 — Analyze Button ─────────────────────────────────────────
    st.subheader("🔍 Run Analysis")
    
    checklist_items = []
    if final_brd_text:
        checklist_items.append("✅ BRD provided")
    else:
        checklist_items.append("❌ BRD missing — required")

    if final_frd_text:
        checklist_items.append("✅ FRD provided")
    else:
        checklist_items.append("⚠️ FRD not provided — optional but recommended")

    if project_type in ["API / UI", "Both"]:
        if github_url:
            checklist_items.append("✅ GitHub URL provided")
        else:
            checklist_items.append("⚠️ GitHub URL not provided — PR analysis will be skipped")

    if project_type in ["ETL Pipeline", "Both"]:
        if databricks_host and databricks_token:
            checklist_items.append("✅ Databricks credentials provided")
        else:
            checklist_items.append("❌ Databricks credentials missing")

    for item in checklist_items:
        st.caption(item)

    # Disable button if BRD is missing
    brd_ready = bool(final_brd_text.strip())
    analyze_clicked = st.button(
        "🔍 Analyze Requirements",
        type="primary",
        disabled=not brd_ready,
        use_container_width=True
    )

    # ── Section 5 — Results ─────────────────────────────────────────
    if analyze_clicked and brd_ready:
        st.divider()
        st.subheader("5. Results")

        # ── Log panel setup ──────────────────────────────────────
        st.markdown("### 🖥️ Execution Log")
        log_container = st.container(border=True)
        log_placeholder = log_container.empty()
        log_lines = []

        def render_logs(lines):
            """Render log lines as styled monospace text."""
            colored = []
            for line in lines:
                if line.startswith("✅") or "done" in line.lower() or "complete" in line.lower():
                    colored.append(f"🟢 {line}")
                elif line.startswith("❌") or "failed" in line.lower() or "error" in line.lower():
                    colored.append(f"🔴 {line}")
                elif line.startswith("⚠️"):
                    colored.append(f"🟡 {line}")
                elif line.startswith("   →"):
                    colored.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{line}")
                elif "─" * 10 in line:
                    colored.append("─" * 50)
                else:
                    colored.append(line)
            log_text = "\\n".join(colored)
            log_placeholder.markdown(
                f'<div style="font-family: monospace; font-size: 13px; '
                f'line-height: 1.8; white-space: pre-wrap;">{log_text}</div>',
                unsafe_allow_html=True
            )

        # ── Progress bar ─────────────────────────────────────────
        progress_bar = st.progress(0, text="Starting pipeline...")
        STEPS = [
            (10,  "Validating inputs..."),
            (30,  "Planner Agent — extracting requirements..."),
            (55,  "Feature Classifier — tagging test types..."),
            (80,  "Test Case Generator — generating test cases..."),
            (95,  "Building final response..."),
            (100, "Complete ✅"),
        ]
        step_index = 0

        # ── Stream from backend ───────────────────────────────────
        payload = {
            "brd_text": final_brd_text,
            "frd_text": final_frd_text,
            "github_repo_url": github_url if project_type in ["API / UI", "Both"] else ""
        }

        final_result = None

        try:
            with requests.post(
                f"{BACKEND_URL}/requirements/analyze/stream",
                json=payload,
                stream=True,
                timeout=600
            ) as response:
                response.raise_for_status()

                for raw_line in response.iter_lines(chunk_size=None, decode_unicode=True):
                    if not raw_line:
                        continue

                    # iter_lines(decode_unicode=True) already strips the response as str if possible
                    line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8")
                    if not line.startswith("data:"):
                        continue

                    try:
                        event = json.loads(line[5:].strip())
                    except Exception as e:
                        st.error(f"❌ Failed to parse SSE event: {e}. Payload (first 100 chars): {line[:100]}")
                        continue

                    # Check if this is the final RESULT event
                    if event.get("type") == "RESULT":
                        final_result = event.get("data")
                        progress_bar.progress(100, text="Complete ✅")
                        break

                    if event.get("type") == "ERROR":
                        st.error(f"❌ {event.get('message')}")
                        break

                    # It's a log line — append and re-render
                    message = event.get("message", "")
                    level   = event.get("level", "INFO")

                    log_lines.append(message)
                    render_logs(log_lines)

                    # Advance progress bar based on keywords in the message
                    if "Validating" in message and step_index == 0:
                        progress_bar.progress(STEPS[0][0], text=STEPS[0][1])
                        step_index = 1
                    elif "Planner Agent starting" in message and step_index <= 1:
                        progress_bar.progress(STEPS[1][0], text=STEPS[1][1])
                        step_index = 2
                    elif "Feature Classifier starting" in message and step_index <= 2:
                        progress_bar.progress(STEPS[2][0], text=STEPS[2][1])
                        step_index = 3
                    elif "Test Case" in message and step_index <= 3:
                        progress_bar.progress(STEPS[3][0], text=STEPS[3][1])
                        step_index = 4
                    elif "Building final response" in message and step_index <= 4:
                        progress_bar.progress(STEPS[4][0], text=STEPS[4][1])
                        step_index = 5

        except requests.exceptions.Timeout:
            st.error("❌ Request timed out after 5 minutes.")
            st.stop()
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot reach backend at {BACKEND_URL}. Is the FastAPI server running?")
            st.stop()
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            st.stop()

        # ── Store result and show summary ─────────────────────────
        if final_result:
            st.session_state["analysis_result"]   = final_result
            st.session_state["requirements"]      = final_result.get("requirements", [])
            st.session_state["test_cases"]        = final_result.get("test_cases", [])
            st.session_state["classifications"]   = final_result.get("classifications", [])


    if "analysis_result" in st.session_state and st.session_state["analysis_result"] is not None:
        result = st.session_state["analysis_result"]
        reqs = st.session_state["requirements"]
        tcs  = st.session_state["test_cases"]

        st.divider()

        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Requirements",  len(reqs))
        m2.metric("Test Cases",    len(tcs))
        m3.metric("Positive",      len([t for t in tcs if t.get("type") == "positive"]))
        m4.metric("Negative + Edge", len([t for t in tcs if t.get("type") in ["negative", "edge"]]))

        st.success(f"✅ Analysis complete — {len(reqs)} requirements, {len(tcs)} test cases generated")

        # Requirements table
        with st.expander("📋 Requirements", expanded=True):
            req_rows = []
            for r in reqs:
                tc_count = len([t for t in tcs if t.get("req_id") == r.get("id")])
                classification = next(
                    (c for c in result.get("classifications", []) if c["req_id"] == r.get("id")),
                    {}
                )
                feature_types = ", ".join(classification.get("feature_types", []))
                r_desc = r.get("description", "")
                req_rows.append({
                    "ID": r.get("id", ""),
                    "Description": r_desc[:90] + "..." if len(r_desc) > 90 else r_desc,
                    "Feature Types": feature_types,
                    "Acceptance Criteria": len(r.get("acceptance_criteria", [])),
                    "Test Cases": tc_count
                })
            st.dataframe(pd.DataFrame(req_rows), use_container_width=True, hide_index=True)

        with st.expander("🏷️ Feature Classifications", expanded=False):
            for c in result.get("classifications", []):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**{c['req_id']}**")
                    type_colors = {"ui": "🟣", "api": "🔵", "etl": "🟤", "performance": "🟡", "security": "🔴"}
                    for ft in c.get("feature_types", []):
                        st.markdown(f"{type_colors.get(ft, '⚪')} `{ft}`")
                with col2:
                    st.caption(c.get("reasoning", ""))
                st.divider()

        # Raw JSON
        with st.expander("🔩 Raw JSON Response"):
            st.json(result)

        # Download button
        st.download_button(
            label="📥 Download Full Analysis as JSON",
            data=json.dumps(result, indent=2),
            file_name="qa_analysis.json",
            mime="application/json"
        )

        st.info("👉 Go to **Test Cases Viewer** in the sidebar to browse and filter all generated test cases.")

    st.caption("QA Agent Internal Testing UI — Not for production use")

# --- PAGE 3: TEST CASES VIEWER ---
elif page == "🧪 Test Cases Viewer":
    st.header("🧪 Test Cases Viewer")
    
    if not st.session_state["analysis_result"]:
        st.warning("No analysis run yet. Go to Input & Analyze first.")
    else:
        reqs = st.session_state["requirements"]
        tcs = st.session_state["test_cases"]
        
        req_ids = ["All"] + list(set(tc.get("req_id", "") for tc in tcs))
        
        col1, col2 = st.columns(2)
        with col1:
            selected_req = st.selectbox("Filter by Requirement ID", req_ids)
        with col2:
            selected_types = st.multiselect("Filter by Type", ["positive", "negative", "edge"], default=["positive", "negative", "edge"])
            
        filtered_tcs = tcs
        if selected_req != "All":
            filtered_tcs = [tc for tc in filtered_tcs if tc.get("req_id") == selected_req]
        if selected_types:
            filtered_tcs = [tc for tc in filtered_tcs if tc.get("type") in selected_types]
            
        st.divider()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", len(filtered_tcs))
        m2.metric("Positive", len([tc for tc in filtered_tcs if tc.get("type") == "positive"]))
        m3.metric("Negative", len([tc for tc in filtered_tcs if tc.get("type") == "negative"]))
        m4.metric("Edge", len([tc for tc in filtered_tcs if tc.get("type") == "edge"]))
        
        st.divider()
        
        classifications = st.session_state.get("analysis_result", {}).get("classifications", [])
        type_map = {c["req_id"]: c.get("feature_types", []) for c in classifications}
        
        type_badge = {"positive": "🟢 positive", "negative": "🔴 negative", "edge": "🟠 edge"}
        
        for tc in filtered_tcs:
            tc_type = tc.get("type", "unknown").lower()
            short_desc = tc.get("description", "")[:60] + "..." if len(tc.get("description", "")) > 60 else tc.get("description", "")
            
            feat_types = type_map.get(tc.get("req_id"), [])
            feat_label = " ".join([f"[{ft}]" for ft in feat_types])
            
            label = f"{type_badge.get(tc_type, tc_type)}  |  {tc.get('id', '')}  |  {short_desc}  |  {tc.get('req_id', '')}  {feat_label}"
            
            with st.expander(label, expanded=False):
                col_left, col_right = st.columns([3, 2])
                
                with col_left:
                    st.markdown("**Description**")
                    st.write(tc.get("description", ""))
                    st.markdown("**Steps**")
                    for i, step in enumerate(tc.get("steps", []), 1):
                        st.markdown(f"{i}. {step}")
                        
                with col_right:
                    st.markdown("**Expected Result**")
                    st.info(tc.get("expected_result", "—"))
                    
                    st.markdown("**Metadata**")
                    st.markdown(f"- **ID:** `{tc.get('id', '')}`")
                    st.markdown(f"- **Requirement:** `{tc.get('req_id', '')}`")
                    st.markdown(f"- **Type:** `{tc.get('type', '')}`")
                    
                    if feat_types:
                        st.markdown("**Feature Types**")
                        cols = st.columns(len(feat_types))
                        feature_colors = {
                            "ui":          "🟣",
                            "api":         "🔵",
                            "etl":         "🟤",
                            "performance": "🟡",
                            "security":    "🔴",
                        }
                        for i, ft in enumerate(feat_types):
                            cols[i].markdown(f"{feature_colors.get(ft, '⚪')} `{ft}`")
                
        st.divider()
        st.subheader("⚙️ Generate Pytest Scripts")

        target_url = st.text_input(
            "Target App Base URL",
            value="http://127.0.0.1:8001",
            help="The URL of the app the tests will run against"
        )

        if st.button("⚙️ Generate Pytest Scripts", type="primary", use_container_width=True):
            if "analysis_result" not in st.session_state:
                st.error("❌ Run analysis first on the Input & Analyze page")
            else:
                result = st.session_state["analysis_result"]

                log_box = st.empty()
                progress = st.progress(0, text="Starting script generation...")
                log_lines = []

                def add_log(msg):
                    log_lines.append(msg)
                    log_box.markdown(
                        '<div style="font-family:monospace;font-size:12px;'
                        'line-height:1.8;white-space:pre-wrap;">'
                        + "\n".join(log_lines) + "</div>",
                        unsafe_allow_html=True
                    )

                add_log("⚙️ Sending to Coder Agent...")
                progress.progress(10, text="Calling coder agent...")

                try:
                    response = requests.post(
                        f"{BACKEND_URL}/test-cases/generate-scripts",
                        json={
                            "requirements": result.get("requirements", []),
                            "test_cases": result.get("test_cases", []),
                            "classifications": result.get("classifications", []),
                            "target_base_url": target_url
                        },
                        timeout=300
                    )
                    response.raise_for_status()
                    gen_result = response.json()

                    progress.progress(100, text="Done ✅")
                    add_log(f"✅ Generated {gen_result['total_files']} test files")

                    for f in gen_result["files"]:
                        add_log(f"   → {f['filename']}  [{', '.join(f['frameworks_used'])}]")

                    add_log(f"📄 Manifest saved to: {gen_result['manifest_path']}")

                    st.session_state["generated_scripts"] = gen_result
                    st.success(f"✅ {gen_result['total_files']} test files written to generated_tests/")

                except Exception as e:
                    st.error(f"❌ Script generation failed: {str(e)}")

        st.divider()
        json_export = json.dumps(tcs, indent=2)
        st.download_button(
            label="📥 Export Test Cases",
            data=json_export,
            file_name="test_cases.json",
            mime="application/json"
        )
        
    st.caption("QA Agent Internal Testing UI — Not for production use")

# --- PAGE 4: TEST RUNNER ---
elif page == "▶️ Test Runner (Coming Soon)":
    st.header("▶️ Test Runner (Coming Soon)")
    st.info("🔧 Test Executor agent is currently being built by the execution team.")
    
    st.subheader("Preview")
    with st.container(border=True):
        st.multiselect("Select Test Cases to Run", ["TC-REQ-101-01", "TC-REQ-102-01"], disabled=True)
        st.text_input("Target URL", value="https://staging.example.com", disabled=True)
        st.button("▶ Run Selected Tests", disabled=True)
        
        st.markdown("**Execution Logs:**")
        st.code("> Waiting for test execution to start...", language="text")
        
    st.caption("QA Agent Internal Testing UI — Not for production use")

# --- PAGE 5: BUG REPORTS ---
elif page == "🐛 Bug Reports (Coming Soon)":
    st.header("🐛 Bug Reports (Coming Soon)")
    st.info("⏳ Bug Reporter agent coming soon. Will auto-create JIRA tickets for failed tests.")
    
    dummy_bugs = [
        {"ID": "BUG-001", "Test": "TC-REQ-102-02", "Severity": "High", "Status": "Open", "JIRA": "Pending"},
        {"ID": "BUG-002", "Test": "TC-REQ-103-03", "Severity": "Medium", "Status": "Open", "JIRA": "Pending"},
    ]
    st.dataframe(dummy_bugs, use_container_width=True)
    
    st.caption("QA Agent Internal Testing UI — Not for production use")

# --- PAGE 6: METRICS DASHBOARD ---
elif page == "📊 Metrics Dashboard (Coming Soon)":
    st.header("📊 Metrics Dashboard (Coming Soon)")
    st.info("📊 QA Metrics agent coming soon. Will show pass/fail rates and release decisions.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tests", "—", help="Available after test run")
    col2.metric("Pass Rate", "—")
    col3.metric("Open Bugs", "—")
    col4.metric("Coverage", "—")
    
    st.markdown("### Test Execution Trends")
    st.bar_chart({"Pass": [0, 0, 0], "Fail": [0, 0, 0]})
    
    st.caption("QA Agent Internal Testing UI — Not for production use")

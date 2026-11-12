import json
import streamlit as st
from repopilot.inspector import run_analysis

st.set_page_config(
    page_title="RepoPilot Advanced Analysis",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 RepoPilot V4")
st.caption("Advanced Code Quality · Security · Dependency Intelligence")

st.info(
    "This tool performs static checks on accessible public repository files. "
    "Findings are indicators for manual review, not proof of vulnerabilities."
)

with st.form("advanced_form"):
    url = st.text_input(
        "Public GitHub repository",
        placeholder="https://github.com/owner/repository"
    )
    submitted = st.form_submit_button(
        "Run Advanced Analysis",
        type="primary",
        use_container_width=True
    )

if submitted:
    if not url.strip():
        st.warning("Enter a repository URL.")
    else:
        try:
            with st.spinner("Downloading source files and running checks..."):
                st.session_state["v4_report"] = run_analysis(url)
        except Exception as error:
            st.error(f"Analysis failed: {error}")

if "v4_report" in st.session_state:
    report = st.session_state["v4_report"]

    st.divider()
    st.subheader(report["repository"])

    if report["tree_truncated"]:
        st.warning("GitHub truncated the repository file tree. Results may be incomplete.")

    summary = report["code_summary"]

    a, b, c, d = st.columns(4)
    a.metric("Python files scanned", summary["files"])
    b.metric("Source lines", summary["lines"])
    c.metric("Functions", summary["functions"])
    d.metric("Classes", summary["classes"])

    code_tab, security_tab, dependencies_tab, report_tab = st.tabs([
        "💻 Code Quality",
        "🛡️ Security Review",
        "📦 Dependencies",
        "📄 JSON Export"
    ])

    with code_tab:
        st.subheader("Code Quality Findings")
        st.write(f"Long lines: {summary['long_lines']}")
        st.write(f"Syntax errors: {summary['syntax_errors']}")

        if report["code_findings"]:
            st.dataframe(report["code_findings"], use_container_width=True)
        else:
            st.success("No findings from the current static checks.")

        st.caption(
            "This is a lightweight heuristic scan, not a full linter "
            "or formal code-quality assessment."
        )

    with security_tab:
        st.subheader("Potential Security Findings")

        if report["secret_findings"]:
            st.warning(
                "Potential secret-like strings found. Verify manually. "
                "Values are not displayed by this scanner."
            )
            st.dataframe(report["secret_findings"], use_container_width=True)
        else:
            st.success("No secret-like patterns detected in scanned files.")

        if report["code_findings"]:
            risky = [
                item for item in report["code_findings"]
                if item["severity"] == "Review"
            ]
            if risky:
                st.subheader("Risky coding patterns")
                st.dataframe(risky, use_container_width=True)

        st.caption(
            "Pattern matching can produce false positives and false negatives. "
            "A clean result does not establish that a repository is secure."
        )

    with dependencies_tab:
        st.subheader("Dependency Inventory and OSV Checks")

        if report["dependencies"]:
            st.dataframe(
                report["dependencies"],
                use_container_width=True
            )
        else:
            st.info(
                "No dependencies found in requirements.txt or "
                "requirements-dev.txt. pyproject.toml dependencies "
                "are not yet parsed."
            )

        st.caption(
            "OSV checks are performed for exact-pinned requirements. "
            "Other version formats are listed but not checked."
        )

    with report_tab:
        st.json(report)
        st.download_button(
            "Download V4 JSON Report",
            data=json.dumps(report, indent=2),
            file_name="repopilot-v4-report.json",
            mime="application/json"
        )

else:
    st.markdown("### V4 analysis modules")
    st.markdown(
        "- Python source inspection\n"
        "- Potential secret detection\n"
        "- Risky function pattern checks\n"
        "- Requirements inventory\n"
        "- OSV vulnerability lookups for pinned packages"
    )

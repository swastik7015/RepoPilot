import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

import streamlit as st

st.set_page_config(
    page_title="RepoPilot | GitHub Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    .hero {
        padding: 25px;
        border-radius: 15px;
        background: linear-gradient(120deg, #182848, #243b55);
        margin-bottom: 25px;
    }
    .hero h1 {color: white; margin: 0;}
    .hero p {color: #cbd5e1; margin-bottom: 0;}
    div[data-testid="stMetric"] {
        background: rgba(128,128,128,0.08);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.15);
    }
</style>
""", unsafe_allow_html=True)


def api_get(url):
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "RepoPilot-Dashboard",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    )

    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_repository(value):
    value = value.strip().rstrip("/")

    if value.endswith(".git"):
        value = value[:-4]

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)

    if parsed.hostname not in ("github.com", "www.github.com"):
        raise ValueError("Please enter a valid github.com repository URL.")

    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError("URL must include both owner and repository.")

    owner, repo = parts[0], parts[1]

    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        raise ValueError("Invalid GitHub username.")

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise ValueError("Invalid repository name.")

    return owner, repo


def check_path(owner, repo, path):
    url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/contents/{path}"
    )
    try:
        api_get(url)
        return True
    except HTTPError as error:
        if error.code == 404:
            return False
        raise


def analyze(owner, repo):
    base = f"https://api.github.com/repos/{owner}/{repo}"
    data = api_get(base)
    languages = api_get(base + "/languages")

    checks = [
        ("README.md", 20, check_path(owner, repo, "README.md")),
        ("LICENSE", 15, check_path(owner, repo, "LICENSE")),
        ("CONTRIBUTING.md", 10, check_path(owner, repo, "CONTRIBUTING.md")),
        ("Tests directory", 20, check_path(owner, repo, "tests")),
        ("GitHub Actions", 15, check_path(owner, repo, ".github/workflows")),
        ("Documentation", 10, check_path(owner, repo, "docs")),
        ("Project configuration", 10, check_path(owner, repo, "pyproject.toml")),
    ]

    score = sum(points for _, points, passed in checks if passed)

    return {
        "repository": data,
        "languages": languages,
        "checks": checks,
        "score": score
    }


# Sidebar
with st.sidebar:
    st.title("🚀 RepoPilot")
    st.caption("GitHub Repository Intelligence")
    st.divider()
    st.markdown("**Version:** 3.0.0")
    st.markdown("**Developer:** Swastik Sharma")
    st.markdown("[GitHub Repository](https://github.com/swastik7015/RepoPilot)")
    st.divider()
    st.caption("Analyze public GitHub repositories without an API key.")


# Header
st.markdown("""
<div class="hero">
    <h1>🚀 RepoPilot Dashboard</h1>
    <p>Understand your GitHub repositories. Analyze, inspect and improve.</p>
</div>
""", unsafe_allow_html=True)

st.subheader("Analyze a GitHub repository")

with st.form("repository_form"):
    repository_url = st.text_input(
        "GitHub repository URL",
        placeholder="https://github.com/owner/repository"
    )
    submitted = st.form_submit_button(
        "Analyze Repository",
        type="primary",
        use_container_width=True
    )

if submitted:
    if not repository_url.strip():
        st.warning("Enter a GitHub repository URL first.")
    else:
        try:
            owner, repo = parse_repository(repository_url)

            with st.spinner("Fetching repository information from GitHub..."):
                result = analyze(owner, repo)

            st.session_state["analysis"] = result
            st.session_state["analyzed_url"] = repository_url

        except HTTPError as error:
            if error.code == 404:
                st.error("Repository not found or is private.")
            elif error.code == 403:
                st.error("GitHub API rate limit reached. Try again later.")
            else:
                st.error(f"GitHub API returned HTTP {error.code}.")
        except (URLError, TimeoutError):
            st.error("Network connection failed. Please try again.")
        except (ValueError, KeyError, TypeError) as error:
            st.error(f"Could not analyze repository: {error}")
        except Exception as error:
            st.error(f"Unexpected error: {error}")


if "analysis" in st.session_state:
    result = st.session_state["analysis"]
    data = result["repository"]
    languages = result["languages"]
    score = result["score"]

    st.divider()

    st.markdown(f"## 📁 {data['full_name']}")

    if data.get("description"):
        st.write(data["description"])

    st.markdown(f"[Open repository on GitHub]({data['html_url']})")

    st.subheader("Repository Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⭐ Stars", f"{data['stargazers_count']:,}")
    c2.metric("🍴 Forks", f"{data['forks_count']:,}")
    c3.metric("👁 Watchers", f"{data['subscribers_count']:,}")
    c4.metric("🐛 Open Issues", f"{data['open_issues_count']:,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Health Score", f"{score}/100")
    c6.metric("Primary Language", data.get("language") or "Unknown")
    c6.metric if False else None
    c7.metric("License", (data.get("license") or {}).get("spdx_id") or "Unknown")
    c8.metric("Default Branch", data["default_branch"])

    st.divider()

    overview_tab, health_tab, language_tab, raw_tab = st.tabs([
        "📊 Overview",
        "🩺 Repository Health",
        "💻 Languages",
        "📄 JSON Report"
    ])

    with overview_tab:
        st.subheader("Repository Activity")

        left, right = st.columns(2)

        with left:
            st.write("**Created**")
            st.write(data["created_at"][:10])
            st.write("**Last Updated**")
            st.write(data["updated_at"][:10])

        with right:
            st.write("**Last Push**")
            st.write(data["pushed_at"][:10])
            st.write("**Repository Status**")
            st.write("Archived" if data["archived"] else "Active")

        st.write("**Topics**")
        topics = data.get("topics", [])
        if topics:
            st.write(" · ".join(topics))
        else:
            st.caption("No topics added.")

        st.write("**Project Information**")
        st.write(f"Owner: {data['owner']['login']}")
        st.write(f"Visibility: {data['visibility']}")
        st.write(f"Fork: {'Yes' if data['fork'] else 'No'}")

    with health_tab:
        st.subheader("Repository Structure Analysis")
        st.caption(
            "This score checks the presence of common project files. "
            "It is not a security or code-quality certification."
        )

        st.progress(score / 100)
        st.metric("Repository Structure Score", f"{score}/100")

        for name, points, passed in result["checks"]:
            col1, col2 = st.columns([4, 1])
            col1.write(name)
            col2.write(
                f"✅ {points}/{points}" if passed
                else f"❌ 0/{points}"
            )

        missing = [
            name for name, _, passed in result["checks"] if not passed
        ]

        if missing:
            st.warning("Suggested improvements: " + ", ".join(missing))
        else:
            st.success("All seven structural checks passed!")

    with language_tab:
        st.subheader("Programming Languages")

        if languages:
            st.bar_chart(languages)
            total = sum(languages.values())

            for language, size in sorted(
                languages.items(), key=lambda item: item[1], reverse=True
            ):
                percentage = size / total * 100
                st.write(f"**{language}** — {percentage:.1f}%")
        else:
            st.info("No language data available.")

    with raw_tab:
        st.subheader("Complete Analysis Data")

        report = {
            "repository": data,
            "languages": languages,
            "health_score": score,
            "checks": [
                {"name": name, "points": points, "passed": passed}
                for name, points, passed in result["checks"]
            ]
        }

        st.json(report)

        st.download_button(
            "⬇ Download JSON Report",
            data=json.dumps(report, indent=2),
            file_name=f"{data['name']}-repopilot-report.json",
            mime="application/json",
            use_container_width=True
        )

else:
    st.info("👆 Enter a public GitHub repository URL above to get started.")

    st.markdown("### What RepoPilot analyzes")
    a, b, c = st.columns(3)

    a.markdown("**📈 Repository Stats**")
    a.caption("Stars, forks, watchers and issues.")

    b.markdown("**🩺 Project Health**")
    b.caption("Documentation, tests, license and CI.")

    c.markdown("**💻 Code Analytics**")
    c.caption("Programming languages and JSON reports.")

    st.divider()
    st.caption("Built with Python and Streamlit · RepoPilot v3.0.0")

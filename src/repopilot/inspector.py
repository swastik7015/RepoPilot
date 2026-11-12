import ast
import base64
import json
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API = "https://api.github.com"
MAX_PYTHON_FILES = 20

SECRET_PATTERNS = {
    "Possible API key": r"(?i)(api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][^'\"]{12,}",
    "Possible access token": r"(?i)(access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][^'\"]{12,}",
    "Possible private key": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "Possible password": r"(?i)password\s*[:=]\s*['\"][^'\"]{4,}",
}

RISK_PATTERNS = {
    "eval() usage": r"\beval\s*\(",
    "exec() usage": r"\bexec\s*\(",
    "OS command execution": r"\bos\.system\s*\(",
    "Shell-enabled subprocess": r"subprocess\.[\w]+\([^)]*shell\s*=\s*True",
    "Unsafe pickle loading": r"pickle\.load\s*\(",
}


def request_json(url, method="GET", payload=None):
    body = None
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RepoPilot"
    }

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=body, headers=headers, method=method)

    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_repo(value):
    value = value.strip().rstrip("/")
    value = value.removesuffix(".git")

    match = re.search(
        r"(?:https?://github\.com/)?([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)",
        value
    )

    if not match:
        raise ValueError("Enter a valid GitHub owner/repository URL.")

    return match.group(1), match.group(2)


def get_source_files(owner, repo):
    info = request_json(f"{API}/repos/{owner}/{repo}")
    branch = info["default_branch"]

    tree = request_json(
        f"{API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    )

    files = [
        item["path"] for item in tree.get("tree", [])
        if item.get("type") == "blob"
    ]

    python_paths = [
        path for path in files
        if path.endswith(".py")
        and not any(part in path.split("/") for part in (
            ".venv", "venv", "site-packages", "__pycache__"
        ))
    ][:MAX_PYTHON_FILES]

    dependency_paths = [
        path for path in files
        if path in (
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml"
        )
    ]

    source = {}

    for path in python_paths + dependency_paths:
        try:
            result = request_json(
                f"{API}/repos/{owner}/{repo}/contents/{path}"
            )
            if result.get("encoding") == "base64":
                content = base64.b64decode(
                    result["content"]
                ).decode("utf-8", errors="replace")
                source[path] = content
        except (HTTPError, URLError, ValueError, KeyError):
            continue

    return info, source, files, tree.get("truncated", False)


def inspect_code(source):
    findings = []
    summary = {
        "files": 0,
        "lines": 0,
        "long_lines": 0,
        "functions": 0,
        "classes": 0,
        "syntax_errors": 0
    }

    for filename, content in source.items():
        if not filename.endswith(".py"):
            continue

        summary["files"] += 1
        lines = content.splitlines()
        summary["lines"] += len(lines)

        for number, line in enumerate(lines, 1):
            if len(line) > 120:
                summary["long_lines"] += 1
                findings.append({
                    "file": filename,
                    "line": number,
                    "severity": "Low",
                    "issue": "Line exceeds 120 characters"
                })

            for name, pattern in RISK_PATTERNS.items():
                if re.search(pattern, line):
                    findings.append({
                        "file": filename,
                        "line": number,
                        "severity": "Review",
                        "issue": name
                    })

        try:
            tree = ast.parse(content)
            summary["functions"] += sum(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                for node in ast.walk(tree)
            )
            summary["classes"] += sum(
                isinstance(node, ast.ClassDef) for node in ast.walk(tree)
            )
        except SyntaxError as error:
            summary["syntax_errors"] += 1
            findings.append({
                "file": filename,
                "line": error.lineno or 0,
                "severity": "Review",
                "issue": "Python syntax error"
            })

    return summary, findings


def inspect_secrets(source):
    findings = []

    for filename, content in source.items():
        if not filename.endswith((".py", ".txt", ".toml", ".yml", ".yaml")):
            continue

        for number, line in enumerate(content.splitlines(), 1):
            for name, pattern in SECRET_PATTERNS.items():
                if re.search(pattern, line):
                    findings.append({
                        "file": filename,
                        "line": number,
                        "issue": name,
                        "severity": "High"
                    })

    return findings


def parse_dependencies(source):
    dependencies = []

    for filename, content in source.items():
        if filename not in (
            "requirements.txt",
            "requirements-dev.txt"
        ):
            continue

        for line in content.splitlines():
            line = line.strip()

            if not line or line.startswith(("#", "-")):
                continue

            match = re.match(
                r"^([A-Za-z0-9_.-]+)\s*(==|>=|<=|~=|!=|>|<)?\s*([A-Za-z0-9_.+-]+)?",
                line
            )

            if match:
                dependencies.append({
                    "name": match.group(1),
                    "operator": match.group(2) or "",
                    "version": match.group(3) or "",
                    "source": filename
                })

    return dependencies


def check_vulnerabilities(dependencies):
    results = []

    for package in dependencies:
        if not package["version"] or package["operator"] != "==":
            results.append({
                **package,
                "status": "Not checked",
                "details": "A pinned version is required for this check."
            })
            continue

        payload = {
            "package": {
                "name": package["name"],
                "ecosystem": "PyPI"
            },
            "version": package["version"]
        }

        try:
            response = request_json(
                "https://api.osv.dev/v1/query",
                method="POST",
                payload=payload
            )
            vulnerabilities = response.get("vulns", [])

            results.append({
                **package,
                "status": "Vulnerable" if vulnerabilities else "No known match",
                "details": [
                    item.get("id", "Unknown")
                    for item in vulnerabilities
                ]
            })
        except Exception:
            results.append({
                **package,
                "status": "Check failed",
                "details": "OSV service was unavailable."
            })

    return results


def run_analysis(repository):
    owner, repo = parse_repo(repository)
    info, source, files, truncated = get_source_files(owner, repo)

    code_summary, code_findings = inspect_code(source)
    secret_findings = inspect_secrets(source)
    dependencies = parse_dependencies(source)
    vulnerability_results = check_vulnerabilities(dependencies)

    return {
        "repository": info["full_name"],
        "code_summary": code_summary,
        "code_findings": code_findings,
        "secret_findings": secret_findings,
        "dependencies": vulnerability_results,
        "scanned_files": len(source),
        "tree_truncated": truncated
    }

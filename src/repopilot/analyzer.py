from pathlib import Path

WEIGHTS = {
    "README.md": 20,
    "LICENSE": 15,
    "CONTRIBUTING.md": 10,
    "tests": 20,
    ".github/workflows": 15,
    "docs": 10,
    "pyproject.toml": 10,
}

def analyze_repository(path):
    root = Path(path).expanduser().resolve()

    if not root.exists() or not root.is_dir():
        raise ValueError(f"Directory does not exist: {root}")

    checks = []

    def add(name, points, passed, detail):
        checks.append({
            "name": name,
            "points": points,
            "passed": bool(passed),
            "earned": points if passed else 0,
            "detail": detail
        })

    readme = root / "README.md"
    license_file = root / "LICENSE"
    contributing = root / "CONTRIBUTING.md"
    tests = root / "tests"
    workflows = root / ".github" / "workflows"
    docs = root / "docs"
    config = root / "pyproject.toml"

    add("README", 20, readme.is_file(),
        "Project documentation found" if readme.is_file()
        else "Add a README.md describing your project")

    add("License", 15, license_file.is_file(),
        "License file found" if license_file.is_file()
        else "Add an open-source license")

    add("Contribution guide", 10, contributing.is_file(),
        "Contribution guide found" if contributing.is_file()
        else "Add CONTRIBUTING.md")

    test_files = (
        list(tests.rglob("test_*.py")) if tests.is_dir() else []
    )
    add("Tests", 20, bool(test_files),
        f"Found {len(test_files)} test file(s)" if test_files
        else "Add automated tests inside tests/")

    workflow_files = (
        list(workflows.glob("*.yml")) +
        list(workflows.glob("*.yaml"))
        if workflows.is_dir() else []
    )
    add("GitHub Actions", 15, bool(workflow_files),
        "CI workflow found" if workflow_files
        else "Add a GitHub Actions workflow")

    add("Documentation", 10,
        docs.is_dir() and any(docs.iterdir()),
        "Documentation folder contains files"
        if docs.is_dir() and any(docs.iterdir())
        else "Add useful documentation inside docs/")

    add("Project configuration", 10, config.is_file(),
        "pyproject.toml found" if config.is_file()
        else "Add project configuration")

    score = sum(item["earned"] for item in checks)

    if score >= 85:
        rating = "Excellent"
    elif score >= 65:
        rating = "Good"
    elif score >= 40:
        rating = "Needs improvement"
    else:
        rating = "Getting started"

    return {
        "repository": root.name,
        "path": str(root),
        "score": score,
        "maximum_score": 100,
        "rating": rating,
        "checks": checks,
        "suggestions": [
            item["detail"] for item in checks if not item["passed"]
        ]
    }

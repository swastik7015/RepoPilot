import argparse
import json
import sys
from pathlib import Path
from .analyzer import analyze_repository

def main():
    parser = argparse.ArgumentParser(
        prog="repopilot",
        description="Analyze the health of a software repository."
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Path to the repository to analyze"
    )
    parser.add_argument(
        "--json", dest="json_file",
        help="Save the report to a JSON file"
    )
    args = parser.parse_args()

    try:
        report = analyze_repository(args.path)
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print("\n================================")
    print("          REP O PILOT")
    print("================================")
    print(f"Repository : {report['repository']}")
    print(f"Health     : {report['score']}/100")
    print(f"Rating     : {report['rating']}")
    print("--------------------------------")

    for item in report["checks"]:
        status = "PASS" if item["passed"] else "TODO"
        print(f"[{status}] {item['name']}: "
              f"{item['earned']}/{item['points']}")
        print(f"       {item['detail']}")

    if report["suggestions"]:
        print("\nSuggestions:")
        for suggestion in report["suggestions"]:
            print(f" - {suggestion}")

    if args.json_file:
        output = Path(args.json_file)
        output.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8"
        )
        print(f"\nJSON report saved to: {output.resolve()}")

    print("\nAnalysis complete!")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

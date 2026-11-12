import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze_repository
from .github import analyze_github_repository

def main():
    parser = argparse.ArgumentParser(
        prog="repopilot",
        description="Analyze GitHub and local repository health."
    )

    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--github", help="Analyze owner/repository")
    parser.add_argument("--json", dest="json_file",
                        help="Save results as JSON")

    args = parser.parse_args()

    try:
        if args.github:
            report = analyze_github_repository(args.github)

            print("\n========== REP O PILOT ==========")
            print(f"Repository : {report['repository']}")
            print(f"URL        : {report['url']}")
            print(f"Language   : {report['language']}")
            print(f"Stars      : {report['stars']}")
            print(f"Forks      : {report['forks']}")
            print(f"Watchers   : {report['watchers']}")
            print(f"Open issues: {report['open_issues']}")
            print(f"License    : {report['license']}")
            print(f"Branch     : {report['default_branch']}")
            print(f"Last push  : {report['last_push']}")
            print(f"Archived   : {report['archived']}")
            print(f"Topics     : {', '.join(report['topics']) or 'None'}")
        else:
            report = analyze_repository(args.path)

            print("\n========== REP O PILOT ==========")
            print(f"Repository : {report['repository']}")
            print(f"Health     : {report['score']}/100")
            print(f"Rating     : {report['rating']}")

            for item in report["checks"]:
                status = "PASS" if item["passed"] else "TODO"
                print(
                    f"[{status}] {item['name']}: "
                    f"{item['earned']}/{item['points']}"
                )
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
            print(f"\nJSON report saved: {output.resolve()}")

        print("\nAnalysis complete!")

    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

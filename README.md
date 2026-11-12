# RepoPilot

A lightweight Python command-line tool that evaluates repository
readiness through documentation, licensing, testing, and CI checks.

## Features

- Repository health score out of 100.
- README and licence detection.
- Contribution guide detection.
- Automated test detection.
- GitHub Actions workflow detection.
- Documentation and project configuration checks.
- JSON report export.
- No external API keys or dependencies required.

## Installation

Python 3.10 or newer is required.

```bash
git clone https://github.com/swastik7015/RepoPilot.git
cd RepoPilot
python -m pip install -e .
```

## Usage

Analyze the current directory:

```bash
repopilot
```

Analyze another repository:

```bash
repopilot "C:/Users/YourName/Desktop/MyProject"
```

Export a JSON report:

```bash
repopilot . --json report.json
```

Alternatively, run without installing:

```bash
python -m repopilot.cli .
```

## Scoring

| Check | Points |
|---|---:|
| README | 20 |
| License | 15 |
| Contribution guide | 10 |
| Tests | 20 |
| GitHub Actions | 15 |
| Documentation | 10 |
| Project configuration | 10 |
| Total | 100 |

The score measures the presence of basic repository practices.
It is not a measure of security, software quality, popularity,
or compliance with any open-source program.

## Development

```bash
python -m unittest discover -s tests -v
```

## Limitations

RepoPilot currently performs local structural checks. It does not
verify repository popularity, downloads, external contributors,
security vulnerabilities, or actual project adoption.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License. See [LICENSE](LICENSE).

## GitHub Analysis

Analyze any public GitHub repository:

```bash
python -m repopilot.cli --github owner/repository
```

Example:

```bash
python -m repopilot.cli --github swastik7015/RepoPilot
```

Export live repository information:

```bash
python -m repopilot.cli --github owner/repository --json github-report.json
```

GitHub analysis uses the public GitHub REST API and requires no
authentication for public repositories. Unauthenticated API rate
limits apply.

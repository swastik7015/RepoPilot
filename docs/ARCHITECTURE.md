# Architecture

RepoPilot is organized into two main layers:

- `analyzer.py`: inspects a local repository and calculates its score.
- `cli.py`: parses command-line arguments, displays results, and exports JSON.

The analyzer returns a structured Python dictionary, allowing future
integrations with web dashboards or other developer tools.

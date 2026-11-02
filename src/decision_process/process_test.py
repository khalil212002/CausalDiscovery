"""Runs the decision process and prints the connection between each pair of variables.

From src/:
    python -m decision_process.process_test smoking "heart disease"
"""

import sys
from pathlib import Path

# Allow running this file directly (e.g. VS Code's Run button), not only with -m
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from decision_process.domain_search import domain_search
from decision_process.gemini_provider import GeminiProvider

DEFAULT_VARIABLES = ["smoking", "heart disease"]


def find_connections(variables: list[str]) -> list[str]:
    """One line per pair of variables, saying how they are connected."""
    connections = []
    for s in domain_search(variables, GeminiProvider()):
        arrow = f"{s.source} -> {s.target}" if s.source else f"{s.var_a} -- {s.var_b}"
        connections.append(f"{arrow}: {s.edge_type}")
    return connections


if __name__ == "__main__":
    variables = sys.argv[1:] or DEFAULT_VARIABLES
    for connection in find_connections(variables):
        print(connection)

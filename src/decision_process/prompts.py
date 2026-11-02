"""The prompt sent to the LLM for one pair of variables, and how its answer is read.

The LLM only reads each abstract and reports what that paper found. Deciding
the final edge from those findings (do they agree? on the direction?) is done
in code by domain_search, so the rules from the paper's flowchart are applied
the same way every time.
"""

import json
from dataclasses import dataclass
from enum import StrEnum

from decision_process.pubmed_client import Article


class PaperVerdict(StrEnum):
    A_CAUSES_B = "a_causes_b"
    B_CAUSES_A = "b_causes_a"
    UNCLEAR_DIRECTION = "unclear_direction"  # a link, but direction not clear
    NO_LINK = "no_link"  # studied the pair and found no effect
    NOT_RELEVANT = "not_relevant"  # mentions the variables but doesn't study the pair


@dataclass
class PaperFinding:
    """What the LLM says one paper found about the pair."""

    pmid: str
    verdict: PaperVerdict
    claim: str  # one-line summary of the paper's finding


@dataclass
class PairAnalysis:
    """The LLM's full answer for one pair."""

    findings: list[PaperFinding]
    summary: str  # a few sentences for the researcher


PROMPT_TEMPLATE = """\
You are helping a medical researcher build a causal diagram (DAG).
Decide what each meta-analysis below found about the causal relationship
between two variables.

Variable A: {var_a}
Variable B: {var_b}

For each paper, choose exactly one verdict:
- "a_causes_b": the paper finds that A affects B (A is the exposure or risk
  factor, B is the outcome).
- "b_causes_a": the paper finds that B affects A.
- "unclear_direction": the paper finds a link between A and B, but says the
  direction is uncertain or goes both ways.
- "no_link": the paper studies A and B and finds no significant effect.
- "not_relevant": the paper mentions A and B but does not study the
  relationship between them (e.g. a broad review where they appear separately).

Rules:
- Use only what the abstract says. Do not add outside knowledge.
- "claim" is one short sentence stating the paper's finding about A and B,
  including the effect size if the abstract gives one.
- "summary" is 2-3 sentences for the researcher on what the papers say
  overall, mentioning any disagreement between them.

Reply with JSON only, no other text, in exactly this format:
{{
  "papers": [
    {{"pmid": "<pmid>", "verdict": "<verdict>", "claim": "<one sentence>"}}
  ],
  "summary": "<2-3 sentences>"
}}

Papers:
{papers}
"""


def build_pair_prompt(var_a: str, var_b: str, articles: list[Article]) -> str:
    """The prompt asking the LLM to judge each article for this pair."""
    papers = "\n\n".join(
        f"PMID: {a.pmid}\nTitle: {a.title}\nAbstract:\n{a.abstract}" for a in articles
    )
    return PROMPT_TEMPLATE.format(var_a=var_a, var_b=var_b, papers=papers)


def parse_pair_response(text: str, articles: list[Article]) -> PairAnalysis:
    """Read the LLM's JSON answer.

    Papers the LLM skipped or gave an unknown verdict are treated as
    not relevant, and PMIDs we never sent are ignored. Raises ValueError if
    the answer is not JSON at all.
    """
    data = json.loads(_strip_code_fence(text))

    answered = {}
    for paper in data.get("papers", []):
        pmid = str(paper.get("pmid", ""))
        try:
            verdict = PaperVerdict(paper.get("verdict"))
        except ValueError:
            verdict = PaperVerdict.NOT_RELEVANT
        answered[pmid] = PaperFinding(pmid, verdict, str(paper.get("claim", "")))

    # One finding per article we sent, in the same order
    findings = [
        answered.get(a.pmid, PaperFinding(a.pmid, PaperVerdict.NOT_RELEVANT, ""))
        for a in articles
    ]
    return PairAnalysis(findings=findings, summary=str(data.get("summary", "")))


def _strip_code_fence(text: str) -> str:
    # LLMs often wrap JSON in ```json ... ``` even when asked not to
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text

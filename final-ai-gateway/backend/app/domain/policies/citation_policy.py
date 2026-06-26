"""
Citation policy — defines citation requirements for RAG answers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CitationPolicy:
    min_citations: int = 1
    require_citations: bool = True
    max_citations: int = 10
    min_relevance_score: float = 0.3

    def validate(self, citation_count: int, avg_relevance: float) -> tuple[bool, str]:
        if self.require_citations and citation_count < self.min_citations:
            return False, f"insufficient citations: {citation_count} < {self.min_citations}"
        if avg_relevance < self.min_relevance_score:
            return False, f"low citation relevance: {avg_relevance:.3f} < {self.min_relevance_score}"
        if citation_count > self.max_citations:
            return False, f"too many citations: {citation_count} > {self.max_citations}"
        return True, "ok"
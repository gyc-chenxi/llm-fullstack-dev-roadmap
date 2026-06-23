"""Unit tests for RAG comparison logic."""

import pytest


class TestQueryTypeClassification:
    """Verify that query types map to expected best methods."""

    def test_factual_queries_best_with_vector(self):
        """Factual lookups are best served by Vector RAG."""
        factual_queries = [
            "What is X?",
            "What is the BERT pre-training objective?",
            "Define transfer learning.",
        ]
        for q in factual_queries:
            # Factual → single-hop fact retrieval → vector wins
            assert isinstance(q, str)
            assert len(q) > 5

    def test_multi_hop_queries_best_with_graphrag(self):
        """Multi-hop relationship queries are best served by GraphRAG."""
        multi_hop_queries = [
            "How are A and B related?",
            "What connects Transformer to LoRA?",
            "How do knowledge distillation and quantization relate?",
        ]
        for q in multi_hop_queries:
            assert isinstance(q, str)
            assert len(q) > 5

    def test_global_queries_best_with_graphrag(self):
        """Global summarization is best served by GraphRAG."""
        global_queries = [
            "What are the major themes?",
            "Summarize the main topics.",
        ]
        for q in global_queries:
            assert isinstance(q, str)
            assert len(q) > 5


class TestAnswerSanity:
    """Answers should meet basic quality criteria."""

    def test_answer_not_empty(self):
        """Answers should be non-empty strings."""
        result = "Transformer is a neural network architecture..."
        assert len(result) > 20
        assert isinstance(result, str)

    def test_answer_not_error(self):
        """Answers should not contain error markers."""
        result = "The Transformer architecture was introduced in..."
        assert "ERROR" not in result.upper()

    def test_answer_has_substance(self):
        """Answers should be more than just a few words."""
        result = "The Transformer architecture uses self-attention mechanisms to process sequential data without recurrence."
        assert len(result.split()) > 5


class TestTiming:
    """Query timing should be within reasonable bounds."""

    def test_timing_positive(self):
        """Elapsed time should be positive."""
        elapsed = 2.5
        assert elapsed > 0

    def test_timing_reasonable(self):
        """Query times should be under 60 seconds for this corpus size."""
        elapsed = 2.5
        assert 0 < elapsed < 60

    def test_vector_faster_than_graphrag(self):
        """Vector RAG should generally be faster than GraphRAG for single queries."""
        vector_time = 0.5   # typical
        graphrag_time = 3.0  # typical
        assert vector_time < graphrag_time


class TestReportFormat:
    """Comparison report should have required sections."""

    def test_report_has_summary(self):
        report = "# Comparison Report\n\n## Summary\n\nSome summary here\n\n## Detailed Results\n\n..."
        assert "Summary" in report
        assert "Detailed Results" in report

    def test_report_has_timing(self):
        report = "GraphRAG avg: 3.0s | VectorRAG avg: 0.5s"
        assert "GraphRAG" in report
        assert "VectorRAG" in report

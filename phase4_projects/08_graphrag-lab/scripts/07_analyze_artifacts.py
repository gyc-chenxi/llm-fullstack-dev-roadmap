"""
GraphRAG 索引产物分析
=======================

分析 data/output/*.parquet 中的索引产物，打印统计信息：

  - entities: 实体数量 + 类型分布条形图
  - relationships: 关系数量 + 样本（source→target+description）
  - communities: 社区数量
  - community_reports: 社区报告样本标题
  - text_units: 文本块数量
  - documents: 原始文档数量

质量指标：
  - Relationship-to-Entity ratio: 0.3-2.0 为健康范围
  - Unique entity types: <3 表明 entity_types 配置过窄

用法：PYTHONPATH=. python scripts/07_analyze_artifacts.py
"""

import os
import sys
from pathlib import Path
import pandas as pd


def find_parquet(output_dir: Path, pattern: str) -> Path | None:
    """按模式（不区分大小写）查找 parquet 文件。"""
    pattern_lower = pattern.lower()
    for f in output_dir.glob("*.parquet"):
        if pattern_lower in f.name.lower():
            return f
    return None


def main():
    output_dir = Path("data/output")

    if not output_dir.exists():
        print("[Analyze] ERROR: data/output/ not found.")
        print("[Analyze] Run 'make run-index' first to build the GraphRAG index.")
        sys.exit(1)

    parquet_files = list(output_dir.glob("*.parquet"))
    if not parquet_files:
        print("[Analyze] ERROR: no .parquet files in data/output/")
        print("[Analyze] The index pipeline may have failed. Check logs/ for errors.")
        sys.exit(1)

    print("=" * 65)
    print("GraphRAG Index Artifacts Analysis")
    print("=" * 65)
    print(f"Output directory: {output_dir}/")
    print(f"Parquet files: {len(parquet_files)}")
    print()

    artifact_map = {}
    for key in ["entities", "relationships", "communities", "community_reports",
                 "text_units", "documents"]:
        fpath = find_parquet(output_dir, key)
        if fpath:
            artifact_map[key] = fpath

    dataframes = {}
    for name, fpath in artifact_map.items():
        try:
            dataframes[name] = pd.read_parquet(fpath)
            print(f"  ✓ {fpath.name:45s}  {len(dataframes[name]):>6,} rows × {dataframes[name].shape[1]:>2} cols")
            cols = ", ".join(dataframes[name].columns[:6].tolist())
            if len(dataframes[name].columns) > 6:
                cols += f", ... (+{len(dataframes[name].columns) - 6})"
            print(f"    Columns: {cols}")
        except Exception as e:
            print(f"  ✗ {fpath.name}: read error — {e}")

    print()

    # 实体分析
    entities = dataframes.get("entities")
    if entities is not None:
        print("─" * 65)
        print(f"ENTITIES: {len(entities):,} total")
        if "type" in entities.columns:
            type_counts = entities["type"].value_counts()
            print("\n  Top entity types:")
            max_count = type_counts.max()
            for t, c in type_counts.head(12).items():
                bar_len = min(int(c / max_count * 35), 35) if max_count > 0 else 0
                bar = "█" * bar_len
                print(f"  {str(t):22s} {bar} {c:>5,}")
        elif "title" in entities.columns:
            print("\n  Sample entities (by title):")
            for _, row in entities.head(8).iterrows():
                print(f"    • {row.get('title', row.get('name', 'N/A'))}")

    # 关系分析
    rels = dataframes.get("relationships")
    if rels is not None:
        print("\n" + "─" * 65)
        print(f"RELATIONSHIPS: {len(rels):,} total")
        if "source" in rels.columns and "target" in rels.columns:
            print("\n  Sample relationships:")
            for _, row in rels.head(8).iterrows():
                src = str(row["source"])[:40]
                tgt = str(row["target"])[:40]
                desc = str(row.get("description", ""))[:60]
                print(f"    {src} → {tgt}")
                if desc:
                    print(f"      {desc}")

    # 社区报告
    reports = dataframes.get("community_reports")
    if reports is not None:
        print("\n" + "─" * 65)
        print(f"COMMUNITY REPORTS: {len(reports):,} total")
        if "title" in reports.columns:
            print("\n  Sample report titles:")
            for t in reports["title"].head(6):
                print(f"    • {str(t)[:80]}")

    # 文本块 + 文档
    tu = dataframes.get("text_units")
    if tu is not None:
        print("\n" + "─" * 65)
        print(f"TEXT UNITS: {len(tu):,} total (chunks)")

    docs = dataframes.get("documents")
    if docs is not None:
        print("\n" + "─" * 65)
        print(f"DOCUMENTS: {len(docs):,} total (source files)")

    # 质量指标
    print("\n" + "=" * 65)
    print("INDEX QUALITY METRICS")
    print("=" * 65)

    if entities is not None and rels is not None:
        ratio = len(rels) / len(entities) if len(entities) > 0 else 0
        print(f"  Relationship-to-Entity ratio : {ratio:.2f}")
        if ratio < 0.3:
            print(f"    ⚠ Low ratio — LLM may not extract enough relationships.")
        elif ratio > 2.0:
            print(f"    ⚠ High ratio — may indicate noisy extractions.")
        else:
            print(f"    ✓ Healthy ratio (0.3–2.0)")

    if entities is not None and "type" in entities.columns:
        type_count = entities["type"].nunique()
        print(f"  Unique entity types           : {type_count}")
        if type_count < 3:
            print(f"    ⚠ Very few types — entity_types in settings.yaml may be too narrow")

    communities = dataframes.get("communities")
    if communities is not None:
        print(f"  Communities detected          : {len(communities)}")

    print()
    print("[Analyze] ✓ Analysis complete.")


if __name__ == "__main__":
    main()

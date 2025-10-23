#!/usr/bin/env python3
# File: scripts/plot/calculate_scene_balance.py
# Purpose: Calculate scene_balance_analysis from scene_structure.scenes
# Context: A28 Enhancement 2 - Scene Granularity Management System

"""
Scene balance calculator for A28 plot templates.

Reads a plot YAML file and calculates the scene_balance_analysis section
based on scene_structure.scenes data.

Usage:
    python scripts/plot/calculate_scene_balance.py <plot_file.yaml>
    python scripts/plot/calculate_scene_balance.py <plot_file.yaml> --output <output.yaml>
    python scripts/plot/calculate_scene_balance.py <plot_file.yaml> --dry-run
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def calculate_rank_distribution(scenes: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate distribution of importance ranks.

    Args:
        scenes: List of scene dictionaries with importance_rank field

    Returns:
        Dict with counts for each rank (S, A, B, C)
    """
    ranks = [scene.get("importance_rank", "B") for scene in scenes]
    counts = Counter(ranks)
    return {
        "S": counts.get("S", 0),
        "A": counts.get("A", 0),
        "B": counts.get("B", 0),
        "C": counts.get("C", 0),
    }


def calculate_tempo_variation(scenes: List[Dict[str, Any]]) -> str:
    """Calculate tempo variation based on emotional_weight changes.

    Args:
        scenes: List of scene dictionaries with emotional_weight field

    Returns:
        "high", "medium", or "low" based on variation
    """
    weights = [scene.get("emotional_weight", "medium") for scene in scenes]

    # Count transitions between different weights
    transitions = 0
    for i in range(len(weights) - 1):
        if weights[i] != weights[i + 1]:
            transitions += 1

    if len(scenes) <= 1:
        return "low"

    transition_ratio = transitions / (len(scenes) - 1)

    if transition_ratio >= 0.6:
        return "high"
    elif transition_ratio >= 0.3:
        return "medium"
    else:
        return "low"


def calculate_balance_score(
    scenes: List[Dict[str, Any]],
    rank_dist: Dict[str, int]
) -> int:
    """Calculate balance score (0-100) based on rank distribution and engagement.

    Scoring criteria:
    - S-rank presence: 20 points (10-20 points based on count)
    - A-rank presence: 15 points (5-15 points based on count)
    - High engagement ratio: 30 points
    - Rank diversity: 20 points
    - Emotional variation: 15 points

    Args:
        scenes: List of scene dictionaries
        rank_dist: Rank distribution dict

    Returns:
        Score from 0 to 100
    """
    score = 0
    total_scenes = len(scenes)

    if total_scenes == 0:
        return 0

    # S-rank scoring (10-20 points)
    s_count = rank_dist["S"]
    if s_count > 0:
        score += min(10 + s_count * 5, 20)

    # A-rank scoring (5-15 points)
    a_count = rank_dist["A"]
    if a_count > 0:
        score += min(5 + a_count * 2, 15)

    # High engagement ratio (30 points)
    high_engagement_count = sum(
        1 for scene in scenes
        if scene.get("reader_engagement_level") == "high"
    )
    engagement_ratio = high_engagement_count / total_scenes
    score += int(engagement_ratio * 30)

    # Rank diversity (20 points)
    unique_ranks = sum(1 for count in rank_dist.values() if count > 0)
    score += (unique_ranks / 4) * 20

    # Emotional variation (15 points)
    tempo = calculate_tempo_variation(scenes)
    tempo_score = {"high": 15, "medium": 10, "low": 5}
    score += tempo_score.get(tempo, 5)

    return min(int(score), 100)


def calculate_scene_balance(plot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate scene_balance_analysis from scene_structure.

    Args:
        plot_data: Full plot YAML data

    Returns:
        Calculated scene_balance_analysis dict
    """
    scene_structure = plot_data.get("scene_structure", {})
    scenes = scene_structure.get("scenes", [])

    if not scenes:
        return {
            "total_scenes": 0,
            "rank_distribution": {"S": 0, "A": 0, "B": 0, "C": 0},
            "tempo_variation": "",
            "balance_score": 0,
        }

    rank_dist = calculate_rank_distribution(scenes)
    tempo = calculate_tempo_variation(scenes)
    score = calculate_balance_score(scenes, rank_dist)

    return {
        "total_scenes": len(scenes),
        "rank_distribution": rank_dist,
        "tempo_variation": tempo,
        "balance_score": score,
    }


def update_plot_file(
    input_path: Path,
    output_path: Path | None = None,
    dry_run: bool = False
) -> None:
    """Update plot file with calculated scene_balance_analysis.

    Args:
        input_path: Input YAML file path
        output_path: Output YAML file path (defaults to input_path)
        dry_run: If True, only print calculated values without writing
    """
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Load YAML
    with open(input_path, "r", encoding="utf-8") as f:
        plot_data = yaml.safe_load(f)

    # Calculate scene balance
    scene_balance = calculate_scene_balance(plot_data)

    # Display results
    print(f"\n=== Scene Balance Analysis ===")
    print(f"Total scenes: {scene_balance['total_scenes']}")
    print(f"Rank distribution:")
    for rank, count in scene_balance['rank_distribution'].items():
        print(f"  {rank}: {count}")
    print(f"Tempo variation: {scene_balance['tempo_variation']}")
    print(f"Balance score: {scene_balance['balance_score']}/100")

    if dry_run:
        print("\n[Dry run mode] No files modified.")
        return

    # Update plot data
    plot_data["scene_balance_analysis"] = scene_balance

    # Write output
    output = output_path or input_path
    with open(output, "w", encoding="utf-8") as f:
        yaml.dump(
            plot_data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    print(f"\n[OK] Updated: {output}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate scene_balance_analysis for A28 plot files"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input plot YAML file"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path (defaults to input file)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show calculated values without modifying files"
    )

    args = parser.parse_args()

    update_plot_file(args.input_file, args.output, args.dry_run)


if __name__ == "__main__":
    main()

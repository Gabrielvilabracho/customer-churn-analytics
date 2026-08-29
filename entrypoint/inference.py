#!/usr/bin/env python3
"""
Inference entrypoint for the churn prediction model.

Usage:
    python inference.py --config config/local.yaml --input data/03-features/new_data.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main(config: dict, input_path: str) -> None:
    """Main inference pipeline."""
    print(f"Starting inference in {config['app']['environment']} environment")
    
    # TODO: Implement inference pipeline
    # 1. Load model from data/04-predictions/
    # 2. Load input data
    # 3. Preprocess input
    # 4. Run predictions
    # 5. Save results
    
    print(f"Inference completed for {input_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run churn predictions")
    parser.add_argument(
        "--config",
        type=str,
        default="config/local.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input data file",
    )
    args = parser.parse_args()
    
    config = load_config(args.config)
    main(config, args.input)
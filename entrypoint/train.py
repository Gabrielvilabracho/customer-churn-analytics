#!/usr/bin/env python3
"""
Training entrypoint for the churn prediction model.

Usage:
    python train.py --config config/local.yaml
"""

import argparse
import sys
from pathlib import Path

import yaml


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main(config: dict) -> None:
    """Main training pipeline."""
    print(f"Starting training in {config['app']['environment']} environment")
    
    # TODO: Implement training pipeline
    # 1. Load data from data/01-raw/
    # 2. Preprocess and save to data/02-preprocessed/
    # 3. Feature engineering and save to data/03-features/
    # 4. Train model
    # 5. Evaluate and save to data/04-predictions/
    
    print("Training pipeline completed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train churn prediction model")
    parser.add_argument(
        "--config",
        type=str,
        default="config/local.yaml",
        help="Path to config file",
    )
    args = parser.parse_args()
    
    config = load_config(args.config)
    main(config)
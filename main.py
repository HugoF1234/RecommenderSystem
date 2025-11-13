"""
Main entry point for Save Eat project
Provides CLI interface for common tasks
"""

import argparse
import sys
from pathlib import Path

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Save Eat - Recipe Recommendation System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Preprocess command
    preprocess_parser = subparsers.add_parser("preprocess", help="Preprocess the dataset")
    preprocess_parser.add_argument("--data-path", type=str, default="data/raw", help="Path to raw data")
    preprocess_parser.add_argument("--output-path", type=str, default="data/processed", help="Path to save processed data")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train the model")
    train_parser.add_argument("--config", type=str, default="config/config.yaml", help="Path to config file")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download the dataset")
    download_parser.add_argument("--dataset", type=str, default="irkaal/foodcom-recipes-and-reviews", help="Kaggle dataset identifier")
    
    args = parser.parse_args()
    
    if args.command == "preprocess":
        print("Preprocessing dataset...")
        # Import and run preprocessing
        from src.data.loader import DataLoader
        from src.data.preprocessing import DataPreprocessor
        import yaml
        
        # Load config
        config_path = Path("config/config.yaml")
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        else:
            config = {}
        
        dataset_config = config.get("dataset", {})
        preprocessor_config = {
            "min_user_interactions": dataset_config.get("min_user_interactions", 5),
            "min_recipe_ratings": dataset_config.get("min_recipe_ratings", 3),
            "train_ratio": dataset_config.get("train_ratio", 0.7),
            "val_ratio": dataset_config.get("val_ratio", 0.15),
            "test_ratio": dataset_config.get("test_ratio", 0.15)
        }
        
        # Load data
        loader = DataLoader(raw_data_path=args.data_path)
        data = loader.load_all()
        
        # Preprocess
        preprocessor = DataPreprocessor(**preprocessor_config)
        processed_data = preprocessor.process(
            data["interactions"],
            data["recipes"],
            save_path=Path(args.output_path)
        )
        
        print(f"Preprocessing complete! Processed {processed_data['stats']['n_users']} users and {processed_data['stats']['n_recipes']} recipes.")
        
    elif args.command == "download":
        print(f"Downloading dataset: {args.dataset}...")
        from src.data.loader import DataLoader
        
        loader = DataLoader()
        try:
            loader.download_dataset(args.dataset)
            print("Dataset downloaded successfully!")
        except Exception as e:
            print(f"Error downloading dataset: {e}")
            print("Please download manually from: https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews")
            print(f"Extract files to: {loader.raw_data_path}")
    
    elif args.command == "train":
        print("Training model...")
        print("Note: Training script needs to be implemented in scripts/train.py")
        print("For now, please use the training module directly or a Jupyter notebook.")
        # TODO: Implement training script
    
    elif args.command == "serve":
        print(f"Starting API server on {args.host}:{args.port}...")
        import uvicorn
        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()


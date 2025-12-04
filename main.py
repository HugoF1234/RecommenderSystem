"""
Main entry point for Save Eat project
Provides CLI interface for common tasks

This module serves as the primary command-line interface for the Save Eat
recommendation system. It handles:
- Dataset downloading and preprocessing
- Database initialization (SQLite/PostgreSQL)
- Model training workflows
- API server startup

The CLI is designed to simplify common operations and provide a consistent
interface for both development and production deployments.
"""

import argparse
import sys
from pathlib import Path

def main():
    """
    Main entry point for the CLI

    Sets up argument parsing for all available commands and routes execution
    to the appropriate handlers. Each command is designed to be independent
    and can be run without requiring other commands to have been executed first.
    """
    parser = argparse.ArgumentParser(description="Save Eat - Recipe Recommendation System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Preprocess command - transforms raw CSV data into model-ready format
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
    download_parser = subparsers.add_parser("download", help="Download the cleaned dataset")
    download_parser.add_argument("--dataset", type=str, default=None, help="Kaggle dataset identifier (default: RecSys project dataset Food.com)")
    
    # Load database command
    load_db_parser = subparsers.add_parser("load-db", help="Load CSV data into database")
    load_db_parser.add_argument("--db-type", type=str, choices=["sqlite", "postgresql"], default="sqlite", help="Database type")
    load_db_parser.add_argument("--host", type=str, help="PostgreSQL host")
    load_db_parser.add_argument("--port", type=int, help="PostgreSQL port")
    load_db_parser.add_argument("--database", type=str, help="PostgreSQL database name")
    load_db_parser.add_argument("--user", type=str, help="PostgreSQL user")
    load_db_parser.add_argument("--password", type=str, help="PostgreSQL password")
    
    args = parser.parse_args()
    
    if args.command == "preprocess":
        print("Preprocessing dataset...")

        # Try to load from database first (if available)
        # This allows us to skip CSV parsing if data is already in the database,
        # which is much faster for large datasets
        db_path = Path("data/saveeat.db")
        if db_path.exists():
            print(f"✅ Found database at {db_path}")
            print("   Loading data from database...")
            try:
                from src.data.db_to_processed import preprocess_from_db
                import os
                
                # Determine database type
                db_type = "sqlite"
                if os.getenv("DATABASE_URL"):
                    db_type = "postgresql"
                    db_path = os.getenv("DATABASE_URL")
                
                processed_data, graph_data = preprocess_from_db(
                    db_path=str(db_path),
                    database_type=db_type,
                    output_path=Path(args.output_path)
                )
                
                print(f"✅ Preprocessing complete!")
                print(f"   - {processed_data['stats']['n_users']} users")
                print(f"   - {processed_data['stats']['n_recipes']} recipes")
                print(f"   - Graph: {graph_data.num_nodes} nodes, {graph_data.num_edges} edges")
                return
            except Exception as e:
                print(f"⚠️  Error loading from database: {e}")
                print("   Falling back to CSV files...")
        
        # Fallback: Load from CSV files
        print("   Loading data from CSV files...")
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
        
        print(f"✅ Preprocessing complete! Processed {processed_data['stats']['n_users']} users and {processed_data['stats']['n_recipes']} recipes.")
        
    elif args.command == "download":
        print("Downloading cleaned dataset from Kaggle...")
        print("Dataset: RecSys project dataset Food.com")
        print("Files needed: recipes_clean_full.csv and reviews_clean_full.csv")
        from src.data.loader import DataLoader
        
        loader = DataLoader()
        try:
            loader.download_dataset(args.dataset)
            print("Dataset downloaded successfully!")
            print("Please verify that recipes_clean_full.csv and reviews_clean_full.csv are in data/raw/")
        except Exception as e:
            print(f"Error downloading dataset: {e}")
            print("Please download manually from Kaggle: 'RecSys project dataset Food.com'")
            print("Ensure you download recipes_clean_full.csv and reviews_clean_full.csv")
            print(f"Extract files to: {loader.raw_data_path}")
    
    elif args.command == "load-db":
        print(f"Loading data into {args.db_type} database...")
        
        if args.db_type == "postgresql":
            from scripts.load_to_postgres import load_to_postgres
            try:
                # If no arguments provided, use DATABASE_URL from environment
                if not args.host and not args.database and not args.user:
                    import os
                    if os.getenv("DATABASE_URL"):
                        print("Using DATABASE_URL from environment...")
                        load_to_postgres()  # Will use DATABASE_URL automatically
                    else:
                        print("Error: No DATABASE_URL found and no connection parameters provided")
                        print("Either set DATABASE_URL environment variable or provide --host, --database, --user, --password")
                        sys.exit(1)
                else:
                    load_to_postgres(
                        host=args.host,
                        port=args.port,
                        database=args.database,
                        user=args.user,
                        password=args.password
                    )
                print("✅ Data loaded successfully into PostgreSQL!")
            except Exception as e:
                print(f"❌ Error loading data: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            from src.data.load_to_db import load_data_to_database
            try:
                load_data_to_database()
                print("✅ Data loaded successfully into SQLite!")
            except Exception as e:
                print(f"❌ Error loading data: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
    
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


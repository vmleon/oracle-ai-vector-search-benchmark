#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import shared utilities
sys.path.append(str(Path(__file__).parent.parent))
from shared_utils import (
    load_benchmark_config, create_base_argument_parser, generate_test_name,
    ensure_reports_directory, print_benchmark_header, print_benchmark_footer,
    merge_config_with_args, validate_environment_variables
)

def load_ingestion_config():
    """Load ingestion specific configuration"""
    load_dotenv()
    
    # Load base config
    config = load_benchmark_config()
    
    # Add ingestion specific settings
    config.update({
        'users': int(os.getenv('BENCHMARK_USERS', '1')),
        'spawn_rate': int(os.getenv('BENCHMARK_SPAWN_RATE', '1')),
        'samples_dir': os.getenv('SAMPLES_DIR', '../../../samples'),
    })
    
    return config

def validate_samples_directory(samples_dir):
    """Validate that samples directory exists and contains PDF files"""
    samples_path = Path(samples_dir)
    
    if not samples_path.exists():
        print(f"Error: Samples directory not found at {samples_dir}")
        print("Please ensure PDF files are available in the samples directory")
        return False
    
    pdf_files = list(samples_path.glob("*.pdf"))
    if not pdf_files:
        print(f"Error: No PDF files found in {samples_dir}")
        return False
    
    return len(pdf_files)

def run_benchmark(config, args):
    """Run the document ingestion benchmark"""
    
    # Merge configuration with command line arguments
    config_mapping = {
        'environment': 'environment',
        'users': 'users',
        'spawn_rate': 'spawn_rate',
        'samples_dir': 'samples_dir'
    }
    final_config = merge_config_with_args(config, args, config_mapping)
    
    # Validate samples directory
    pdf_count = validate_samples_directory(final_config['samples_dir'])
    if not pdf_count:
        return 1
    
    # Generate test name and setup
    test_name = generate_test_name("document_ingestion_completion", final_config['environment'])
    ensure_reports_directory()
    
    # Calculate expected uploads
    # TODO: Make PDF file count dynamic based on actual files in samples directory
    expected_uploads = final_config['users'] * 19  # 19 PDF files per user (hardcoded for this iteration)
    
    # Print standardized header
    print_benchmark_header(test_name, final_config, "run-to-completion ingestion benchmark")
    print(f"Expected total uploads: {expected_uploads} ({final_config['users']} users × 19 files each)")
    print(f"PDF Files Available: {pdf_count}")
    print(f"Samples Directory: {final_config['samples_dir']}")
    print("Mode: Run-to-completion (test ends when all files are uploaded)")
    print("-" * 40)
    
    # Prepare locust command (no --run-time for completion mode)
    locust_cmd = [
        'locust',
        '-f', 'locustfile.py',
        '--users', str(final_config['users']),
        '--spawn-rate', str(final_config['spawn_rate']),
        '--headless',
        '--test-name', test_name,
        '--html', f'reports/{test_name}.html',
        '--csv', f'reports/{test_name}',
        '--logfile', f'reports/{test_name}.log'
    ]
    
    # Set environment variables for locust using consistent .env variables
    env = os.environ.copy()
    env['LOCUST_HOST'] = final_config['host']
    env['SAMPLES_DIR'] = final_config['samples_dir']
    
    try:
        # Run locust
        result = subprocess.run(locust_cmd, env=env, check=True)
        
        print("-" * 40)
        print("Run-to-completion ingestion benchmark completed!")
        print("Reports saved to:")
        print(f"  HTML: reports/{test_name}.html")
        print(f"  CSV:  reports/{test_name}_*.csv")
        print(f"  Log:  reports/{test_name}.log")
        print("")
        # TODO: Make PDF file count dynamic based on actual files in samples directory  
        print("This test measured how long it takes to upload all 19 PDFs")
        print(f"with {final_config['users']} concurrent user(s). Check the reports for detailed timing.")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"Error running benchmark: {e}")
        return 1
    except FileNotFoundError:
        print("Error: locust command not found. Please ensure locust is installed.")
        return 1

def main():
    # Create argument parser using shared utilities
    epilog_examples = """
This tool measures how long it takes to upload all 19 PDF files once, not continuous load testing.

Examples:
  python benchmark.py                           # Use defaults from .env
  python benchmark.py --environment staging    # Override environment
  python benchmark.py --users 3 --spawn-rate 2    # 3 concurrent users
  python benchmark.py --host http://custom:8000    # Override host
        """
    
    parser = create_base_argument_parser('Document Ingestion Run-to-Completion Benchmark Tool', epilog_examples)
    
    # Add ingestion specific arguments
    parser.add_argument('--samples-dir', 
                       help='Directory containing PDF files for upload')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_ingestion_config()
    
    # Run benchmark
    return run_benchmark(config, args)

if __name__ == '__main__':
    sys.exit(main())
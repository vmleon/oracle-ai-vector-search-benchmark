#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Import shared utilities
sys.path.append(str(Path(__file__).parent.parent))
from shared_utils import (
    load_benchmark_config, create_base_argument_parser, generate_test_name,
    ensure_reports_directory, print_benchmark_header, print_benchmark_footer,
    merge_config_with_args, validate_environment_variables
)

def load_vector_search_config():
    """Load vector search specific configuration"""
    load_dotenv()
    
    # Load base config
    config = load_benchmark_config()
    
    # Add vector search specific settings
    config.update({
        'users': int(os.getenv('BENCHMARK_USERS', '20')),
        'spawn_rate': int(os.getenv('BENCHMARK_SPAWN_RATE', '2')),
        'run_time': os.getenv('BENCHMARK_RUN_TIME', '300s'),
    })
    
    return config

def run_benchmark(config, args):
    """Run the vector search benchmark"""
    
    # Merge configuration with command line arguments
    config_mapping = {
        'environment': 'environment',
        'users': 'users', 
        'spawn_rate': 'spawn_rate',
        'run_time': 'run_time'
    }
    final_config = merge_config_with_args(config, args, config_mapping)
    
    # Generate test name and setup
    test_name = generate_test_name("vector_search", final_config['environment'])
    ensure_reports_directory()
    
    # Print standardized header
    print_benchmark_header(test_name, final_config, "vector search benchmark")
    print("-" * 40)
    
    # Prepare locust command
    locust_cmd = [
        'locust',
        '-f', 'locustfile.py',
        '--users', str(final_config['users']),
        '--spawn-rate', str(final_config['spawn_rate']),
        '--run-time', str(final_config['run_time']),
        '--headless',
        '--test-name', test_name,
        '--html', f'reports/{test_name}.html',
        '--csv', f'reports/{test_name}',
        '--logfile', f'reports/{test_name}.log'
    ]
    
    # Set environment variables for locust using consistent .env variables
    env = os.environ.copy()
    env['LOCUST_HOST'] = final_config['host']
    
    try:
        # Run locust
        result = subprocess.run(locust_cmd, env=env, check=True)
        print_benchmark_footer(test_name, success=True)
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"Error running benchmark: {e}")
        print_benchmark_footer(test_name, success=False)
        return 1
    except FileNotFoundError:
        print("Error: locust command not found. Please ensure locust is installed.")
        return 1

def main():
    # Create argument parser using shared utilities
    epilog_examples = """
Examples:
  python benchmark.py                           # Use defaults from .env
  python benchmark.py --environment staging    # Override environment
  python benchmark.py --users 50 --run-time 600s  # Override test parameters
  python benchmark.py --host http://custom:8000    # Override host
        """
    
    parser = create_base_argument_parser('Vector Search Benchmark Tool', epilog_examples)
    
    # Add vector search specific arguments
    parser.add_argument('--run-time', '-t',
                       help='Test duration (e.g., 300s, 10m, 1h)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_vector_search_config()
    
    # Run benchmark
    return run_benchmark(config, args)

if __name__ == '__main__':
    sys.exit(main())
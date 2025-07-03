#!/usr/bin/env python3
"""
Shared utilities for stress testing tools.
Provides common functions for configuration, argument parsing, and reporting.
"""

import os
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


def load_benchmark_config():
    """Load benchmark configuration from .env file and environment variables"""
    load_dotenv()
    
    config = {
        'host': os.getenv('BENCHMARK_HOST', 'http://localhost:8000'),
        'environment': os.getenv('BENCHMARK_ENVIRONMENT', 'local'),
    }
    
    # Apply environment-specific host overrides
    config['host'] = resolve_environment_host(config['environment'])
    
    return config


def resolve_environment_host(environment):
    """Resolve host URL based on environment name"""
    # Environment-specific host mappings
    env_hosts = {
        'local': os.getenv('LOCAL_HOST', 'http://localhost:8000'),
        'staging': os.getenv('STAGING_HOST', 'http://staging-api.yourcompany.com'),
        'production': os.getenv('PRODUCTION_HOST', 'http://api.yourcompany.com')
    }
    
    # Return environment-specific host or treat as custom URL
    return env_hosts.get(environment, environment)


def create_base_argument_parser(description, epilog_examples=""):
    """Create a base argument parser with common options"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_examples
    )
    
    # Common arguments for all benchmark tools
    parser.add_argument('--environment', '-e', 
                       help='Target environment (local, staging, production)')
    parser.add_argument('--users', '-u', type=int,
                       help='Number of concurrent users')
    parser.add_argument('--spawn-rate', '-r', type=int,
                       help='Users spawned per second')
    parser.add_argument('--host', 
                       help='Target host URL (overrides environment-based host)')
    
    return parser


def generate_test_name(test_type, environment):
    """Generate a standardized test name with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{test_type}_{environment}_{timestamp}"


def ensure_reports_directory():
    """Create reports directory if it doesn't exist"""
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def print_benchmark_header(test_name, config, test_type="benchmark"):
    """Print standardized benchmark header information"""
    print(f"Starting {test_type}: {test_name}")
    print(f"Environment: {config.get('environment', 'unknown')}")
    print(f"Host: {config.get('host', 'unknown')}")
    print(f"Users: {config.get('users', 'unknown')}")
    print(f"Spawn Rate: {config.get('spawn_rate', 'unknown')}/s")
    
    # Add run time for vector search tests
    if 'run_time' in config:
        print(f"Duration: {config['run_time']}")


def print_benchmark_footer(test_name, success=True):
    """Print standardized benchmark completion information"""
    status = "completed!" if success else "failed!"
    print("-" * 40)
    print(f"Benchmark {status}")
    print("Reports saved to:")
    print(f"  HTML: reports/{test_name}.html")
    print(f"  CSV:  reports/{test_name}_*.csv")
    print(f"  Log:  reports/{test_name}.log")


def validate_environment_variables(required_vars):
    """Validate that required environment variables are set"""
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file or set these variables.")
        return False
    
    return True


def merge_config_with_args(base_config, args, config_mapping):
    """Merge base configuration with command line arguments"""
    merged_config = base_config.copy()
    
    for arg_name, config_key in config_mapping.items():
        arg_value = getattr(args, arg_name, None)
        if arg_value is not None:
            merged_config[config_key] = arg_value
    
    # Handle host override logic
    if args.host:
        merged_config['host'] = args.host
    elif args.environment and args.environment != base_config.get('environment'):
        merged_config['host'] = resolve_environment_host(args.environment)
        merged_config['environment'] = args.environment
    
    return merged_config
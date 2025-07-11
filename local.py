#!/usr/bin/env python3

import kagglehub
import os
import sys
import shutil
import subprocess
import time
import secrets
import string
from dotenv import load_dotenv, set_key

# Load existing environment variables from .env file
load_dotenv()

def setup():
    # Create necessary directories
    os.makedirs("db_data", exist_ok=True)
    os.makedirs("samples", exist_ok=True)
    
    check_podman_machine_running()
    
    print("Running Oracle Database as a container:")
    
    # Check that there is not already a container named ora_vector_benchmark, if exists, skip the podman run that follows.
    try:
        if is_oracle_database_container_created():
            print("✓ Container ora_vector_benchmark already exists, skipping creation")
        else:
            # Run Oracle Database with podman
            db_data_path = os.path.abspath("db_data")
            try:
                subprocess.run([
                    "podman", "run", 
                    "--name", "ora_vector_benchmark", 
                    "--rm", "-d", 
                    "-p", "1521:1521", 
                    "-v", f"{db_data_path}:/opt/oracle/oradata",
                    "container-registry.oracle.com/database/free:latest"
                ], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: Failed to start Oracle Database container: {e}")
                sys.exit(1)
    except subprocess.CalledProcessError:
        print("Error: Could not check existing containers")
        sys.exit(1)

    print("Waiting for database to be healthy...")
    wait_for_database_ready()
    print("✓ Oracle Database container started")

    # Generate database password if not exists
    env_file_path = '.env'
    existing_password = os.getenv('ORACLE_DB_PASSWORD')
    
    if not existing_password:
        # Generate random password and save it in .env file
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        
        # Create .env file if it doesn't exist
        if not os.path.exists(env_file_path):
            with open(env_file_path, 'w') as f:
                f.write("# Oracle Database Password\n")
        
        # Update or add the ORACLE_DB_PASSWORD using dotenv
        set_key(env_file_path, 'ORACLE_DB_PASSWORD', password)
        print("✓ Generated and saved database password to .env file")
    else:
        print("✓ Database password already exists in .env file")
        password = existing_password

    # Check that there are pdf files on samples/ folder. if there are pdf files, skip kagglehub download
    pdf_files = [f for f in os.listdir("samples") if f.lower().endswith('.pdf')]
    if pdf_files:
        print(f"✓ Found {len(pdf_files)} PDF files in samples/ folder, skipping download")
    else:
        # using kagglehub, download "manisha717/dataset-of-pdf-files"
        print("Downloading PDF dataset from Kaggle...")
        path = kagglehub.dataset_download("manisha717/dataset-of-pdf-files")
        
        # Move all files from downloaded path to flat structure in samples/
        for root, _, files in os.walk(path):
            for file in files:
                source_file_path = os.path.join(root, file)
                shutil.move(source_file_path, "samples/")

        shutil.rmtree(path)
        print("✓ PDF dataset downloaded and extracted")

    print("✓ Using database password from .env file")
    
    # Set the database password
    set_database_password(password)

    # grand permissions to database user
    grand_permissions_to_pdbadmin(password)

    # Create the queues
    create_queues(password)
    
    # Run liquibase update from src/liquibase/
    liquibase_dir = os.path.abspath("src/liquibase")
    try:
        subprocess.run([
                "liquibase", f"--password={password}", "update"
            ], cwd=liquibase_dir, check=True)
        print("✓ Database schema updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to update database schema: {e}")
        sys.exit(1)

    print("\nDatabase setup complete!")
    print("\nTo start the services:")
    print("1. API Service (port 8000):")
    print("   cd src/api_service && source venv/bin/activate && gunicorn app:app -c gunicorn.conf.py")
    print("2. Vector Maker Service (port 8001):")
    print("   cd src/vector_maker_service && source venv/bin/activate && gunicorn app:app -c gunicorn.conf.py")

def cleanup():
    # Stop and remove container ora_vector_benchmark using podman
    try:
        subprocess.run(["podman", "stop", "ora_vector_benchmark"], check=False)
        print("✓ Container stopped and removed")
    except Exception as e:
        print(f"Warning: Error cleaning up container: {e}")
    
    if os.path.exists("samples"):
        shutil.rmtree("samples")
    if os.path.exists("db_data"):
        shutil.rmtree("db_data")
    if os.path.exists("src/shared"):
        shutil.rmtree("src/shared")

def set_database_password(password):
    try:
        subprocess.run([
            "podman", "exec", "ora_vector_benchmark", 
            "./setPassword.sh", password
        ], check=True)
        print("✓ Database password set successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to set database password: {e}")
        sys.exit(1)

def grand_permissions_to_pdbadmin(password):
    try:
        subprocess.run([
                "sql", f"sys/{password}@localhost:1521/FREE", "as", 
                "sysdba", "@local_pdb_grant.sql"
            ], check=True)
        print("✓ Database user grant permissions successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to grand user permissions: {e}")
        sys.exit(1)

def create_queues(password):
    try:
        subprocess.run([
                "sql", f"pdbadmin/{password}@localhost:1521/FREEPDB1", "@pdb_queues.sql"
            ], check=True)
        print("✓ Database created queues successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to create queues: {e}")
        sys.exit(1)

def wait_for_database_ready(max_wait_seconds=120, check_interval=20):
    """Wait for Oracle database container to be ready, checking every interval for max_wait_seconds."""
    print(f"Checking database readiness every {check_interval} seconds (max {max_wait_seconds}s)...")
    
    # ORA-12514: Cannot connect to database
    # ORA-03113: database connection closed by peer
    # ORA-12528: TNS:listener: all appropriate instances are blocking new connections
    # ORA-01017: invalid credential or not authorized; logon denied
    
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        try:
            # Check if container is running
            if not is_oracle_database_container_created():
                print("✗ Container not running")
                time.sleep(check_interval)
                continue
            
            # Try to connect to the database to check if it's ready
            result = subprocess.run([
                "sql", "-s", f"pdbadmin/no_password@localhost:1521/FREEPDB1"
            ], capture_output=True, timeout=30)
            
            if result.returncode == 1 and is_pdbadmin_locked_and_ready(result.stdout):
                elapsed = int(time.time() - start_time)
                print(f"✓ Database is ready (took {elapsed}s)")
                return True
            else:
                print("✗ Database not ready yet...")
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print("✗ Database connection failed, retrying...")
        
        time.sleep(check_interval)
    
    print(f"✗ Database did not become ready within {max_wait_seconds} seconds")
    return False

def is_pdbadmin_locked_and_ready(stdout):
    if "ORA-28000: The account is locked" in str(stdout):
        time.sleep(5)
        return True
    return False

def check_podman_machine_running():
    # Check that podman machine is running
    try:
        result = subprocess.run(["podman", "machine", "list"], capture_output=True, text=True, check=True)
        if "Currently running" not in result.stdout:
            print("Error: Podman machine is not running. Please start it first.")
            sys.exit(1)
        print("✓ Podman machine is running")
    except subprocess.CalledProcessError:
        print("Error: Could not check podman machine status. Make sure podman is installed.")
        sys.exit(1)

def is_oracle_database_container_created():
    result = subprocess.run(["podman", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, check=True)
    return "ora_vector_benchmark" in result.stdout
            

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python local.py [setup|cleanup]")
        sys.exit(1)
    
    task = sys.argv[1]
    if task == "setup":
        setup()
    elif task == "cleanup":
        cleanup()
    else:
        print("Unknown task. Use: setup or cleanup")
        sys.exit(1)
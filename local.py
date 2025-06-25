#!/usr/bin/env python3

import kagglehub
import os
import sys
import shutil
import subprocess
import time
import secrets
import string
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load existing environment variables from .env file
load_dotenv()

def setup():
    os.makedirs("temp", exist_ok=True)
    os.makedirs("db_data", exist_ok=True)
    os.makedirs("samples", exist_ok=True)

    # Check that there are pdf files on samples/ folder. if there are pdf files, skip kagglehub download
    pdf_files = [f for f in os.listdir("samples") if f.lower().endswith('.pdf')]
    if pdf_files:
        print(f"✓ Found {len(pdf_files)} PDF files in samples/ folder, skipping download")
        return

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


def run():
    print("Running Oracle Database as a container:")
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
    
    # Check that there is not already a container named ora_vector_benchmark, if exists, skip the podman run that follows.
    try:
        result = subprocess.run(["podman", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, check=True)
        if "ora_vector_benchmark" in result.stdout:
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
                print("Waiting for database to be healthy...")
                time.sleep(30)
                print("✓ Oracle Database container started")
            except subprocess.CalledProcessError as e:
                print(f"Error: Failed to start Oracle Database container: {e}")
                sys.exit(1)
    except subprocess.CalledProcessError:
        print("Error: Could not check existing containers")
        sys.exit(1)
    
    # Ensure container is running if it was already created but stopped
    try:
        result = subprocess.run(["podman", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, check=True)
        if "ora_vector_benchmark" not in result.stdout:
            print("Starting existing container...")
            subprocess.run(["podman", "start", "ora_vector_benchmark"], check=True)
            print("✓ Existing container started")
            # Wait for the database to be healthy
            print("Waiting for database to be healthy...")
            time.sleep(30)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not start existing container: {e}")
    
    # Generate random password and save it in .env file
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    
    # Use dotenv to properly update the ORACLE_DB_PASSWORD in .env file
    env_file_path = '.env'
    
    # Create .env file if it doesn't exist
    if not os.path.exists(env_file_path):
        with open(env_file_path, 'w') as f:
            f.write("# Oracle Database Password\n")
    
    # Update or add the ORACLE_DB_PASSWORD using dotenv
    set_key(env_file_path, 'ORACLE_DB_PASSWORD', password)
    print("✓ Generated and saved database password to .env file")
    
    # Set the database password
    try:
        subprocess.run([
            "podman", "exec", "ora_vector_benchmark", 
            "./setPassword.sh", password
        ], check=True)
        print("✓ Database password set successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to set database password: {e}")
        sys.exit(1)

    # grand permissions to database user
    try:
        subprocess.run([
                "sql", f"sys/{password}@localhost:1521/FREE", "as", 
                "sysdba", "@local_pdb_grant.sql"
            ], check=True)
        print("✓ Database user grant permissions successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to grand user permissions: {e}")
        sys.exit(1)

    # Create the queues
    try:
        subprocess.run([
                "sql", f"pdbadmin/{password}@localhost:1521/FREEPDB1" "@pdb_queues.sql"
            ], check=True)
        print("✓ Database created queues successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to create queues: {e}")
        sys.exit(1)
    
    # TODO from src/ run liquibase update
    # grand permissions to database user
    src_dir = os.path.abspath("src")
    try:
        subprocess.run([
                "liquibase", f"--password={password}", "update"
            ], cwd=src_dir, check=True)
        print("✓ Database user grant permissions successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to grand user permissions: {e}")
        sys.exit(1)

    print("\nDatabase setup complete!")
    print("Change directory to src and run the application vector_maker with this command:")
    print("gunicorn -w 1 --timeout 300 --graceful-timeout 300 -b 0.0.0.0:8000 vector_maker:app")

def cleanup():
    # Stop and remove container ora_vector_benchmark using podman
    try:
        subprocess.run(["podman", "stop", "ora_vector_benchmark"], check=False)
        subprocess.run(["podman", "rm", "ora_vector_benchmark"], check=False)
        print("✓ Container stopped and removed")
    except Exception as e:
        print(f"Warning: Error cleaning up container: {e}")
    
    if os.path.exists("samples"):
        shutil.rmtree("samples")
    if os.path.exists("db_data"):
        shutil.rmtree("db_data")
    if os.path.exists("temp"):
        shutil.rmtree("temp")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python local.py [setup|run|cleanup]")
        sys.exit(1)
    
    task = sys.argv[1]
    if task == "setup":
        setup()
    elif task == "run":
        run()
    elif task == "cleanup":
        cleanup()
    else:
        print("Unknown task. Use: setup, run, or cleanup")
        sys.exit(1)
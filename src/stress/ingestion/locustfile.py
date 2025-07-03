import os
import random
import time
from locust import HttpUser, between, task, events
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DocumentIngestion(HttpUser):
    wait_time = between(0.5, 1)  # Minimal wait between tasks
    
    # Pre-populate host from environment variable or default
    host = os.getenv('LOCUST_HOST', 'http://localhost:8000')
    
    # Test PDF files from samples directory
    test_files = [
        "J5ZSV4CEZDUKODXRBOAVGJVB5XTR5QMA.pdf",
        "CS4O7BCLPRK6J5MKIK7BPBFC2UURCM7X.pdf",
        "BLQYONKYGPSK7RW76LOAUDZGQXB634CT.pdf",
        "HPXULDFI3DAZ3V2NZOHYUGUY5SLS4AHU.pdf",
        "JQTLTBNFMLOTJNAZWAJGUYXUWJ42X5WM.pdf",
        "WT4PUCQSO7JLM6FV4HZDJ6DN4ZGWFL7U.pdf",
        "W5VHS6JXL2IZQKOADSVN6J2JWZPNWVC6.pdf",
        "5F7F36M3NZCHDTIFIVI5JQRBDYNY6KJL.pdf",
        "CT6O4FXETQ2ABBLKKRWK5E344XQA73C3.pdf",
        "EI4NKIFHUUATUUEER4SDXP6EZNJK7GQH.pdf",
        "R6LHWCGK5EOQHHR7EXRI7ZJLBG2R5QOF.pdf",
        "XLXYJ2Y3MNRFYEKWJ4VFACQHPYGFASLZ.pdf",
        "QE6FLNHQQKHXPNZIXRPA362DGNJ4UZJB.pdf",
        "27UIROOYZ4IE3FKKNAPCKEQXWBKKN7XM.pdf",
        "VYK5MZE2ESWMGNXTHQZ56OQ46BR3JJUG.pdf",
        "YWJI57UE6VBGPHTJYLGMHWGRIBWIF2BG.pdf",
        "MG64TNXHW4FTW3UTMAX6PXK5AZ5MMO5X.pdf",
        "65WL52OJL3MDCHS3SWEUYFWBO5W23F2M.pdf",
        "HOR7BQTQAFIPH2Z5TCKEJ5FZCCV7MZBO.pdf"
    ]
    
    def on_start(self):
        """Called when a user starts"""
        # Check if API is ready before starting load test
        response = self.client.get("/health/ready")
        if response.status_code != 200:
            print(f"API not ready: {response.status_code}")
        
        # Set samples directory path
        self.samples_dir = os.getenv('SAMPLES_DIR', '../../../samples')
        
        # Initialize upload tracking
        self.files_to_upload = self.test_files.copy()
        self.upload_start_time = None
        self.upload_end_time = None
        self.completed_uploads = 0
    
    @task
    def upload_all_documents(self):
        """Upload all documents once and measure total time"""
        
        # Start timer on first upload
        if self.upload_start_time is None:
            self.upload_start_time = time.time()
            print(f"User {self.environment.runner.user_count} starting upload of {len(self.files_to_upload)} files")
        
        # Check if we have files left to upload
        if not self.files_to_upload:
            # All files uploaded, record end time and stop this user
            if self.upload_end_time is None:
                self.upload_end_time = time.time()
                total_time = self.upload_end_time - self.upload_start_time
                print(f"User completed all uploads in {total_time:.2f} seconds ({self.completed_uploads} files)")
            
            # Stop this user from running more tasks
            self.environment.runner.quit()
            return
        
        # Get the next file to upload
        filename = self.files_to_upload.pop(0)
        file_path = os.path.join(self.samples_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (filename, file, 'application/pdf')}
                
                with self.client.post("/upload", files=files, catch_response=True, name="upload_document") as response:
                    if response.status_code == 200:
                        # Validate response structure
                        try:
                            data = response.json()
                            if 'document_id' in data and 'message' in data:
                                response.success()
                                self.completed_uploads += 1
                            else:
                                response.failure("Missing 'document_id' or 'message' in response")
                        except:
                            response.failure("Invalid JSON response")
                    elif response.status_code == 409:
                        # Document already exists - count as successful
                        response.success()
                        self.completed_uploads += 1
                    else:
                        response.failure(f"HTTP {response.status_code}")
        except Exception as e:
            self.client.post("/upload", name="upload_error", catch_response=True).failure(f"File error: {str(e)}")

# Global variables for tracking
test_start_time = None
user_completion_times = []

# Custom event listeners for enhanced reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global test_start_time
    test_start_time = time.time()
    print(f"Starting run-to-completion ingestion test against {environment.host}")
    print(f"Target users: {environment.parsed_options.num_users}")
    print(f"Spawn rate: {environment.parsed_options.spawn_rate}")
    # TODO: Make PDF file count dynamic based on actual files in samples directory
    print(f"Test files per user: {len(DocumentIngestion.test_files)} PDFs")
    print(f"Total uploads expected: {environment.parsed_options.num_users * len(DocumentIngestion.test_files)}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    global test_start_time, user_completion_times
    
    test_end_time = time.time()
    total_test_time = test_end_time - test_start_time if test_start_time else 0
    
    print("Run-to-completion ingestion test completed")
    print(f"Total test duration: {total_test_time:.2f} seconds")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Successful uploads: {environment.stats.total.num_requests - environment.stats.total.num_failures}")
    print(f"Failed requests: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {environment.stats.total.max_response_time:.2f}ms")
    
    # Calculate throughput
    if total_test_time > 0:
        overall_rps = environment.stats.total.num_requests / total_test_time
        print(f"Overall RPS: {overall_rps:.2f}")

# Configuration for headless mode
@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--test-name", type=str, default="document_ingestion_run_to_completion", 
                       help="Name for the test run")
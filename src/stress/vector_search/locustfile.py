import os
import random
from locust import HttpUser, between, task, events
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class VectorSearch(HttpUser):
    wait_time = between(1, 3)  # Reduced for more intensive testing
    
    # Pre-populate host from environment variable or default
    host = os.getenv('LOCUST_HOST', 'http://localhost:8000')
    
    # Pre-populate test queries with varying complexity
    test_queries = [
        "These estimates were converted to the percent of population exposed",
        "machine learning algorithms for data processing",
        "artificial intelligence models and neural networks",
        "statistical analysis methods in research",
        "data visualization techniques",
        "cloud computing infrastructure",
        "software development best practices",
        "database optimization strategies",
        "cybersecurity threat detection",
        "natural language processing applications"
    ]
    
    def on_start(self):
        """Called when a user starts"""
        # Check if API is ready before starting load test
        response = self.client.get("/health/ready")
        if response.status_code != 200:
            print(f"API not ready: {response.status_code}")
    
    @task(weight=10)
    def search_vector(self):
        """Main search task - weighted heavily"""
        query = random.choice(self.test_queries)
        
        with self.client.post("/search", json={
            "query": query,
            "limit": int(os.getenv('SEARCH_LIMIT', '5'))
        }, catch_response=True) as response:
            if response.status_code == 200:
                # Validate response structure
                try:
                    data = response.json()
                    if 'results' in data:
                        response.success()
                    else:
                        response.failure("Missing 'results' in response")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(weight=2)
    def health_check(self):
        """Health check task - lower weight"""
        self.client.get("/health/ready", name="health_check")
    
    @task(weight=1)
    def status_check(self):
        """Status check task - lowest weight"""
        self.client.get("/status", name="status_check")

# Custom event listeners for enhanced reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"Starting benchmark test against {environment.host}")
    print(f"Target users: {environment.parsed_options.num_users}")
    print(f"Spawn rate: {environment.parsed_options.spawn_rate}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Benchmark test completed")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed requests: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {environment.stats.total.max_response_time:.2f}ms")
    print(f"RPS: {environment.stats.total.current_rps:.2f}")

# Configuration for headless mode
@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--test-name", type=str, default="vector_search_benchmark", 
                       help="Name for the test run")
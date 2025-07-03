from locust import HttpUser, between, task

class VectorSearch(HttpUser):
    wait_time = between(5, 15)
    
    @task
    def search_vector(self):
        self.client.post("/search", json={"query": "These estimates were converted to the percent of population exposed"})
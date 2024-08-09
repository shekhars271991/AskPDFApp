import os
from locust import HttpUser, task, between, TaskSet, events
import json

class UserBehavior(TaskSet):
    
    def on_start(self):
        self.login()
    
    def login(self):
        response = self.client.post("/auth/login", json={
            "username": "user1",
            "password": "12345"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token", None)
            print(f"Login successful, token: {self.token}")
        else:
            self.token = None
            print(f"Login failed with status code {response.status_code}")

    @task(1)
    def ask_question(self):
        if self.token:
            response = self.client.post("/api/ask?skip_cache=yes&test_db_perf=yes", json={"query": "What is AI?"}, headers={
                "Authorization": f"Bearer {self.token}"
            })
            # print(f"ask_question response status: {response.status_code}")

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(0.1, 0.5)

# Optional: Log request data
# @events.request.add_listener
# def log_request_data(request_type, name, response_time, response_length, **kwargs):
#     print(f"Request {name} took {response_time} ms and returned {response_length} bytes")


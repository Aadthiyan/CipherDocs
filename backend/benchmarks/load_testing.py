"""
Load Testing Configuration using Locust

Simulates various load patterns:
- Sustained load (constant 100 req/s)
- Ramp-up load (0 → 500 req/s over 10 minutes)
- Spike load (sudden 1000 req/s for 1 minute)

Requires: locust library
Install: pip install locust
"""

import random
import time
from locust import HttpUser, task, between, events, TaskSet
from locust.contrib.fasthttp import FastHttpUser


class DocumentSearchUser(FastHttpUser):
    """
    Simulates a user searching documents
    
    Tasks:
    - Search documents
    - Upload document
    - View search results
    """
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        # Simulate login
        self.token = self._get_token()
    
    def _get_token(self):
        """Get authentication token"""
        # Simulate token retrieval
        return "test_token_" + str(random.randint(1, 1000))
    
    @task(10)
    def search_documents(self):
        """Search documents (10% of traffic)"""
        queries = [
            "machine learning",
            "python programming",
            "data science",
            "cloud computing",
            "artificial intelligence",
        ]
        
        query = random.choice(queries)
        
        with self.client.get(
            f"/api/search?q={query}",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(3)
    def upload_document(self):
        """Upload document (3% of traffic)"""
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        
        with self.client.post(
            "/api/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Upload failed: {response.status_code}")
    
    @task(1)
    def get_document(self):
        """Get document details (1% of traffic)"""
        doc_id = random.randint(1, 1000)
        
        with self.client.get(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # 404 is valid
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class BrowsingUser(FastHttpUser):
    """
    Simulates a user browsing documents without searching heavily
    """
    
    wait_time = between(2, 5)
    
    def on_start(self):
        self.token = "test_token_" + str(random.randint(1, 1000))
    
    @task(5)
    def view_documents(self):
        """View document list"""
        with self.client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to list documents: {response.status_code}")


class AdminUser(FastHttpUser):
    """
    Simulates an admin performing system operations
    """
    
    wait_time = between(3, 7)
    
    def on_start(self):
        self.token = "admin_token_" + str(random.randint(1, 100))
    
    @task(2)
    def check_analytics(self):
        """Check analytics dashboard"""
        with self.client.get(
            "/api/analytics",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Analytics check failed: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("=" * 70)
    print("LOAD TEST STARTED")
    print("=" * 70)
    print(f"Target: {environment.host}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("=" * 70)
    print("LOAD TEST COMPLETED")
    print("=" * 70)
    print(f"Stop time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Log each request for analysis"""
    if exception:
        print(f"[FAIL] {request_type} {name} - {exception}")
    elif response.status_code >= 400:
        print(f"[ERROR] {request_type} {name} - {response.status_code}")


# Load test scenarios
"""
Run different load tests with:

1. SUSTAINED LOAD (100 req/s for 5 minutes):
   locust -f benchmarks/load_testing.py --host=http://localhost:8000 \
   -u 100 -r 10 -t 5m

2. RAMP-UP LOAD (0 → 500 req/s over 10 minutes):
   locust -f benchmarks/load_testing.py --host=http://localhost:8000 \
   -u 500 -r 50 -t 10m

3. SPIKE LOAD (1000 req/s for 1 minute):
   locust -f benchmarks/load_testing.py --host=http://localhost:8000 \
   -u 1000 -r 100 -t 1m

User Distribution:
- DocumentSearchUser: 70% (typical users searching)
- BrowsingUser: 20% (casual browsing)
- AdminUser: 10% (admin operations)

Key Metrics to Monitor:
- Response time (median, p95, p99)
- Request throughput
- Error rate
- CPU usage
- Memory usage
- Database connections

Success Criteria:
- Error rate < 1%
- P99 latency < 1000ms
- No connection timeouts
- Memory usage stable
- CPU not maxed out
"""

if __name__ == "__main__":
    print("Load testing configuration for CipherDocs")
    print("")
    print("Usage: locust -f benchmarks/load_testing.py --host=http://localhost:8000")
    print("")
    print("Examples:")
    print("  1. 100 users ramp-up over 5 minutes:")
    print("     locust -f benchmarks/load_testing.py -u 100 -r 10 -t 5m")
    print("")
    print("  2. 500 users constant for 10 minutes:")
    print("     locust -f benchmarks/load_testing.py -u 500 -r 50 -t 10m --headless")
    print("")
    print("  3. Spike test 1000 users for 1 minute:")
    print("     locust -f benchmarks/load_testing.py -u 1000 -r 100 -t 1m --headless")

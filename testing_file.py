import requests
import uuid
import time

# Configuration - Nginx handles the routing to the FastAPI cluster

BASE_URL = "http://localhost"
ORDER_URL = f"{BASE_URL}/order"
CHECKOUT_URL = f"{BASE_URL}/checkout"

def run_test_case(endpoint_url, header_name, payload, test_name):
    """
    Generic runner for testing endpoints with idempotency checks.
    """
    idempotency_key = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        header_name: idempotency_key
    }

    print(f"\n--- Running: {test_name} ---")
    print(f"Target: {endpoint_url}")
    print(f"Key: {idempotency_key}")

    try:
        # 1. Initial Request
        print(f"[Step 1] Sending initial request...")
        res1 = requests.post(endpoint_url, json=payload, headers=headers)
        
        if res1.status_code in [200, 201, 202]:
            print(f"✅ Success: API accepted request. Response: {res1.json()}")
        else:
            print(f"❌ Failed: HTTP {res1.status_code} - {res1.text}")
            return

        # 2. Idempotency Check (Duplicate)
        print(f"[Step 2] Sending duplicate request...")
        res2 = requests.post(endpoint_url, json=payload, headers=headers)
        
        if res2.status_code == 409 or (res2.status_code == 200 and "processed" in res2.text):
            print(f"✅ Success: Idempotency handled correctly (No duplicate processing).")
        else:
            print(f"⚠️ Warning: Expected block/conflict, but got HTTP {res2.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Ensure Nginx and API containers are healthy.")

def main():
    print("🚀 Starting Unified API Testing Suite")
    
    # Test Case 1: Standard Order Endpoint
    order_payload = {
        "order_id": f"ORD-{str(uuid.uuid4())[:8]}",
        "customer_id": "sonia_researcher",
        "total_amount": 450.75,
        "items": ["RTX-4090", "H100-GPU"],
        "shipping_address": "AI Research Lab, Sector 5",
        "correlation_id": str(uuid.uuid4())
    }
    run_test_case(ORDER_URL, "X-Idempotency-Key", order_payload, "Order Saga Flow")

    # Small delay to separate events in logs
    time.sleep(1)

    # Test Case 2: Legacy Checkout Endpoint
    checkout_payload = {
        "user_id": "user_88",
        "amount": 1200.00,
        "metadata": {"source": "mobile_app"}
    }
    run_test_case(CHECKOUT_URL, "Idempotency-Key", checkout_payload, "Checkout Legacy Flow")

    print("\n" + "="*40)
    print("Testing Complete. Check container logs to verify Kafka events:")
    print("sudo docker-compose logs -f api inventory-worker")
    print("="*40)

if __name__ == "__main__":
    main()
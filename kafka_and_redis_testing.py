import requests
import uuid
import time
import json

# Configuration
BASE_URL = "http://localhost"
ORDER_URL = f"{BASE_URL}/order"
CHECKOUT_URL = f"{BASE_URL}/checkout"

# Infrastructure Dashboards (for your reference)
INFRA_URLS = {
    "Redis Insight": "http://localhost:8001",
    "Kafka UI (Kafdrop)": "http://localhost:9000",
    "Prometheus": "http://localhost:9090",
    "Grafana": "http://localhost:3000"
}

def test_endpoint(name, url, header_name, payload):
    idempotency_key = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        header_name: idempotency_key
    }

    print(f"\n{'='*60}")
    print(f"🚀 TESTING ENDPOINT: {name}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Header: {header_name}: {idempotency_key}")

    try:
        # 1. Send Request
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers)
        latency = round((time.time() - start_time) * 1000, 2)

        print(f"\n--- [API RESPONSE] ---")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        print(f"Latency: {latency}ms")

        # 2. Check for Success
        if response.status_code in [200, 201]:
            print(f"\n✅ SUCCESS: Order accepted by {name}.")
            
            # Instructions for Infrastructure Verification
            print(f"\n--- [INFRASTRUCTURE VERIFICATION] ---")
            print(f"1. Check Redis (Idempotency):")
            print(f"   URL: {INFRA_URLS['Redis Insight']}")
            print(f"   Look for Key: 'order-lock:{idempotency_key}' or 'checkout-lock:{idempotency_key}'")
            
            print(f"2. Check Kafka (Avro Event):")
            print(f"   URL: {INFRA_URLS['Kafka UI (Kafdrop)']}/topic/order.created/messages")
            print(f"   Note: Message will be binary (Avro format).")

        # 3. Test Idempotency (Immediate Duplicate)
        print(f"\n--- [IDEMPOTENCY RETRY] ---")
        dup_res = requests.post(url, json=payload, headers=headers)
        print(f"Retry Status: {dup_res.status_code}")
        if dup_res.status_code == 409 or "processed" in dup_res.text:
            print(f"✅ PASSED: Duplicate request blocked.")
        else:
            print(f"❌ FAILED: Duplicate request was not blocked correctly.")

    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")

def main():
    # Test Case 1: Standard Order
    order_data = {
        "order_id": f"ORD-{str(uuid.uuid4())[:8]}",
        "customer_id": "sonia_ai",
        "total_amount": 599.99,
        "items": ["Jetson Nano", "Lidar Sensor"],
        "shipping_address": "Gurugram, Sector 44"
    }
    test_endpoint("Order Service", ORDER_URL, "X-Idempotency-Key", order_data)

    time.sleep(2) # Wait for logs to propagate

    # Test Case 2: Legacy Checkout
    checkout_data = {
        "user_id": "user_456",
        "amount": 125.50,
        "product": "Premium Subscription"
    }
    test_endpoint("Checkout Service", CHECKOUT_URL, "Idempotency-Key", checkout_data)

    print(f"\n{'='*60}")
    print("TESTING COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
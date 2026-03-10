import asyncio
import json
from common.kafka_client import get_producer, get_consumer
from common.idempotency import is_duplicate
import aioredis

async def main():
    redis = aioredis.from_url("redis://redis:6379")
    
    # 1. Initialize Kafka 
    consumer = await get_consumer(topic="order.created", group_id="inventory-service")
    producer = await get_producer()

    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode())
            order_id = data.get("order_id")

            # 2. Idempotency Check (Section 3 of your diagram)
            if await is_duplicate(redis, f"inv-lock:{order_id}"):
                continue

            # 3. Execute & Reply (Section 2 of your diagram)
            print(f"Processing stock for: {order_id}")
            
            # Logic here...
            
            # Reply back to Kafka
            await producer.send_and_wait("inventory.completed", b"SUCCESS")

    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
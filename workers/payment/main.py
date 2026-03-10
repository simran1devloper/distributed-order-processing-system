import asyncio
import logging
from redis import asyncio as aioredis
from common.idempotency import is_duplicate
from common.kafka_client import KafkaManager, get_consumer, get_producer
from common.models import OrderEvent, OrderStatus

# Professional Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("payment-worker")

REDIS_URL = "redis://redis:6379"

async def process_payment(order_id: str, amount: float) -> bool:
    """
    Simulates a 3rd party payment gateway call (e.g., Stripe/PayPal).
    """
    logger.info(f"💳 Processing Payment | Order: {order_id} | Amount: ${amount}")
    await asyncio.sleep(1.5)  # Simulate external API latency
    return True  # Logic: return True for success, False for decline

async def main():
    # 1. Initialize Infrastructure Connections
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    
    # Listen for 'inventory.success'
    consumer = await get_consumer(
        topic="inventory.success", 
        group_id="payment-worker-group"
    )
    producer = await get_producer()

    logger.info("🚀 Payment Worker active. Listening for 'inventory.success' events...")

    try:
        async for msg in consumer:
            if msg.value is None:
                continue

            try:
                # msg.value is already deserialized by KafkaManager.avro_deserializer
                event_data = OrderEvent(**msg.value)
                order_id = event_data.order_id
                amount = event_data.total_amount

                # 2. Idempotency Check
                if await is_duplicate(redis, f"payment-lock:{order_id}"):
                    logger.warning(f"⚠️ Duplicate payment request detected and skipped: {order_id}")
                    continue

                # 3. Business Logic Execution
                payment_success = await process_payment(order_id, amount)

                # 4. Saga Reply
                if payment_success:
                    reply_topic = "payment.success"
                    event_data.status = OrderStatus.PAYMENT_COMPLETED
                else:
                    reply_topic = "payment.failed"
                    event_data.status = OrderStatus.FAILED

                event_data.payload["transaction_id"] = f"txn_{order_id}"

                # Send result back to Kafka
                await producer.send_and_wait(reply_topic, event_data)
                logger.info(f"✅ Order {order_id} processed. Status: {event_data.status} -> Sent to {reply_topic}")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    except Exception as e:
        logger.error(f"💥 Critical error in Payment Worker loop: {e}")
    finally:
        # Graceful shutdown
        await consumer.stop()
        await KafkaManager.stop_producer()
        await redis.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Closing Payment Worker.")
import asyncio
import logging
from redis import asyncio as aioredis
from common.kafka_client import KafkaManager, get_producer, get_consumer
from common.idempotency import is_duplicate
from common.models import OrderEvent, OrderStatus

# Structured logging for Grafana/Loki
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shipping-worker")

REDIS_URL = "redis://redis:6379"

async def arrange_fulfillment(order_id: str, address: str) -> str:
    """
    Simulates integration with a Shipping Provider (e.g., FedEx, DHL, UPS).
    """
    logger.info(f"📦 Generating shipping label for Order: {order_id} to {address}")
    await asyncio.sleep(1.5)  # Simulate API call to shipping provider
    tracking_number = f"TRK-{order_id.upper()}-XYZ"
    return tracking_number

async def main():
    # 1. Connect to Infrastructure
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    
    # Listen for 'payment.success'
    consumer = await get_consumer(
        topic="payment.success", 
        group_id="shipping-worker-group"
    )
    producer = await get_producer()

    logger.info("🚚 Shipping Worker is online. Waiting for paid orders...")

    try:
        async for msg in consumer:
            if msg.value is None:
                continue

            try:
                # 2. Parse Incoming Event using Pydantic
                event = OrderEvent(**msg.value)
                order_id = event.order_id
                customer_address = event.payload.get("address", "Default Warehouse Address")

                # 3. Idempotency Layer
                if await is_duplicate(redis, f"shipping-lock:{order_id}"):
                    logger.warning(f"⚠️ Duplicate shipping request detected for: {order_id}")
                    continue

                # 4. Execute (Business Logic)
                tracking_id = await arrange_fulfillment(order_id, customer_address)

                # 5. Reply (Final Saga Step)
                reply_topic = "shipping.completed"
                event.status = OrderStatus.ORDER_COMPLETED
                event.payload["tracking_id"] = tracking_id
                event.payload["message"] = "Order has been handed to the carrier."

                await producer.send_and_wait(reply_topic, event)
                logger.info(f"✅ Shipping label created: {tracking_id} for {order_id}")

            except Exception as e:
                logger.error(f"💥 Shipping processing error for {order_id if 'order_id' in locals() else 'unknown'}: {e}")

    finally:
        await consumer.stop()
        await KafkaManager.stop_producer()
        await redis.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Closing Shipping Worker.")
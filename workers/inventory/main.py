import asyncio
import logging
from redis import asyncio as aioredis
from common.idempotency import is_duplicate
from common.kafka_client import KafkaManager, get_consumer, get_producer
from common.models import OrderEvent, InventoryReply

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inventory-worker")

REDIS_URL = "redis://redis:6379"

async def handle_order_created():
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    consumer = await get_consumer("order.created", group_id="inventory-worker-group")
    producer = await get_producer()

    logger.info("Inventory worker started, waiting for events...")

    try:
        async for msg in consumer:
            if msg.value is None:
                continue
            
            try:
                # msg.value is already deserialized by KafkaManager.avro_deserializer
                event = OrderEvent(**msg.value)
                order_id = event.order_id

                # Idempotency Check
                if await is_duplicate(redis, f"inventory:{order_id}"):
                    logger.info(f"Skipping duplicate order: {order_id}")
                    continue

                # Business Logic: Deduct Stock
                logger.info(f"📦 Deducting stock for Order: {order_id}")
                success = True  # Mocked success

                # Reply
                if success:
                    reply_topic = "inventory.success"
                    reply = InventoryReply(order_id=order_id, status="reserved")
                else:
                    reply_topic = "inventory.failed"
                    reply = InventoryReply(order_id=order_id, status="failed", reason="out_of_stock")

                await producer.send_and_wait(reply_topic, reply)
                logger.info(f"✅ Replied to {reply_topic} for order {order_id}")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    finally:
        await consumer.stop()
        await KafkaManager.stop_producer()
        await redis.close()

if __name__ == "__main__":
    asyncio.run(handle_order_created())
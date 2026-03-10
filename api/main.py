import os
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Depends
from redis import asyncio as aioredis
from common.kafka_client import KafkaManager
from common.idempotency import is_duplicate
from common.models import OrderEvent, OrderStatus

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-orchestrator")

# Environment
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Connected to Redis")
    yield
    # Shutdown
    await KafkaManager.stop_producer()
    await app.state.redis.close()
    logger.info("Resources cleaned up")

app = FastAPI(title="Saga Orchestrator API", lifespan=lifespan)

async def get_redis():
    return app.state.redis

# --- Service Layer Logic ---
async def start_saga_flow(order_event: OrderEvent):
    producer = await KafkaManager.get_producer()
    await producer.send_and_wait("order.created", order_event)
    logger.info(f"Saga started for order: {order_event.order_id}")

# --- Endpoints ---

@app.post("/order", status_code=202)
async def create_order(
    payload: dict, 
    x_idempotency_key: str = Header(None),
    redis: aioredis.Redis = Depends(get_redis)
):
    if not x_idempotency_key:
        raise HTTPException(status_code=400, detail="X-Idempotency-Key header missing")

    if await is_duplicate(redis, f"order-lock:{x_idempotency_key}"):
        raise HTTPException(status_code=409, detail="Duplicate request in progress")

    order_event = OrderEvent(
        order_id=payload.get("order_id", f"ORD-{uuid.uuid4().hex[:8]}"),
        correlation_id=payload.get("correlation_id", str(uuid.uuid4())),
        customer_id=payload.get("customer_id", "GUEST"),
        total_amount=float(payload.get("total_amount", 0.0)),
        status=OrderStatus.PENDING,
        payload={"source": "order_endpoint", "items": str(payload.get("items", []))}
    )

    try:
        await start_saga_flow(order_event)
        return {"status": "accepted", "order_id": order_event.order_id}
    except Exception as e:
        logger.error(f"Failed to start saga: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/checkout", status_code=202)
async def start_checkout(
    payload: dict, 
    idempotency_key: str = Header(None),
    redis: aioredis.Redis = Depends(get_redis)
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")

    if await is_duplicate(redis, f"checkout-lock:{idempotency_key}"):
        raise HTTPException(status_code=409, detail="Request already being processed")

    order_event = OrderEvent(
        order_id=f"CHK-{uuid.uuid4().hex[:8]}",
        correlation_id=str(uuid.uuid4()),
        customer_id=payload.get("user_id", "anonymous"),
        total_amount=float(payload.get("amount", 0.0)),
        status=OrderStatus.CHECKOUT_INITIATED,
        payload={"source": "checkout_endpoint"}
    )

    try:
        await start_saga_flow(order_event)
        return {"status": "Checkout Saga Started", "id": idempotency_key}
    except Exception as e:
        logger.error(f"Failed to start checkout saga: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
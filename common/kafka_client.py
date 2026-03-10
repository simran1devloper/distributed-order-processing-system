import os
import io
import logging
import fastavro
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from typing import Optional, Any, Dict

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kafka-client")

# Environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

class KafkaManager:
    _producer: Optional[AIOKafkaProducer] = None
    _schema: Optional[Any] = None

    @classmethod
    def load_schema(cls):
        if cls._schema is None:
            schema_path = os.path.join(os.path.dirname(__file__), "schema/order.avsc")
            try:
                cls._schema = fastavro.schema.load_schema(schema_path)
                logger.info(f"Avro schema loaded from {schema_path}")
            except FileNotFoundError:
                logger.error(f"Avro schema file not found at {schema_path}")
        return cls._schema

    @classmethod
    def avro_serializer(cls, value: Any) -> bytes:
        if hasattr(value, "model_dump"):
            value = value.model_dump(mode='json')
        elif hasattr(value, "dict"):
            value = value.dict()
        
        if not isinstance(value, dict):
            return value
        
        schema = cls.load_schema()
        fo = io.BytesIO()
        fastavro.schemaless_writer(fo, schema, value)
        return fo.getvalue()

    @classmethod
    def avro_deserializer(cls, data: bytes) -> Optional[Dict]:
        if data is None:
            return None
        
        schema = cls.load_schema()
        fo = io.BytesIO(data)
        try:
            return fastavro.schemaless_reader(fo, schema)
        except Exception as e:
            logger.error(f"Avro deserialization failed: {e}")
            return None

    @classmethod
    async def get_producer(cls) -> AIOKafkaProducer:
        if cls._producer is None:
            logger.info("Starting AIOKafkaProducer WITHOUT retries...")
            cls._producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                acks="all",
                retry_backoff_ms=500,
                request_timeout_ms=30000,
                value_serializer=cls.avro_serializer
            )
            await cls._producer.start()
            logger.info("Kafka Producer started")
        return cls._producer

    @classmethod
    async def stop_producer(cls):
        if cls._producer is not None:
            await cls._producer.stop()
            cls._producer = None
            logger.info("Kafka Producer stopped")

# Legacy functional wrappers to maintain compatibility
async def get_producer() -> AIOKafkaProducer:
    return await KafkaManager.get_producer()

async def get_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        session_timeout_ms=30000,
        heartbeat_interval_ms=10000,
        value_deserializer=KafkaManager.avro_deserializer
    )
    await consumer.start()
    logger.info(f"Connected to topic: {topic} as group: {group_id}")
    return consumer
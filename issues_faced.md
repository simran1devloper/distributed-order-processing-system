# Issues Faced & Solutions

This document logs the critical issues encountered during the refactor and stabilization of the Saga Orchestrator, along with their respective resolutions.

## 1. Kafka Producer Configuration Error
**Issue**: `TypeError: AIOKafkaProducer.__init__() got an unexpected keyword argument 'retries'`
- **Cause**: The `aiokafka` library does not support a `retries` argument in the constructor; it's handled automatically or via other parameters.
- **Fix**: Removed `retries=5` from the `AIOKafkaProducer` initialization in `common/kafka_client.py`.

## 2. Modern Redis Asynchronous Support
**Issue**: `ModuleNotFoundError: No module named 'aioredis'` (or import errors with modern `redis`)
- **Cause**: The legacy `aioredis` package is now integrated into the main `redis` package as `redis.asyncio`.
- **Fix**: Updated `common/idempotency.py` and service `requirements.txt` to use `from redis import asyncio as aioredis` and the `redis` package.

## 3. Kafka Infrastructure Versioning (KRaft vs Zookeeper)
**Issue**: `KafkaConnectionError: Unable to bootstrap from kafka:29092` and DNS resolution failures.
- **Cause**: Using the `latest` tag for `confluentinc/cp-kafka` defaulted to KRaft mode (which requires specific `KAFKA_PROCESS_ROLES` variables), but our `docker-compose.yml` was configured for Zookeeper.
- **Fix**: Pinned Kafka and Zookeeper images to version `7.5.0` and corrected the `KAFKA_ADVERTISED_LISTENERS` to distinguish between internal and external traffic.

## 4. Avro Serialization: BufferedReader Error
**Issue**: `TypeError: expected str, bytes or os.PathLike object, not BufferedReader`
- **Cause**: `fastavro.schema.load_schema` was being passed an open file object (`with open(...) as f`) instead of the file path string.
- **Fix**: Updated `common/kafka_client.py` to pass the path string directly to `load_schema`.

## 5. Pydantic & Enum Serialization
**Issue**: Kafka messages failed to serialize due to Pydantic objects or Enum values being passed directly.
- **Cause**: Avro's `schemaless_writer` requires a dictionary with primitive types, but Pydantic models contain complex types.
- **Fix**: Improved `avro_serializer` in `common/kafka_client.py` to use `model_dump(mode='json')` which automatically converts Enums and UUIDs to strings.

## 6. Service Orchestration Race Conditions
**Issue**: Workers failing with "Connection Refused" while Kafka was still booting.
- **Cause**: Containers report as "Up" before the internal Kafka process is ready to accept connections.
- **Fix**: Added a robust `nc -z` healthcheck to the Kafka container and updated standard workers to use the `service_healthy` condition in `docker-compose.yml`.

## 7. Test Suite Inconsistency (Idempotency Status)
**Issue**: `testing_file.py` warned about 202 Accepted for duplicate checkout requests.
- **Cause**: The legacy `/checkout` endpoint returned a success status instead of a conflict code for duplicates.
- **Fix**: Updated `api/main.py` to raise an `HTTPException(status_code=409)` for duplicate requests, ensuring consistency with the `/order` endpoint.

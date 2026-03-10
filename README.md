# Saga Orchestrator

A robust, event-driven Saga Orchestrator built with FastAPI, Kafka (Avro), and Redis for idempotent distributed transactions.

## High-Level Design (HLD)

```mermaid
graph TD
    Client[Real-time Client]
    Nginx[Nginx Gateway]
    API["API Orchestrator (FastAPI)"]
    Redis[(Redis - Idempotency)]
    Kafka{Kafka - Event Bus}
    
    subgraph Workers
        Inventory[Inventory Worker]
        Payment[Payment Worker]
        Shipping[Shipping Worker]
    end

    Client -->|POST /order| Nginx
    Nginx --> API
    API -->|Check Duplicates| Redis
    API -->|Publish: order.created| Kafka
    
    Kafka -->|Consume| Inventory
    Inventory -->|Publish: inventory.success| Kafka
    
    Kafka -->|Consume| Payment
    Payment -->|Publish: payment.success| Kafka
    
    Kafka -->|Consume| Shipping
    Shipping -->|Finalize| Kafka
    
    Inventory & Payment & Shipping -->|Verify| Redis
```

## Key Features
- **Choreography-based Saga**: Decentralized transaction management using Kafka events.
- **Avro Serialization**: Efficient, schema-enforced messaging.
- **Idempotency**: Redis-backed request de-duplication across all layers.
- **Modern Infrastructure**: Containerized with health-checks and automated dependency orchestration.

## Getting Started

1. **Start the Infrastructure**:
   ```bash
   sudo docker-compose up -d --build
   ```

2. **Run Integration Tests**:
   ```bash
   python testing_file.py
   ```

## Stack
- **Backend**: FastAPI (Python 3.11)
- **Messaging**: Kafka (Confluent 7.5.0)
- **Serialization**: Avro (fastavro)
- **Storage**: Redis (Idempotency)
- **Observability**: Prometheus, Loki, Kafdrop

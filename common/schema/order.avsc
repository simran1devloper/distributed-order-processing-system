{
  "type": "record",
  "name": "OrderEvent",
  "namespace": "com.saga.order",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "correlation_id", "type": "string"},
    {"name": "customer_id", "type": "string"},
    {"name": "total_amount", "type": "double"},
    {"name": "status", "type": "string", "default": "PENDING"},
    {
      "name": "payload",
      "type": {
        "type": "map",
        "values": "string"
      },
      "default": {}
    }
  ]
}
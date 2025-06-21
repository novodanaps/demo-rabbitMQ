# Direct Exchange Example

## Overview
Direct exchange routes messages to queues based on exact routing key matching. This is perfect for point-to-point messaging where you want specific consumers to receive specific types of messages.

## How it works
- Producer sends messages with a specific routing key
- Exchange routes messages only to queues bound with the exact same routing key
- Multiple queues can be bound to the same routing key

## Running the Example

### Terminal 1 - Consumer for error messages
```bash
python consumer.py error
```

### Terminal 2 - Consumer for warning and info messages  
```bash
python consumer.py warning info
```

### Terminal 3 - Producer
```bash
# Send error message (only first consumer will receive)
python producer.py error "Database connection failed"

# Send warning message (only second consumer will receive)
python producer.py warning "Low disk space"

# Send info message (only second consumer will receive)  
python producer.py info "User logged in successfully"
```

## Use Cases
- Log message routing by severity level
- Task distribution to specific worker types
- Service-to-service communication with specific message types

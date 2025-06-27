# Direct Exchange Example with Retry Mechanism

## Overview
Direct exchange routes messages to queues based on exact routing key matching. This example includes an advanced retry mechanism with exponential backoff and dead letter queues for robust error handling.

## Features
- **Exact routing key matching** for point-to-point messaging
- **Automatic retry mechanism** with exponential backoff
- **Dead letter queue** for failed messages
- **Configurable retry attempts** and delays
- **Different error handling** for permanent vs temporary failures

## How it works
- Producer sends messages with a specific routing key
- Exchange routes messages only to queues bound with the exact same routing key
- Consumer processes messages with automatic retry on failures
- Failed messages are retried up to 3 times with increasing delays (1s, 2s, 4s)
- Messages exceeding retry limits are sent to dead letter queue

## Retry Configuration
- **Max retry attempts**: 3
- **Initial delay**: 1 second
- **Backoff multiplier**: 2 (exponential backoff)
- **Retry queues**: Temporary queues with TTL for delayed retries
- **Dead letter queue**: Permanent storage for failed messages

## Running the Example

### Terminal 1 - Consumer with retry functionality
```bash
python consumer.py error warning info
```

### Terminal 2 - Producer
```bash
# Send normal message (will process successfully)
python producer.py info "Normal processing message"

# Send temporary error (will retry 3 times then go to DLQ)
python producer.py warning "temporary_error test"

# Send permanent error (goes directly to DLQ)
python producer.py error "critical_error test"

# Send random failure test
python producer.py info "random_fail test"
```

### Terminal 3 - Test retry functionality
```bash
# Run comprehensive retry tests
python test_retry.py

# Monitor queue status
python monitor.py list

# View dead letter queue messages
python monitor.py dlq
```

## Error Types Handled

### Temporary Errors (Will Retry)
- Connection timeouts
- Network issues  
- Temporary service unavailability
- Random processing failures

### Permanent Errors (No Retry)
- Invalid data format
- Business logic violations
- Critical application errors
- JSON parsing errors

## Monitoring

### Queue Status
```bash
python monitor.py list
```

### Dead Letter Queue
```bash
python monitor.py dlq
```

## Message Flow

1. **Normal Processing**: Message → Process → Acknowledge → Done
2. **Temporary Failure**: Message → Fail → Retry Queue → Wait → Retry → Success/DLQ
3. **Permanent Failure**: Message → Fail → Dead Letter Queue → Done
4. **Max Retries Exceeded**: Message → Retry 3x → Dead Letter Queue → Done

## Use Cases
- **Log message routing** by severity level with failure recovery
- **Task distribution** to specific worker types with retry logic
- **Service-to-service communication** with robust error handling
- **Event processing** with guaranteed delivery or dead letter storage

# Fanout Exchange Example

## Overview
Fanout exchange broadcasts messages to all bound queues, completely ignoring the routing key. Every consumer connected to the exchange will receive every message.

## How it works
- Producer sends messages to fanout exchange
- Exchange copies the message to all bound queues
- All consumers receive every message
- Routing key is ignored

## Running the Example

### Terminal 1 - Email Service Consumer
```bash
python consumer.py "EmailService"
```

### Terminal 2 - SMS Service Consumer
```bash
python consumer.py "SMSService"
```

### Terminal 3 - Push Notification Consumer
```bash
python consumer.py "PushNotificationService"
```

### Terminal 4 - Producer
```bash
# All consumers will receive this message
python producer.py "New product launch announcement!"

# All consumers will receive this too
python producer.py "System maintenance scheduled for tonight"

# Every message goes to all consumers
python producer.py "Special discount available now!"
```

## Use Cases
- Broadcasting notifications to multiple services
- Real-time updates to multiple clients
- Event distribution to multiple systems
- Cache invalidation across multiple servers
- Live chat/messaging applications

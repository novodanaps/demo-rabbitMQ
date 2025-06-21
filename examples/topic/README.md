# Topic Exchange Example

## Overview
Topic exchange provides flexible routing using pattern matching on routing keys. It uses wildcards to match routing key patterns:
- `*` (star) - matches exactly one word
- `#` (hash) - matches zero or more words

## How it works
- Routing keys are dot-separated words (e.g., "auth.error.database")
- Consumers bind to patterns using wildcards
- Exchange routes messages to queues with matching patterns
- Very flexible for complex routing scenarios

## Routing Key Format
We use the format: `<facility>.<severity>.<source>`
- **facility**: auth, payment, user, order, etc.
- **severity**: info, warning, error, critical
- **source**: api, database, gateway, etc.

## Pattern Examples
- `*.error.*` - All error messages from any facility/source
- `auth.*` - All messages from auth facility
- `*.*.database` - All database-related messages
- `payment.#` - All payment-related messages (any severity/source)
- `#` - All messages (equivalent to fanout)

## Running the Example

### Terminal 1 - Error Monitor (all errors)
```bash
python consumer.py "*.error.*" "ErrorMonitor"
```

### Terminal 2 - Auth Service Monitor (all auth-related)
```bash
python consumer.py "auth.*" "AuthMonitor"  
```

### Terminal 3 - Critical Alert Handler (all critical messages)
```bash
python consumer.py "*.critical.*" "CriticalAlertHandler"
```

### Terminal 4 - Database Monitor (all database issues)
```bash
python consumer.py "*.*.database" "DatabaseMonitor"
```

### Terminal 5 - Payment System Monitor (all payment-related)
```bash
python consumer.py "payment.#" "PaymentMonitor"
```

### Terminal 6 - Producer (send various messages)
```bash
# This will go to ErrorMonitor and AuthMonitor
python producer.py "auth.error.database" "Authentication failed - database connection error"

# This will go to CriticalAlertHandler and PaymentMonitor  
python producer.py "payment.critical.gateway" "Payment gateway is down"

# This will go to AuthMonitor only
python producer.py "auth.info.api" "User successfully logged in"

# This will go to DatabaseMonitor only
python producer.py "user.warning.database" "Database query timeout"

# This will go to ErrorMonitor, DatabaseMonitor, and PaymentMonitor
python producer.py "payment.error.database" "Payment transaction failed - database error"
```

## Advanced Patterns

### Multiple Patterns Consumer
```bash
# Monitor both errors and critical messages
python consumer.py "*.error.*" "*.critical.*" "AlertSystem"
```

### Catch-All Consumer  
```bash
# Receive all messages (like fanout)
python consumer.py "#" "LogAggregator"
```

## Use Cases
- Log aggregation and filtering by severity/component
- Event routing in microservices architecture  
- Notification systems with complex routing rules
- Monitoring and alerting systems
- IoT device message routing by location/type
- Multi-tenant applications with tenant-specific routing

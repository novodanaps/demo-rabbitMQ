# RabbitMQ Exchange Examples

This project demonstrates the three main RabbitMQ exchange mechanisms with practical, ready-to-run examples:

## 🎯 Exchange Types Covered

### 1. **Direct Exchange** 
Routes messages to queues based on **exact routing key matching**
- **Use case**: Point-to-point messaging, log routing by severity
- **Example**: Error messages go only to error handlers

### 2. **Fanout Exchange**
**Broadcasts messages to ALL bound queues** (ignores routing key)
- **Use case**: Notifications, real-time updates, cache invalidation
- **Example**: Send announcement to email, SMS, and push notification services

### 3. **Topic Exchange**
Routes messages using **pattern matching** with wildcards
- **Use case**: Complex routing rules, microservices communication
- **Example**: `*.error.*` matches all error messages from any service

## 🚀 Quick Start

### Option 1: Interactive Demo (Recommended)
```bash
# Start RabbitMQ and run interactive demo
./start.sh
python demo.py
```

### Option 2: Manual Setup
```bash
# 1. Start RabbitMQ
cd settings && docker-compose up -d

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run examples (see individual READMEs)
cd examples/direct && python producer.py error "Database failed"
```

## 📁 Project Structure

```
├── demo.py                    # Interactive demo of all exchanges
├── start.sh                   # Quick start script
├── requirements.txt           # Python dependencies
├── examples/
│   ├── direct/               # Direct exchange examples
│   │   ├── producer.py       # Send messages with exact routing
│   │   ├── consumer.py       # Receive specific message types
│   │   └── README.md         # Detailed instructions
│   ├── fanout/               # Fanout exchange examples  
│   │   ├── producer.py       # Broadcast messages
│   │   ├── consumer.py       # Receive all broadcasts
│   │   └── README.md         # Detailed instructions
│   └── topic/                # Topic exchange examples
│       ├── producer.py       # Send with pattern-based routing
│       ├── consumer.py       # Subscribe to patterns
│       └── README.md         # Detailed instructions
└── settings/                 # Docker configuration
    ├── docker-compose.yml    # RabbitMQ server setup
    ├── dockerfile            # Custom RabbitMQ image
    └── init.sh              # Server initialization
```

## 🎮 Running Examples

Each example directory contains:
- **Producer**: Sends messages to the exchange
- **Consumer**: Receives messages from queues
- **README**: Detailed instructions and use cases

### Direct Exchange Example
```bash
cd examples/direct

# Terminal 1: Listen for errors
python consumer.py error

# Terminal 2: Send error message
python producer.py error "Database connection failed"
```

### Fanout Exchange Example  
```bash
cd examples/fanout

# Terminal 1: Email service
python consumer.py EmailService

# Terminal 2: SMS service  
python consumer.py SMSService

# Terminal 3: Broadcast message (both receive it)
python producer.py "New product launch!"
```

### Topic Exchange Example
```bash
cd examples/topic

# Terminal 1: Monitor all errors
python consumer.py "*.error.*" ErrorMonitor

# Terminal 2: Monitor auth system
python consumer.py "auth.*" AuthMonitor

# Terminal 3: Send auth error (both consumers receive it)
python producer.py "auth.error.database" "Auth DB connection failed"
```

## 🔧 Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.x**
- **pip** (for installing dependencies)

## 🌐 Management Interface

Access RabbitMQ Management UI at **http://localhost:15672**
- **Username**: `leon`
- **Password**: `dxt`

Use the UI to:
- Monitor queues and exchanges
- View message rates and statistics  
- Debug routing and bindings
- Manage users and permissions

## 💡 Learning Path

1. **Start here**: Run `python demo.py` for interactive overview
2. **Understand basics**: Read each exchange type's README
3. **Hands-on practice**: Run producer/consumer examples
4. **Experiment**: Modify routing keys and patterns
5. **Monitor**: Use Management UI to see what's happening
6. **Build**: Create your own messaging patterns

## 🎯 Real-World Use Cases

### Direct Exchange
- **Log routing**: route error/warning/info to different handlers
- **Task queues**: send tasks to specific worker types
- **Service communication**: point-to-point messaging

### Fanout Exchange  
- **Notifications**: broadcast to email, SMS, push services
- **Cache invalidation**: notify all cache servers
- **Real-time updates**: live chat, stock prices, sports scores

### Topic Exchange
- **Microservices**: complex routing in distributed systems
- **IoT platforms**: route sensor data by location/type
- **Multi-tenant apps**: route messages by tenant/feature
- **Monitoring systems**: flexible alerting rules

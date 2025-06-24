# RabbitMQ Demo - Complete Guide

This project provides comprehensive demonstrations of RabbitMQ features, from basic exchange patterns to advanced clustering capabilities.

## 🎯 What's Included

### 📡 **Exchange Patterns**
Master the three core RabbitMQ exchange types:

**1. Direct Exchange** - Exact routing key matching
- Point-to-point messaging, log routing by severity
- Example: Error messages go only to error handlers

**2. Fanout Exchange** - Broadcast to all queues
- Notifications, real-time updates, cache invalidation  
- Example: Send announcement to email, SMS, and push services

**3. Topic Exchange** - Pattern-based routing with wildcards
- Complex routing rules, microservices communication
- Example: `*.error.*` matches all error messages from any service

### 🏗️ **RabbitMQ Cluster**
Production-ready clustering with high availability:
- **3-Node Cluster** with automatic failover
- **HAProxy Load Balancer** for connection distribution
- **High Availability Queues** mirrored across nodes
- **Failover Testing** and recovery demonstrations

## 🚀 Quick Start

### Option 1: Complete Demo Suite (Recommended)
```bash
# Interactive menu with all demos
./run_demo.sh
```

### Option 2: Basic Exchange Demo
```bash
# Start RabbitMQ and run interactive demo
./start.sh
python demo.py
```

### Option 3: RabbitMQ Cluster Demo
```bash
# Start 3-node cluster with load balancer
cd cluster
./start_cluster.sh

# Run cluster demonstrations
python cluster_demo.py
```

### Option 4: Manual Setup
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
├── cluster/                   # RabbitMQ Cluster Demo
│   ├── docker-compose-cluster.yml  # 3-node cluster setup
│   ├── haproxy.cfg           # Load balancer configuration
│   ├── start_cluster.sh      # Start cluster script
│   ├── cluster_demo.py       # Interactive cluster demo
│   ├── producer.py           # Cluster-aware producer
│   ├── consumer.py           # HA consumer with failover
│   ├── failover_test.py      # Comprehensive failover testing
│   └── README.md             # Detailed cluster documentation
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

### For Beginners
1. **Start here**: Run `python demo.py` for interactive overview
2. **Understand basics**: Read each exchange type's README
3. **Hands-on practice**: Run producer/consumer examples
4. **Experiment**: Modify routing keys and patterns

### For Production Use
1. **Cluster setup**: Explore `cluster/` directory
2. **High availability**: Test failover scenarios
3. **Load balancing**: Monitor HAProxy distribution
4. **Monitoring**: Use management interfaces
5. **Build**: Create your own distributed messaging patterns

## 🏗️ Advanced Features

### RabbitMQ Cluster Benefits
- **High Availability**: Automatic failover when nodes fail
- **Load Distribution**: Even spread of connections and queues
- **Scalability**: Easy addition/removal of nodes
- **Data Persistence**: Messages survive node failures
- **Zero Downtime**: Rolling updates and maintenance

### Cluster Management
```bash
# Check cluster status
docker exec rabbitmq1 rabbitmqctl cluster_status

# View HA policies
docker exec rabbitmq1 rabbitmqctl list_policies

# Monitor queue mirroring
docker exec rabbitmq1 rabbitmqctl list_queues name slave_pids
```

### Access Points
- **Load Balanced Management**: http://localhost:15675
- **Individual Nodes**: http://localhost:15672-15674
- **HAProxy Stats**: http://localhost:8404
- **AMQP Load Balanced**: localhost:5675

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

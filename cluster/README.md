# RabbitMQ Cluster Demo

This directory contains a comprehensive demonstration of RabbitMQ clustering capabilities, showcasing high availability, load balancing, and failover scenarios.

## 🏗️ Architecture

### Cluster Components
- **3 RabbitMQ Nodes**: `rabbitmq1`, `rabbitmq2`, `rabbitmq3`
- **HAProxy Load Balancer**: Distributes connections across nodes
- **High Availability Policies**: Automatic queue mirroring across all nodes
- **Persistent Volumes**: Data persistence across container restarts

### Network Layout
```
┌─────────────────┐    ┌──────────────────────────────────┐
│   HAProxy LB    │    │         RabbitMQ Cluster         │
│   Port: 5675    │───▶│  Node1:5672  Node2:5673  Node3:5674 │
│   Port: 15675   │    │  Port:15672  Port:15673  Port:15674 │
└─────────────────┘    └──────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Start the Cluster
```bash
# Make scripts executable and start cluster
chmod +x start_cluster.sh
./start_cluster.sh
```

### 2. Verify Cluster Status
```bash
# Check cluster nodes
docker exec rabbitmq1 rabbitmqctl cluster_status

# Check HA policy
docker exec rabbitmq1 rabbitmqctl list_policies
```

### 3. Run Demos
```bash
# Interactive cluster demo
python cluster_demo.py

# Simple producer/consumer
python producer.py 20
python consumer.py

# Failover testing
python failover_test.py
```

## 🎯 Demo Scripts

### `cluster_demo.py`
Interactive demonstration of cluster features:
- **Load Balancing**: Send messages through HAProxy
- **HA Consumer**: Resilient message consumption
- **Failover Simulation**: Test node failure scenarios
- **Health Monitoring**: Check cluster and queue status

### `producer.py`
Simple message producer that:
- Connects via load balancer (port 5675)
- Sends persistent messages to HA queues
- Demonstrates connection resilience

### `consumer.py`
Resilient message consumer with:
- Automatic reconnection logic
- Graceful error handling
- Message acknowledgment patterns
- Load-balanced consumption

### `failover_test.py`
Comprehensive failover testing:
- Multi-node connection testing
- Message persistence verification
- Simulated node failures
- Recovery validation

## 🌐 Access Points

### Web Interfaces
- **Load Balanced Management**: http://localhost:15675
- **Node 1 Management**: http://localhost:15672
- **Node 2 Management**: http://localhost:15673
- **Node 3 Management**: http://localhost:15674
- **HAProxy Stats**: http://localhost:8404

**Credentials**: `admin` / `admin123`

### Connection Endpoints
- **Load Balanced AMQP**: `localhost:5675`
- **Direct Node Access**: `localhost:5672`, `localhost:5673`, `localhost:5674`

## 🔧 Configuration

### High Availability Policy
```bash
# Applied automatically by start_cluster.sh
rabbitmqctl set_policy ha-all ".*" '{"ha-mode":"all","ha-sync-mode":"automatic"}'
```

This policy ensures:
- All queues are mirrored across all nodes
- Automatic synchronization of queue contents
- Seamless failover when nodes go down

### HAProxy Configuration
- **Round-robin load balancing** for AMQP connections
- **Health checks** on all RabbitMQ nodes
- **Management UI load balancing**
- **Statistics interface** for monitoring

## 🧪 Testing Scenarios

### 1. Load Balancing Test
```bash
# Send messages through load balancer
python producer.py 100

# Monitor distribution in HAProxy stats
# http://localhost:8404
```

### 2. High Availability Test
```bash
# Start consumer
python consumer.py &

# Stop one node
docker stop rabbitmq2

# Send more messages - should still work
python producer.py 10

# Restart node
docker start rabbitmq2
```

### 3. Complete Failover Test
```bash
# Run comprehensive failover test
python failover_test.py
```

## 📊 Monitoring

### Cluster Status
```bash
# Check cluster membership
docker exec rabbitmq1 rabbitmqctl cluster_status

# Check queue status
docker exec rabbitmq1 rabbitmqctl list_queues name messages consumers policy

# Check node status
docker exec rabbitmq1 rabbitmqctl node_health_check
```

### Queue Mirroring
```bash
# Check which nodes have queue mirrors
docker exec rabbitmq1 rabbitmqctl list_queues name slave_pids synchronised_slave_pids
```

### Performance Metrics
- **HAProxy Stats**: http://localhost:8404
- **RabbitMQ Management**: Various node UIs
- **Connection Distribution**: Monitor in HAProxy statistics

## 🛠️ Troubleshooting

### Common Issues

1. **Nodes not joining cluster**
   ```bash
   # Check Erlang cookie consistency
   docker exec rabbitmq1 cat /var/lib/rabbitmq/.erlang.cookie
   docker exec rabbitmq2 cat /var/lib/rabbitmq/.erlang.cookie
   ```

2. **Connection failures**
   ```bash
   # Check node health
   docker exec rabbitmq1 rabbitmqctl status
   
   # Check ports
   netstat -tulpn | grep 567
   ```

3. **HA policy not applied**
   ```bash
   # Manually apply HA policy
   docker exec rabbitmq1 rabbitmqctl set_policy ha-all ".*" '{"ha-mode":"all"}'
   ```

### Logs
```bash
# Check container logs
docker logs rabbitmq1
docker logs haproxy

# Check RabbitMQ logs inside container
docker exec rabbitmq1 cat /var/log/rabbitmq/rabbit@rabbitmq1.log
```

## 🧹 Cleanup

```bash
# Stop and remove all containers
docker-compose -f docker-compose-cluster.yml down -v

# Remove volumes (WARNING: deletes all data)
docker volume prune
```

## 📚 Key Concepts Demonstrated

1. **Cluster Formation**: Automatic joining of nodes to form a cluster
2. **High Availability**: Queue mirroring across all nodes
3. **Load Balancing**: Even distribution of connections and load
4. **Failover**: Seamless handling of node failures
5. **Persistence**: Message durability across restarts and failures
6. **Monitoring**: Comprehensive cluster health monitoring
7. **Scalability**: Easy addition/removal of cluster nodes

This demo provides a production-like RabbitMQ cluster setup suitable for learning and testing distributed messaging patterns.

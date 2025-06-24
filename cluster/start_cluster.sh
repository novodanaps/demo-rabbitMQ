#!/bin/bash

echo "🚀 Starting RabbitMQ Cluster Demo..."

# Navigate to cluster directory
cd "$(dirname "$0")"

# Start the cluster
echo "📦 Starting RabbitMQ cluster with Docker Compose..."
docker-compose -f docker-compose-cluster.yml up -d

echo "⏳ Waiting for cluster to be ready..."
sleep 30

echo "🔧 Configuring High Availability policies..."

# Wait a bit more for all nodes to join
sleep 10

# Configure HA policies via any node
docker exec rabbitmq1 rabbitmqctl set_policy ha-all ".*" '{"ha-mode":"all","ha-sync-mode":"automatic"}'

echo "✅ RabbitMQ Cluster is ready!"
echo ""
echo "🌐 Access Points:"
echo "  • Load Balanced Management UI: http://localhost:15675 (admin/admin123)"
echo "  • Node 1 Management UI:       http://localhost:15672 (admin/admin123)"
echo "  • Node 2 Management UI:       http://localhost:15673 (admin/admin123)"  
echo "  • Node 3 Management UI:       http://localhost:15674 (admin/admin123)"
echo "  • HAProxy Stats:              http://localhost:8404 (admin/admin123)"
echo ""
echo "🔌 Connection Endpoints:"
echo "  • Load Balanced AMQP: localhost:5675"
echo "  • Node 1 AMQP:        localhost:5672"
echo "  • Node 2 AMQP:        localhost:5673"
echo "  • Node 3 AMQP:        localhost:5674"
echo ""
echo "📚 Run cluster demos:"
echo "  python cluster_demo.py"

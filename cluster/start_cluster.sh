#!/bin/bash

echo "🚀 Starting RabbitMQ Cluster Demo..."

# Navigate to cluster directory
cd "$(dirname "$0")"

# Stop any existing containers
echo "🧹 Cleaning up existing containers..."
sudo docker-compose -f docker-compose-cluster.yml down

# Start the cluster
echo "📦 Starting RabbitMQ cluster with Docker Compose..."
sudo docker-compose -f docker-compose-cluster.yml up -d

echo "⏳ Waiting for primary node to be ready..."
sleep 15

# Wait for rabbitmq1 to be fully ready
echo "🔍 Checking if primary node is ready..."
until sudo docker exec rabbitmq1 rabbitmqctl status > /dev/null 2>&1; do
    echo "   Waiting for rabbitmq1..."
    sleep 5
done

echo "✅ Primary node is ready!"

echo "🔗 Setting up cluster formation..."
sleep 5

# Join node 2 to cluster
echo "   Adding rabbitmq2 to cluster..."
sudo docker exec rabbitmq2 rabbitmqctl stop_app
sudo docker exec rabbitmq2 rabbitmqctl reset
sudo docker exec rabbitmq2 rabbitmqctl join_cluster rabbit@rabbitmq1
sudo docker exec rabbitmq2 rabbitmqctl start_app

# Join node 3 to cluster  
echo "   Adding rabbitmq3 to cluster..."
sudo docker exec rabbitmq3 rabbitmqctl stop_app
sudo docker exec rabbitmq3 rabbitmqctl reset
sudo docker exec rabbitmq3 rabbitmqctl join_cluster rabbit@rabbitmq1
sudo docker exec rabbitmq3 rabbitmqctl start_app

echo "🔧 Configuring High Availability policies..."
sleep 5

# Configure HA policies via primary node
sudo docker exec rabbitmq1 rabbitmqctl set_policy ha-all ".*" '{"ha-mode":"all","ha-sync-mode":"automatic"}'

echo "🔍 Verifying cluster status..."
sudo docker exec rabbitmq1 rabbitmqctl cluster_status

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

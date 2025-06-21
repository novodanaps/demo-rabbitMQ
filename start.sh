#!/bin/bash
# RabbitMQ Quick Start Script

echo "🐰 RabbitMQ Demo Setup"
echo "======================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start RabbitMQ
echo "🚀 Starting RabbitMQ server..."
cd settings
docker-compose up -d

# Wait for RabbitMQ to be ready
echo "⏳ Waiting for RabbitMQ to be ready..."
sleep 10

# Check if RabbitMQ is accessible
if curl -f -u leon:dxt http://localhost:15672/api/overview > /dev/null 2>&1; then
    echo "✅ RabbitMQ is running!"
    echo ""
    echo "📊 Management UI: http://localhost:15672"
    echo "   Username: leon"
    echo "   Password: dxt"
    echo ""
    echo "🎯 Quick Start Options:"
    echo "   1. Run interactive demo: python ../demo.py"
    echo "   2. Explore examples in ../examples/ directory"
    echo "   3. Install dependencies: pip install -r ../requirements.txt"
else
    echo "❌ RabbitMQ is not responding. Check the logs:"
    docker-compose logs rabbitmq
fi

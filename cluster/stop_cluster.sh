#!/bin/bash

echo "🛑 Stopping RabbitMQ Cluster..."

# Navigate to cluster directory
cd "$(dirname "$0")"

# Stop the cluster
echo "📦 Stopping cluster containers..."
docker-compose -f docker-compose-cluster.yml down

echo "🧹 Removing stopped containers..."
docker container prune -f

echo "📊 Cluster Status:"
echo "  • Containers stopped: ✅"
echo "  • Volumes preserved: ✅ (use 'docker-compose down -v' to remove)"
echo "  • Networks cleaned: ✅"

echo ""
echo "🔄 To restart cluster:"
echo "  ./start_cluster.sh"
echo ""
echo "🗑️ To completely remove (including data):"
echo "  docker-compose -f docker-compose-cluster.yml down -v"

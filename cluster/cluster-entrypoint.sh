#!/bin/bash
set -e

# Start RabbitMQ in the background
/usr/local/bin/docker-entrypoint.sh rabbitmq-server &

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ to start..."
until rabbitmqctl wait --timeout 60 /var/lib/rabbitmq/mnesia/rabbit@$(hostname).pid > /dev/null 2>&1; do
    echo "Waiting for RabbitMQ..."
    sleep 2
done

echo "RabbitMQ is ready"

# Enable management plugin
rabbitmq-plugins enable rabbitmq_management

# If this is not the first node, join the cluster
if [ "$(hostname)" != "rabbitmq1" ]; then
    echo "Joining cluster..."
    rabbitmqctl stop_app
    rabbitmqctl join_cluster rabbit@rabbitmq1
    rabbitmqctl start_app
    echo "Joined cluster successfully"
fi

# Wait for the background process
wait

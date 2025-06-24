#!/usr/bin/env python3
"""
RabbitMQ Cluster Producer - Demonstrates publishing to HA queues
"""

import pika
import json
import time
import sys
from datetime import datetime

def create_connection(host='localhost', port=5675):
    """Create connection to RabbitMQ cluster"""
    try:
        connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=pika.PlainCredentials('admin', 'admin123'),
            heartbeat=30
        )
        connection = pika.BlockingConnection(connection_params)
        return connection
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def setup_infrastructure(channel):
    """Setup exchange and queue"""
    # Declare exchange
    channel.exchange_declare(
        exchange='cluster_exchange',
        exchange_type='direct',
        durable=True
    )
    
    # Declare HA queue
    channel.queue_declare(
        queue='cluster_queue',
        durable=True,
        arguments={
            'x-message-ttl': 300000,  # 5 minutes TTL
        }
    )
    
    # Bind queue
    channel.queue_bind(
        exchange='cluster_exchange',
        queue='cluster_queue',
        routing_key='cluster_messages'
    )

def send_messages(channel, count=10):
    """Send messages to the cluster"""
    print(f"📤 Sending {count} messages to cluster...")
    
    for i in range(count):
        message = {
            'id': i,
            'timestamp': datetime.now().isoformat(),
            'message': f'Cluster message #{i}',
            'sender': 'cluster_producer'
        }
        
        channel.basic_publish(
            exchange='cluster_exchange',
            routing_key='cluster_messages',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent messages
                message_id=str(i),
                timestamp=int(time.time())
            )
        )
        
        print(f"✅ Sent message {i}")
        time.sleep(0.5)  # Small delay to see the process

def main():
    if len(sys.argv) > 1:
        try:
            message_count = int(sys.argv[1])
        except ValueError:
            message_count = 10
    else:
        message_count = 10
    
    print("🚀 RabbitMQ Cluster Producer")
    print(f"📊 Will send {message_count} messages")
    
    # Connect to load-balanced endpoint
    connection = create_connection()
    if not connection:
        print("❌ Failed to connect to cluster")
        return
    
    try:
        channel = connection.channel()
        setup_infrastructure(channel)
        send_messages(channel, message_count)
        print("✅ All messages sent successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        connection.close()
        print("🔌 Connection closed")

if __name__ == "__main__":
    main()

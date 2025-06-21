#!/usr/bin/env python3
"""
Fanout Exchange Producer
Broadcasts messages to all bound queues (ignores routing key)
"""
import pika
import sys
import json
from datetime import datetime

def connect_rabbitmq():
    """Establish connection to RabbitMQ server"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials('leon', 'dxt')
        )
    )
    return connection

def broadcast_message(message):
    """Broadcast message to all connected consumers via fanout exchange"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # Declare the fanout exchange
    exchange_name = 'broadcast_news'
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
    
    # Create message with metadata
    message_body = {
        'content': message,
        'timestamp': datetime.now().isoformat(),
        'broadcast_id': f"broadcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    # Publish message (routing_key is ignored in fanout)
    channel.basic_publish(
        exchange=exchange_name,
        routing_key='',  # Ignored for fanout
        body=json.dumps(message_body),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )
    
    print(f" [x] Broadcasted: {message}")
    connection.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python producer.py <message>")
        print("Example: python producer.py 'Breaking news: New product launch!'")
        sys.exit(1)
    
    message = ' '.join(sys.argv[1:])
    broadcast_message(message)

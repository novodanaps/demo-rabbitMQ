#!/usr/bin/env python3
"""
Topic Exchange Producer
Sends messages with routing keys that can be matched using patterns
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

def send_message(routing_key, message):
    """Send message to topic exchange with pattern-based routing key"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # Declare the topic exchange
    exchange_name = 'topic_logs'
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')
    
    # Create message with metadata
    message_body = {
        'content': message,
        'timestamp': datetime.now().isoformat(),
        'routing_key': routing_key,
        'source': 'topic_producer'
    }
    
    # Publish message
    channel.basic_publish(
        exchange=exchange_name,
        routing_key=routing_key,
        body=json.dumps(message_body),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )
    
    print(f" [x] Sent message with routing key '{routing_key}': {message}")
    connection.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python producer.py <routing_key> <message>")
        print("\nRouting key format: <facility>.<severity>.<source>")
        print("Examples:")
        print("  python producer.py 'auth.error.database' 'Authentication failed'")
        print("  python producer.py 'payment.warning.gateway' 'Gateway timeout'")
        print("  python producer.py 'user.info.api' 'New user registered'")
        print("  python producer.py 'order.critical.inventory' 'Stock depleted'")
        print("\nPattern examples for consumers:")
        print("  '*.error.*'     - All error messages")
        print("  'auth.*'        - All auth-related messages")
        print("  '*.*.database'  - All database-related messages")
        print("  '#'             - All messages")
        sys.exit(1)
    
    routing_key = sys.argv[1]
    message = ' '.join(sys.argv[2:])
    
    send_message(routing_key, message)

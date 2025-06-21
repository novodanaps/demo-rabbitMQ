#!/usr/bin/env python3
"""
Direct Exchange Consumer
Receives messages from specific routing keys
"""
import pika
import sys
import json

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

def callback(ch, method, properties, body):
    """Process received message"""
    try:
        message_data = json.loads(body)
        print(f" [x] Received [{method.routing_key}]: {message_data['content']}")
        print(f"     Timestamp: {message_data['timestamp']}")
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError:
        print(f" [x] Received invalid JSON: {body}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_messages(routing_keys):
    """Start consuming messages for specified routing keys"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # Declare the direct exchange
    exchange_name = 'direct_logs'
    channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
    
    # Create a unique queue for this consumer
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    
    # Bind queue to exchange for each routing key
    for routing_key in routing_keys:
        channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key=routing_key
        )
        print(f" [*] Binding queue to routing key: {routing_key}")
    
    # Set up consumer
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback
    )
    
    print(" [*] Waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python consumer.py <routing_key1> [routing_key2] ...")
        print("Example: python consumer.py error warning")
        print("Available routing keys: info, warning, error")
        sys.exit(1)
    
    routing_keys = sys.argv[1:]
    consume_messages(routing_keys)

#!/usr/bin/env python3
"""
Topic Exchange Consumer
Receives messages based on routing key patterns using wildcards
* (star) - matches exactly one word
# (hash) - matches zero or more words
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
        print(f" [x] Received message:")
        print(f"     Routing Key: {method.routing_key}")
        print(f"     Content: {message_data['content']}")
        print(f"     Timestamp: {message_data['timestamp']}")
        print(f"     Source: {message_data.get('source', 'unknown')}")
        print("-" * 60)
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError:
        print(f" [x] Received invalid JSON: {body}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_messages(binding_keys, consumer_name="TopicConsumer"):
    """Start consuming messages for specified binding key patterns"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # Declare the topic exchange
    exchange_name = 'topic_logs'
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')
    
    # Create a unique queue for this consumer
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    
    # Bind queue to exchange for each binding key pattern
    for binding_key in binding_keys:
        channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key=binding_key
        )
        print(f" [*] {consumer_name} bound to pattern: '{binding_key}'")
    
    # Set up consumer
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback
    )
    
    print(f" [*] {consumer_name} waiting for messages. To exit press CTRL+C")
    print(f" [*] Listening for patterns: {', '.join(binding_keys)}")
    print("-" * 60)
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python consumer.py <pattern1> [pattern2] ... [consumer_name]")
        print("\nPattern examples:")
        print("  '*.error.*'     - All error messages")
        print("  'auth.*'        - All auth-related messages")
        print("  '*.*.database'  - All database-related messages")
        print("  '#'             - All messages")
        print("  'payment.#'     - All payment-related messages")
        print("\nExamples:")
        print("  python consumer.py '*.error.*' 'ErrorHandler'")
        print("  python consumer.py 'auth.*' '*.critical.*' 'SecurityMonitor'")
        print("  python consumer.py '#' 'LogAggregator'")
        sys.exit(1)
    
    # Check if last argument is consumer name (doesn't contain wildcards)
    if len(sys.argv) > 2 and '*' not in sys.argv[-1] and '#' not in sys.argv[-1]:
        binding_keys = sys.argv[1:-1]
        consumer_name = sys.argv[-1]
    else:
        binding_keys = sys.argv[1:]
        consumer_name = "TopicConsumer"
    
    consume_messages(binding_keys, consumer_name)

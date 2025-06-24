#!/usr/bin/env python3
"""
Fanout Exchange Consumer
Receives all broadcasted messages regardless of routing key
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
    """Process received broadcast message"""
    try:
        message_data = json.loads(body)
        consumer_name = sys.argv[1] if len(sys.argv) > 1 else "Anonymous"
        
        print(f" [x] {consumer_name} received broadcast:")
        print(f"     Message: {message_data['content']}")
        print(f"     Broadcast ID: {message_data['broadcast_id']}")
        print(f"     Timestamp: {message_data['timestamp']}")
        print("-" * 50)
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError:
        print(f" [x] Received invalid JSON: {body}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consuming(consumer_name="Anonymous"):
    """Start consuming broadcast messages"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # Declare the fanout exchange
    exchange_name = 'broadcast_news'
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
    
    # Create a unique queue for this consumer
    # NOTE: If use queue='', RabbitMQ will create a unique queue for each consumer and when the consumer disconnects, the queue will be deleted. So message will not be lost.
    # CASE 1: 
    # result = channel.queue_declare(queue='', exclusive=True)
    # queue_name = result.method.queue
    
    # CASE 2:
    queue_name = f'{consumer_name}_queue'
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Bind queue to exchange (no routing key needed for fanout)
    channel.queue_bind(exchange=exchange_name, queue=queue_name)
    
    # Set up consumer
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback
    )
    
    print(f" [*] {consumer_name} waiting for broadcast messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

if __name__ == '__main__':
    consumer_name = sys.argv[1] if len(sys.argv) > 1 else "Anonymous"
    start_consuming(consumer_name)

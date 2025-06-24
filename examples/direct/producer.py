"""
Direct Exchange Producer
Sends messages to specific queues using exact routing key matching
Date: 2025-06-01
Author: Nguyen Hoai Nam
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

# TODO: Implement a callback function to handle responses
"""
import uuid
corr_id = str(uuid.uuid4())
def on_response(ch, method, props, body):
    # Check if the correlation_id of the response matches the one of the request
    if corr_id == props.correlation_id:
        # Store the response in a variable
        response = body
"""

def send_message(routing_key, message):
    """Send message to direct exchange with specific routing key"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # Declare the direct exchange
    exchange_name = 'direct_logs'
    channel.exchange_declare(exchange=exchange_name, exchange_type='direct')

    # TODO: Declare a queue to receive responses and subscribe to it
    """
    response_queue = channel.queue_declare(queue="", exclusive=True)
    channel.basic_consume(
        queue=response_queue.method.queue,
        on_message_callback=on_response,
        auto_ack=True,
    )
    """
    
    # Create message with metadata
    message_body = {
        'content': message,
        'timestamp': datetime.now().isoformat(),
        'routing_key': routing_key
    }
    
    # Publish message
    # NOTE: if you want send message when queue it not available, mandatory=True
    # will return message to the producer, but if you want to send message when queue is 
    channel.basic_publish(
        exchange=exchange_name,
        routing_key=routing_key,
        body=json.dumps(message_body),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )
    
    print(f" [x] Sent message to '{routing_key}': {message}")
    connection.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python producer.py <routing_key> <message>")
        print("Example: python producer.py error 'Database connection failed'")
        print("Available routing keys: info, warning, error")
        sys.exit(1)
    
    routing_key = sys.argv[1]
    message = ' '.join(sys.argv[2:])
    
    send_message(routing_key, message)

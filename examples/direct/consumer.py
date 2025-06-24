"""
Direct Exchange Consumer
Receives messages from specific routing keys
Date: 2025-06-01
Author: Nguyen Hoai Nam
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

        #TODO: If send message to another queue, use ch.basic_publish() here
        """
        ch.basic_publish(
            exchange='another_exchange',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id,
            ),
            body=json.dumps(message_data)
        )
        """

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
    # NOTE: If use queue='', RabbitMQ will create a unique queue for each consumer and when the consumer disconnects, the queue will be deleted. So message will not be lost.
    # CASE 1: 
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    
    # CASE 2:
    # queue_name = 'my_consumer_queue'
    # channel.queue_declare(queue=queue_name)

    # Bind queue to exchange for each routing key
    for routing_key in routing_keys:
        channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key=routing_key
        )
        print(f" [*] Binding queue to routing key: {routing_key}")
    
    # Set QoS to ensure fair dispatch
    channel.basic_qos(prefetch_count=1)

    # Set up consumer
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=False  # Disable auto-acknowledgment to manually acknowledge messages
    )
    
    print(" [*] Waiting for messages. To exit press CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()
auto_ack=True 
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python consumer.py <routing_key1> [routing_key2] ...")
        print("Example: python consumer.py error warning")
        print("Available routing keys: info, warning, error")
        sys.exit(1)
    
    routing_keys = sys.argv[1:]
    consume_messages(routing_keys)

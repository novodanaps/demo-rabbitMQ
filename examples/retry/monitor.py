#!/usr/bin/env python3
"""
Queue Monitor - Monitor retry and dead letter queues
"""

import pika
import json
import sys

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

def get_queue_info(channel, queue_name):
    """Get information about a queue"""
    try:
        method = channel.queue_declare(queue=queue_name, passive=True)
        return method.method.message_count
    except Exception:
        return None

def list_queues():
    """List all queues and their message counts"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # List of queues to check
    queues_to_check = [
        'dead_letter_queue',
        'retry_queue_1s',
        'retry_queue_2s',
        'retry_queue_4s',
        'retry_queue_8s',
    ]
    
    print("=== Queue Status ===")
    print(f"{'Queue Name':<20} {'Messages':<10}")
    print("-" * 35)
    
    for queue_name in queues_to_check:
        count = get_queue_info(channel, queue_name)
        if count is not None:
            print(f"{queue_name:<20} {count:<10}")
        else:
            print(f"{queue_name:<20} {'N/A':<10}")
    
    connection.close()

def consume_dead_letter_queue():
    """Consume and display messages from dead letter queue"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # Declare dead letter queue
    channel.exchange_declare(exchange='direct_logs_dlq', exchange_type='direct')
    channel.queue_declare(queue='dead_letter_queue', durable=True)
    
    def callback(ch, method, properties, body):
        try:
            message_data = json.loads(body)
            headers = properties.headers or {}
            
            print(f"\n=== Dead Letter Message ===")
            print(f"Content: {message_data.get('content', 'N/A')}")
            print(f"Original Routing Key: {headers.get('x-original-routing-key', 'N/A')}")
            print(f"Death Reason: {headers.get('x-death-reason', 'N/A')}")
            
            # Display both readable datetime and timestamp
            death_datetime = headers.get('x-death-datetime', 'N/A')
            death_timestamp = headers.get('x-death-timestamp', 'N/A')
            print(f"Death Time: {death_datetime} (timestamp: {death_timestamp})")
            print(f"Retry Count: {headers.get('x-retry-count', 0)}")
            print("=" * 30)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Error processing dead letter message: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
    
    # Check if there are messages
    method = channel.queue_declare(queue='dead_letter_queue', passive=True)
    message_count = method.method.message_count
    
    if message_count == 0:
        print("No messages in dead letter queue.")
        connection.close()
        return
    
    print(f"Found {message_count} messages in dead letter queue:")
    
    # Consume messages
    channel.basic_consume(
        queue='dead_letter_queue',
        on_message_callback=callback,
        auto_ack=False
    )
    
    print("Press CTRL+C to stop...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'dlq':
            consume_dead_letter_queue()
        elif sys.argv[1] == 'list':
            list_queues()
        else:
            print("Usage:")
            print("  python monitor.py list    - List queue statuses")
            print("  python monitor.py dlq     - Consume dead letter queue")
    else:
        list_queues()

if __name__ == '__main__':
    main()

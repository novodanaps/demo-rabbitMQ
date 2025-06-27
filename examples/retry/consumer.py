"""
Direct Exchange Consumer with Retry Mechanism
Receives messages from specific routing keys and retries on errors
Date: 2025-06-01
Author: Nguyen Hoai Nam
"""
import pika
import sys
import json
import time
import traceback
from typing import Dict, Any
from datetime import datetime

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 1  # seconds
BACKOFF_MULTIPLIER = 2

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

def process_message(message_data: Dict[str, Any]) -> bool:
    """
    Process the actual message logic.
    Returns True if successful, False if should retry, raises exception for permanent failures.
    """
    try:
        # Simulate processing that might fail
        content = message_data['content']
        
        # Example: simulate different types of failures based on content
        if 'critical_error' in content.lower():
            raise ValueError("Critical error - should not retry")
        elif 'temporary_error' in content.lower():
            # Simulate temporary error that should be retried
            raise ConnectionError("Temporary connection issue")
        elif 'random_fail' in content.lower():
            import random
            if random.random() < 0.5:  # 50% chance of failure
                raise RuntimeError("Random processing error")
        
        # Normal processing
        print(f" [✓] Successfully processed: {content}")
        return True
        
    except (ValueError, TypeError) as e:
        # Permanent errors - don't retry
        print(f" [!] Permanent error processing message: {e}")
        raise
    except Exception as e:
        # Temporary errors - can be retried
        print(f" [!] Temporary error processing message: {e}")
        return False

def get_retry_count(headers: Dict[str, Any]) -> int:
    """Extract retry count from message headers"""
    if headers and 'x-retry-count' in headers:
        return int(headers['x-retry-count'])
    return 0

def send_to_retry_queue(ch, method, properties, body, retry_count):
    """Send message to retry queue with delay"""
    try:
        # Check if channel is open
        if not ch.is_open:
            print(" [!] Channel is closed, cannot send to retry queue")
            return False
            
        exchange_name = 'direct_logs_retry'
        
        # Calculate delay based on retry count
        delay = INITIAL_RETRY_DELAY * (BACKOFF_MULTIPLIER ** retry_count)
        
        # Create headers if they don't exist - ensure all values are AMQP compatible
        headers = {}
        headers['x-retry-count'] = int(retry_count + 1)
        headers['x-original-routing-key'] = str(method.routing_key)
        headers['x-retry-delay'] = int(delay)  # Convert to integer for AMQP compatibility
        
        # Declare retry exchange and queue
        ch.exchange_declare(exchange=exchange_name, exchange_type='direct')
        
        # Create delayed queue using message TTL and dead letter exchange
        retry_queue_name = f"retry_queue_{int(delay)}s"
        ch.queue_declare(
            queue=retry_queue_name,
            durable=True,
            arguments={
                'x-message-ttl': int(delay * 1000),  # TTL in milliseconds
                'x-dead-letter-exchange': 'direct_logs',  # Send back to original exchange
                'x-dead-letter-routing-key': method.routing_key
            }
        )
        
        # Bind retry queue to retry exchange
        ch.queue_bind(exchange=exchange_name, queue=retry_queue_name, routing_key=method.routing_key)
        
        # Publish to retry queue
        ch.basic_publish(
            exchange=exchange_name,
            routing_key=method.routing_key,
            body=body,
            properties=pika.BasicProperties(
                headers=headers,
                delivery_mode=2,  # Make message persistent
                correlation_id=properties.correlation_id,
                reply_to=properties.reply_to
            )
        )
        
        print(f" [↻] Message sent to retry queue (attempt {retry_count + 1}/{MAX_RETRY_ATTEMPTS}) with {int(delay)}s delay")
        return True
        
    except Exception as retry_error:
        print(f" [!] Failed to send message to retry queue: {retry_error}")
        return False

def safe_ack(ch, delivery_tag):
    """Safely acknowledge a message, checking channel state first"""
    try:
        if ch.is_open:
            ch.basic_ack(delivery_tag=delivery_tag)
            return True
        else:
            print(" [!] Channel is closed, cannot acknowledge message")
            return False
    except Exception as ack_error:
        print(f" [!] Failed to acknowledge message: {ack_error}")
        return False

def send_to_dead_letter_queue(ch, method, properties, body, error_message):
    """Send message to dead letter queue after max retries"""
    try:
        # Check if channel is open
        if not ch.is_open:
            print(" [!] Channel is closed, cannot send to dead letter queue")
            print(f" [!] Lost message due to channel closure: {error_message}")
            return False
            
        exchange_name = 'direct_logs_dlq'
        queue_name = 'dead_letter_queue'
        
        # Declare dead letter exchange and queue
        ch.exchange_declare(exchange=exchange_name, exchange_type='direct')
        ch.queue_declare(queue=queue_name, durable=True)
        ch.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=method.routing_key)
        
        # Create headers with error information - ensure all values are AMQP compatible
        headers = {}
        headers['x-death-reason'] = str(error_message)[:1000]  # Limit length and ensure string
        headers['x-death-timestamp'] = int(time.time())  # Convert to integer for AMQP compatibility
        headers['x-death-datetime'] = datetime.now().isoformat()  # Human readable timestamp
        headers['x-original-routing-key'] = str(method.routing_key)
        
        # Add retry count if available from original headers
        if properties.headers and 'x-retry-count' in properties.headers:
            headers['x-retry-count'] = int(properties.headers['x-retry-count'])
        
        # Publish to dead letter queue
        ch.basic_publish(
            exchange=exchange_name,
            routing_key=method.routing_key,
            body=body,
            properties=pika.BasicProperties(
                headers=headers,
                delivery_mode=2,
                correlation_id=properties.correlation_id,
                reply_to=properties.reply_to
            )
        )
        
        print(f" [💀] Message sent to dead letter queue: {str(error_message)[:100]}...")
        return True
        
    except Exception as dlq_error:
        print(f" [!] Failed to send message to dead letter queue: {dlq_error}")
        print(f" [!] Original error was: {error_message}")
        # In production, you might want to log this to a file or external system
        return False

def callback(ch, method, properties, body):
    """Process received message with retry logic"""
    try:
        message_data = json.loads(body)
        retry_count = get_retry_count(properties.headers)
        
        print(f" [x] Received [{method.routing_key}]: {message_data['content']}")
        print(f"     Timestamp: {message_data['timestamp']}")
        if retry_count > 0:
            print(f"     Retry attempt: {retry_count}/{MAX_RETRY_ATTEMPTS}")
        
        try:
            # Process the message
            success = process_message(message_data)
            
            if success:
                # Message processed successfully
                safe_ack(ch, method.delivery_tag)
                print(f" [✓] Message acknowledged successfully")
            else:
                # Processing failed, check if we should retry
                if retry_count < MAX_RETRY_ATTEMPTS:
                    retry_success = send_to_retry_queue(ch, method, properties, body, retry_count)
                    if not retry_success:
                        # If retry queue failed, send to dead letter queue
                        send_to_dead_letter_queue(ch, method, properties, body, f"Retry queue failed after {retry_count} attempts")
                    safe_ack(ch, method.delivery_tag)
                else:
                    # Max retries exceeded
                    send_to_dead_letter_queue(ch, method, properties, body, "Max retry attempts exceeded")
                    safe_ack(ch, method.delivery_tag)
                    
        except Exception as permanent_error:
            # Permanent error - don't retry
            print(f" [!] Permanent error: {permanent_error}")
            send_to_dead_letter_queue(ch, method, properties, body, str(permanent_error))
            safe_ack(ch, method.delivery_tag)

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

    except json.JSONDecodeError as e:
        print(f" [x] Received invalid JSON: {body}")
        print(f"     JSON Error: {e}")
        # Send malformed JSON to dead letter queue
        send_to_dead_letter_queue(ch, method, properties, body, f"Invalid JSON: {str(e)}")
        safe_ack(ch, method.delivery_tag)
    except Exception as e:
        print(f" [!] Unexpected error in callback: {e}")
        print(f"     Traceback: {traceback.format_exc()}")
        # Send to dead letter queue for unexpected errors
        send_to_dead_letter_queue(ch, method, properties, body, f"Unexpected error: {str(e)}")
        safe_ack(ch, method.delivery_tag)

def consume_messages(routing_keys):
    """Start consuming messages for specified routing keys"""
    connection = connect_rabbitmq()
    channel = connection.channel()
    
    # Declare the direct exchange
    exchange_name = 'direct_logs'
    channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
    
    # Declare retry and dead letter exchanges
    channel.exchange_declare(exchange='direct_logs_retry', exchange_type='direct')
    channel.exchange_declare(exchange='direct_logs_dlq', exchange_type='direct')
    
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
    
    print(f" [*] Retry configuration: Max attempts={MAX_RETRY_ATTEMPTS}, Initial delay={INITIAL_RETRY_DELAY}s")
    print(" [*] Waiting for messages. To exit press CTRL+C")
    print(" [*] Legend: [✓] Success, [↻] Retry, [💀] Dead Letter, [!] Error")
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n [*] Stopping consumer...")
        try:
            channel.stop_consuming()
            connection.close()
        except Exception as cleanup_error:
            print(f" [!] Error during cleanup: {cleanup_error}")
    except Exception as consume_error:
        print(f" [!] Error during consumption: {consume_error}")
        print(f"     Traceback: {traceback.format_exc()}")
        try:
            connection.close()
        except Exception as close_error:
            print(f" [!] Error closing connection: {close_error}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python consumer.py <routing_key1> [routing_key2] ...")
        print("Example: python consumer.py error warning")
        print("Available routing keys: info, warning, error")
        print("Test messages:")
        print("  - Send 'critical_error' to test permanent failure")
        print("  - Send 'temporary_error' to test retry mechanism")
        print("  - Send 'random_fail' to test random failures")
        sys.exit(1)
    
    routing_keys = sys.argv[1:]
    consume_messages(routing_keys)

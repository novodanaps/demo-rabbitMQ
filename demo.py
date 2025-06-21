#!/usr/bin/env python3
"""
Complete RabbitMQ Exchange Demo
Demonstrates all three exchange types with interactive examples
"""
import pika
import json
import time
from datetime import datetime

def connect_rabbitmq():
    """Establish connection to RabbitMQ server"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('leon', 'dxt')
            )
        )
        return connection
    except pika.exceptions.AMQPConnectionError:
        print("❌ Failed to connect to RabbitMQ. Make sure the server is running:")
        print("   cd settings && docker-compose up -d")
        return None

def demo_direct_exchange():
    """Demonstrate Direct Exchange"""
    print("\n" + "="*60)
    print("🎯 DIRECT EXCHANGE DEMO")
    print("="*60)
    print("Direct exchange routes messages based on exact routing key matching")
    
    connection = connect_rabbitmq()
    if not connection:
        return
        
    channel = connection.channel()
    
    # Declare exchange and queues
    exchange_name = 'demo_direct'
    channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
    
    # Create queues for different log levels
    queues = ['error_queue', 'warning_queue', 'info_queue']
    routing_keys = ['error', 'warning', 'info']
    
    for queue, routing_key in zip(queues, routing_keys):
        channel.queue_declare(queue=queue, durable=True)
        channel.queue_bind(exchange=exchange_name, queue=queue, routing_key=routing_key)
    
    # Send sample messages
    messages = [
        ('error', 'Database connection failed'),
        ('warning', 'High memory usage detected'),
        ('info', 'User login successful'),
        ('error', 'API rate limit exceeded'),
    ]
    
    for routing_key, message in messages:
        message_body = {
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'level': routing_key
        }
        
        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(message_body)
        )
        print(f"📤 Sent [{routing_key}]: {message}")
    
    # Show queue contents
    print("\n📊 Queue Status:")
    for queue, routing_key in zip(queues, routing_keys):
        method = channel.queue_declare(queue=queue, passive=True)
        print(f"   {queue}: {method.method.message_count} messages")
    
    connection.close()
    print("✅ Direct exchange demo completed!")

def demo_fanout_exchange():
    """Demonstrate Fanout Exchange"""
    print("\n" + "="*60)
    print("📢 FANOUT EXCHANGE DEMO")
    print("="*60)
    print("Fanout exchange broadcasts messages to ALL bound queues")
    
    connection = connect_rabbitmq()
    if not connection:
        return
        
    channel = connection.channel()
    
    # Declare exchange and queues
    exchange_name = 'demo_fanout'
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
    
    # Create queues for different services
    services = ['email_service', 'sms_service', 'push_notification_service']
    
    for service in services:
        channel.queue_declare(queue=service, durable=True)
        channel.queue_bind(exchange=exchange_name, queue=service)
    
    # Send broadcast messages
    messages = [
        'New product launch announcement!',
        'System maintenance in 1 hour',
        'Special offer: 50% off today only!'
    ]
    
    for message in messages:
        message_body = {
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'broadcast_id': f"broadcast_{int(time.time())}"
        }
        
        channel.basic_publish(
            exchange=exchange_name,
            routing_key='',  # Ignored in fanout
            body=json.dumps(message_body)
        )
        print(f"📢 Broadcasted: {message}")
    
    # Show queue contents
    print("\n📊 Queue Status (all should have same message count):")
    for service in services:
        method = channel.queue_declare(queue=service, passive=True)
        print(f"   {service}: {method.method.message_count} messages")
    
    connection.close()
    print("✅ Fanout exchange demo completed!")

def demo_topic_exchange():
    """Demonstrate Topic Exchange"""
    print("\n" + "="*60)
    print("🔀 TOPIC EXCHANGE DEMO")
    print("="*60)
    print("Topic exchange routes messages using pattern matching")
    print("Patterns: * = one word, # = zero or more words")
    
    connection = connect_rabbitmq()
    if not connection:
        return
        
    channel = connection.channel()
    
    # Declare exchange
    exchange_name = 'demo_topic'
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')
    
    # Create queues with different binding patterns
    bindings = [
        ('all_errors', '*.error.*'),
        ('auth_messages', 'auth.*'),
        ('database_issues', '*.*.database'),
        ('critical_alerts', '*.critical.*'),
        ('payment_logs', 'payment.#')
    ]
    
    for queue_name, pattern in bindings:
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=pattern)
        print(f"🔗 Created queue '{queue_name}' with pattern '{pattern}'")
    
    # Send messages with different routing keys
    messages = [
        ('auth.error.database', 'Authentication failed - database error'),
        ('payment.critical.gateway', 'Payment gateway is down'),
        ('user.info.api', 'User registration successful'),
        ('auth.warning.api', 'Multiple failed login attempts'),
        ('payment.error.database', 'Transaction rollback failed'),
        ('order.critical.inventory', 'Critical stock level reached'),
    ]
    
    print(f"\n📤 Sending messages:")
    for routing_key, message in messages:
        message_body = {
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'routing_key': routing_key
        }
        
        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(message_body)
        )
        print(f"   [{routing_key}]: {message}")
    
    # Show which queues received messages
    print(f"\n📊 Queue Status:")
    for queue_name, pattern in bindings:
        method = channel.queue_declare(queue=queue_name, passive=True)
        count = method.method.message_count
        print(f"   {queue_name} (pattern: {pattern}): {count} messages")
    
    connection.close()
    print("✅ Topic exchange demo completed!")

def cleanup_demo_resources():
    """Clean up demo queues and exchanges"""
    print("\n🧹 Cleaning up demo resources...")
    connection = connect_rabbitmq()
    if not connection:
        return
        
    channel = connection.channel()
    
    # Delete demo exchanges
    exchanges = ['demo_direct', 'demo_fanout', 'demo_topic']
    for exchange in exchanges:
        try:
            channel.exchange_delete(exchange=exchange)
            print(f"   Deleted exchange: {exchange}")
        except:
            pass
    
    # Delete demo queues
    queues = [
        'error_queue', 'warning_queue', 'info_queue',
        'email_service', 'sms_service', 'push_notification_service',
        'all_errors', 'auth_messages', 'database_issues', 'critical_alerts', 'payment_logs'
    ]
    
    for queue in queues:
        try:
            channel.queue_delete(queue=queue)
            print(f"   Deleted queue: {queue}")
        except:
            pass
    
    connection.close()
    print("✅ Cleanup completed!")

def main():
    """Run the complete demo"""
    print("🐰 RabbitMQ Exchange Types Demo")
    print("This demo will show you how the 3 main exchange types work")
    print("\nMake sure RabbitMQ is running: cd settings && docker-compose up -d")
    
    input("\n📍 Press Enter to start the demo...")
    
    # Run demos
    demo_direct_exchange()
    input("\n📍 Press Enter to continue to Fanout demo...")
    
    demo_fanout_exchange()
    input("\n📍 Press Enter to continue to Topic demo...")
    
    demo_topic_exchange()
    
    print("\n" + "="*60)
    print("🎉 ALL DEMOS COMPLETED!")
    print("="*60)
    print("\nWhat you learned:")
    print("🎯 Direct Exchange: Exact routing key matching")
    print("📢 Fanout Exchange: Broadcast to all queues")
    print("🔀 Topic Exchange: Pattern-based routing with wildcards")
    
    print(f"\n💡 Next steps:")
    print("- Explore the examples in each directory")
    print("- Run producers and consumers manually")
    print("- Check RabbitMQ Management UI: http://localhost:15672")
    print("- Experiment with your own routing patterns")
    
    cleanup_choice = input("\n🧹 Clean up demo resources? (y/N): ")
    if cleanup_choice.lower() == 'y':
        cleanup_demo_resources()
    
    print("\n👋 Demo finished! Happy messaging!")

if __name__ == '__main__':
    main()

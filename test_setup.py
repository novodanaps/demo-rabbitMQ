#!/usr/bin/env python3
"""
Test script to verify RabbitMQ connection and basic functionality
"""
import pika
import sys

def test_connection():
    """Test basic connection to RabbitMQ"""
    print("🔌 Testing RabbitMQ connection...")
    
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('leon', 'dxt')
            )
        )
        channel = connection.channel()
        
        print("✅ Successfully connected to RabbitMQ!")
        
        # Test basic operations
        test_queue = 'test_connection_queue'
        channel.queue_declare(queue=test_queue, durable=False)
        channel.basic_publish(
            exchange='',
            routing_key=test_queue,
            body='Hello RabbitMQ!'
        )
        
        # Get the message back
        method_frame, header_frame, body = channel.basic_get(queue=test_queue)
        if method_frame:
            channel.basic_ack(method_frame.delivery_tag)
            print(f"✅ Message test successful: {body.decode()}")
        else:
            print("❌ Failed to retrieve test message")
            return False
        
        # Cleanup
        channel.queue_delete(queue=test_queue)
        connection.close()
        
        print("✅ All tests passed! RabbitMQ is ready for the examples.")
        return True
        
    except pika.exceptions.AMQPConnectionError:
        print("❌ Failed to connect to RabbitMQ!")
        print("   Make sure RabbitMQ is running:")
        print("   cd settings && docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_docker():
    """Check if Docker containers are running"""
    import subprocess
    
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=rabbit-server', '--format', '{{.Status}}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and 'Up' in result.stdout:
            print("🐳 Docker container 'rabbit-server' is running")
            return True
        else:
            print("🐳 Docker container 'rabbit-server' is not running")
            print("   Start it with: cd settings && docker-compose up -d")
            return False
            
    except FileNotFoundError:
        print("🐳 Docker not found. Please install Docker.")
        return False

def main():
    """Run all tests"""
    print("🧪 RabbitMQ Setup Test")
    print("=" * 30)
    
    # Check Docker first
    if not check_docker():
        sys.exit(1)
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    print("\n🎉 Setup verification complete!")
    print("You can now run the examples:")
    print("  python demo.py                    # Interactive demo")
    print("  cd examples/direct && python producer.py error 'test'")

if __name__ == '__main__':
    main()

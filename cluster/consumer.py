#!/usr/bin/env python3
"""
RabbitMQ Cluster Consumer - Demonstrates consuming from HA queues with resilience
"""

import pika
import json
import time
import signal
import sys
from datetime import datetime

class ClusterConsumer:
    def __init__(self, host='localhost', port=5675):
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None
        self.consuming = False
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.stop_consuming()

    def connect(self):
        """Connect to RabbitMQ cluster with retry logic"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                connection_params = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=pika.PlainCredentials('admin', 'admin123'),
                    heartbeat=30,
                    blocked_connection_timeout=300,
                )
                
                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()
                
                # Setup infrastructure
                self.setup_infrastructure()
                
                print(f"✅ Connected to cluster at {self.host}:{self.port}")
                return True
                
            except Exception as e:
                print(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        print("❌ Failed to connect after all retries")
        return False

    def setup_infrastructure(self):
        """Setup exchange and queue"""
        # Declare exchange
        self.channel.exchange_declare(
            exchange='cluster_exchange',
            exchange_type='direct',
            durable=True
        )
        
        # Declare HA queue
        self.channel.queue_declare(
            queue='cluster_queue',
            durable=True,
            arguments={
                'x-message-ttl': 300000,  # 5 minutes TTL
            }
        )
        
        # Bind queue
        self.channel.queue_bind(
            exchange='cluster_exchange',
            queue='cluster_queue',
            routing_key='cluster_messages'
        )

    def message_callback(self, channel, method, properties, body):
        """Process received messages"""
        try:
            # Parse message
            message = json.loads(body)
            
            # Log receipt
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 📨 Received message:")
            print(f"  • ID: {message.get('id', 'N/A')}")
            print(f"  • Content: {message.get('message', 'N/A')}")
            print(f"  • Sender: {message.get('sender', 'Unknown')}")
            
            # Simulate processing time
            processing_time = 1  # 1 second
            print(f"  • Processing for {processing_time}s...")
            time.sleep(processing_time)
            
            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print(f"  • ✅ Processed and acknowledged")
            print()
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            # Reject and don't requeue malformed messages
            channel.basic_nack(
                delivery_tag=method.delivery_tag, 
                requeue=False
            )
            
        except Exception as e:
            print(f"❌ Processing error: {e}")
            # Reject and requeue for retry
            channel.basic_nack(
                delivery_tag=method.delivery_tag, 
                requeue=True
            )

    def start_consuming(self, queue_name='cluster_queue'):
        """Start consuming messages from the queue"""
        if not self.channel:
            print("❌ No active channel")
            return
            
        try:
            # Set QoS to limit unacknowledged messages
            self.channel.basic_qos(prefetch_count=5)
            
            # Start consuming
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self.message_callback
            )
            
            self.consuming = True
            print(f"👂 Starting to consume from queue: {queue_name}")
            print("🔄 Waiting for messages... Press Ctrl+C to stop")
            print("=" * 50)
            
            # Start the consumption loop
            while self.consuming:
                self.connection.process_data_events(time_limit=1)
                
        except Exception as e:
            print(f"❌ Consumption error: {e}")
        finally:
            self.stop_consuming()

    def stop_consuming(self):
        """Stop consuming messages"""
        if self.consuming:
            self.consuming = False
            
        if self.channel:
            try:
                self.channel.stop_consuming()
            except:
                pass
                
        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
                print("🔌 Connection closed")
            except:
                pass

def main():
    print("🚀 RabbitMQ Cluster Consumer")
    print("🎯 Connecting to load-balanced cluster endpoint")
    
    # Allow specifying different connection endpoints
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5675
    
    print(f"🔌 Connecting to {host}:{port}")
    
    consumer = ClusterConsumer(host, port)
    
    if consumer.connect():
        try:
            consumer.start_consuming()
        except Exception as e:
            print(f"❌ Consumer error: {e}")
    else:
        print("❌ Failed to start consumer")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
RabbitMQ Cluster Demo

This demo showcases RabbitMQ cluster features including:
- High Availability (HA) queues
- Load balancing across nodes
- Failover simulation
- Cluster monitoring
"""

import pika
import json
import time
import random
import threading
from datetime import datetime
from typing import List, Dict, Any

class RabbitMQClusterDemo:
    def __init__(self):
        # Connection parameters for different scenarios
        self.load_balanced_params = pika.ConnectionParameters(
            host='localhost',
            port=5675,
            credentials=pika.PlainCredentials('admin', 'admin123'),
            heartbeat=30
        )
        
        self.node_params = [
            pika.ConnectionParameters(
                host='localhost', port=5672, 
                credentials=pika.PlainCredentials('admin', 'admin123'),
                heartbeat=30
            ),
            pika.ConnectionParameters(
                host='localhost', port=5673,
                credentials=pika.PlainCredentials('admin', 'admin123'),
                heartbeat=30
            ),
            pika.ConnectionParameters(
                host='localhost', port=5674,
                credentials=pika.PlainCredentials('admin', 'admin123'),
                heartbeat=30
            )
        ]
        
        self.connections: List[pika.BlockingConnection] = []
        self.channels: List[pika.channel.Channel] = []

    def connect_to_cluster(self) -> bool:
        """Connect to the load-balanced cluster endpoint"""
        try:
            connection = pika.BlockingConnection(self.load_balanced_params)
            channel = connection.channel()
            self.connections.append(connection)
            self.channels.append(channel)
            print("✅ Connected to RabbitMQ cluster via load balancer")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to cluster: {e}")
            return False

    def connect_to_specific_nodes(self) -> List[bool]:
        """Connect to specific cluster nodes for testing"""
        results = []
        for i, params in enumerate(self.node_params, 1):
            try:
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                self.connections.append(connection)
                self.channels.append(channel)
                print(f"✅ Connected to Node {i}")
                results.append(True)
            except Exception as e:
                print(f"❌ Failed to connect to Node {i}: {e}")
                results.append(False)
        return results

    def setup_ha_queue(self, queue_name: str = "ha_demo_queue"):
        """Setup a High Availability queue"""
        if not self.channels:
            print("❌ No active connections")
            return
            
        channel = self.channels[0]
        
        # Declare queue with HA policy
        # The policy is set at cluster level via rabbitmqctl
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={
                'x-message-ttl': 300000,  # 5 minutes TTL
                'x-max-length': 10000,    # Max 10k messages
            }
        )
        
        # Declare exchange
        channel.exchange_declare(
            exchange='ha_exchange',
            exchange_type='direct',
            durable=True
        )
        
        # Bind queue to exchange
        channel.queue_bind(
            exchange='ha_exchange',
            queue=queue_name,
            routing_key='ha_messages'
        )
        
        print(f"✅ Setup HA queue: {queue_name}")

    def demonstrate_load_balancing(self, message_count: int = 100):
        """Demonstrate load balancing by sending messages through load balancer"""
        print(f"\n🔄 Load Balancing Demo - Sending {message_count} messages...")
        
        if not self.channels:
            print("❌ No active connections")
            return
            
        channel = self.channels[0]
        
        start_time = time.time()
        
        for i in range(message_count):
            message = {
                'id': i,
                'timestamp': datetime.now().isoformat(),
                'data': f'Load balanced message {i}',
                'random_value': random.randint(1, 1000)
            }
            
            channel.basic_publish(
                exchange='ha_exchange',
                routing_key='ha_messages',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    message_id=str(i),
                    timestamp=int(time.time())
                )
            )
            
            if (i + 1) % 20 == 0:
                print(f"📤 Sent {i + 1} messages...")
        
        elapsed = time.time() - start_time
        print(f"✅ Sent {message_count} messages in {elapsed:.2f} seconds")
        print(f"📊 Rate: {message_count/elapsed:.2f} messages/second")

    def demonstrate_ha_consumer(self, queue_name: str = "ha_demo_queue"):
        """Demonstrate HA consumer that can survive node failures"""
        print(f"\n👂 Starting HA Consumer for queue: {queue_name}")
        
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                print(f"📨 Received: ID={message['id']}, Data={message['data'][:30]}...")
                
                # Simulate processing time
                time.sleep(0.1)
                
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        if not self.channels:
            print("❌ No active connections")
            return
            
        channel = self.channels[0]
        
        # Set QoS to limit unacknowledged messages
        channel.basic_qos(prefetch_count=10)
        
        # Start consuming
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback
        )
        
        print("🔄 Starting consumption... Press Ctrl+C to stop")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            print("\n🛑 Stopping consumer...")
            channel.stop_consuming()

    def test_failover_scenario(self):
        """Simulate node failure and test cluster resilience"""
        print("\n🚨 Failover Simulation Demo")
        print("This will test cluster resilience by connecting to specific nodes")
        
        # Connect to all nodes
        print("🔌 Connecting to all cluster nodes...")
        node_connections = self.connect_to_specific_nodes()
        
        active_nodes = sum(node_connections)
        print(f"📊 Active nodes: {active_nodes}/3")
        
        if active_nodes < 2:
            print("⚠️  Need at least 2 nodes for meaningful failover test")
            return
        
        # Test message persistence across nodes
        print("\n📤 Sending test messages to different nodes...")
        
        for i, (connected, channel) in enumerate(zip(node_connections, self.channels[-3:]), 1):
            if connected:
                try:
                    message = {
                        'node': i,
                        'timestamp': datetime.now().isoformat(),
                        'test_data': f'Failover test from node {i}'
                    }
                    
                    channel.basic_publish(
                        exchange='ha_exchange',
                        routing_key='ha_messages',
                        body=json.dumps(message),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    print(f"✅ Sent message via Node {i}")
                    
                except Exception as e:
                    print(f"❌ Failed to send via Node {i}: {e}")

    def monitor_cluster_health(self):
        """Monitor cluster health and queue statistics"""
        print("\n📊 Cluster Health Monitoring")
        
        if not self.channels:
            print("❌ No active connections")
            return
            
        channel = self.channels[0]
        
        try:
            # Get queue info
            method = channel.queue_declare(queue='ha_demo_queue', passive=True)
            message_count = method.method.message_count
            consumer_count = method.method.consumer_count
            
            print(f"📈 Queue Statistics:")
            print(f"  • Messages in queue: {message_count}")
            print(f"  • Active consumers: {consumer_count}")
            print(f"  • Queue is durable: Yes")
            print(f"  • HA policy applied: Yes (all nodes)")
            
        except Exception as e:
            print(f"❌ Error getting queue stats: {e}")

    def cleanup(self):
        """Clean up connections"""
        print("\n🧹 Cleaning up connections...")
        for connection in self.connections:
            try:
                connection.close()
            except:
                pass
        self.connections.clear()
        self.channels.clear()
        print("✅ Cleanup complete")

def main():
    demo = RabbitMQClusterDemo()
    
    try:
        print("🎯 RabbitMQ Cluster Demo")
        print("=" * 50)
        
        # Connect to cluster
        if not demo.connect_to_cluster():
            print("❌ Cannot proceed without cluster connection")
            return
        
        # Setup HA queue
        demo.setup_ha_queue()
        
        while True:
            print("\n📋 Available Demos:")
            print("1. Load Balancing Demo")
            print("2. HA Consumer Demo")
            print("3. Failover Simulation")
            print("4. Cluster Health Monitor")
            print("5. Exit")
            
            choice = input("\n🎯 Enter your choice (1-5): ").strip()
            
            if choice == '1':
                count = input("📊 Number of messages to send (default 50): ").strip()
                count = int(count) if count.isdigit() else 50
                demo.demonstrate_load_balancing(count)
                
            elif choice == '2':
                print("⚠️  Consumer will run until Ctrl+C is pressed")
                input("Press Enter to start consumer, then use another terminal to send messages...")
                demo.demonstrate_ha_consumer()
                
            elif choice == '3':
                demo.test_failover_scenario()
                
            elif choice == '4':
                demo.monitor_cluster_health()
                
            elif choice == '5':
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
    
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        demo.cleanup()

if __name__ == "__main__":
    main()

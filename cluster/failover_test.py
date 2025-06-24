#!/usr/bin/env python3
"""
RabbitMQ Cluster Failover Test

This script demonstrates cluster resilience by:
1. Connecting to multiple nodes
2. Sending messages through different nodes
3. Simulating node failures
4. Testing message persistence and recovery
"""

import pika
import json
import time
import threading
import random
from datetime import datetime
from typing import List, Optional

class FailoverTester:
    def __init__(self):
        self.node_configs = [
            {'host': 'localhost', 'port': 5672, 'name': 'Node1'},
            {'host': 'localhost', 'port': 5673, 'name': 'Node2'},  
            {'host': 'localhost', 'port': 5674, 'name': 'Node3'},
        ]
        
        self.load_balancer_config = {
            'host': 'localhost', 
            'port': 5675, 
            'name': 'LoadBalancer'
        }
        
        self.connections = {}
        self.channels = {}
        self.active_nodes = set()

    def create_connection(self, config):
        """Create connection to a specific node"""
        try:
            connection_params = pika.ConnectionParameters(
                host=config['host'],
                port=config['port'],
                credentials=pika.PlainCredentials('admin', 'admin123'),
                heartbeat=30,
                connection_attempts=3,
                retry_delay=1,
                socket_timeout=5
            )
            
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            
            # Setup infrastructure
            self.setup_infrastructure(channel)
            
            return connection, channel
            
        except Exception as e:
            print(f"❌ Failed to connect to {config['name']}: {e}")
            return None, None

    def setup_infrastructure(self, channel):
        """Setup exchanges and queues"""
        # Exchange for testing
        channel.exchange_declare(
            exchange='failover_test',
            exchange_type='direct',
            durable=True
        )
        
        # HA Queue for testing
        channel.queue_declare(
            queue='failover_queue',
            durable=True,
            arguments={
                'x-message-ttl': 600000,  # 10 minutes
            }
        )
        
        # Bind queue
        channel.queue_bind(
            exchange='failover_test',
            queue='failover_queue',
            routing_key='test_messages'
        )

    def test_all_connections(self):
        """Test connections to all nodes"""
        print("🔌 Testing connections to all cluster nodes...")
        
        # Test load balancer
        lb_conn, lb_channel = self.create_connection(self.load_balancer_config)
        if lb_conn:
            self.connections['LoadBalancer'] = lb_conn
            self.channels['LoadBalancer'] = lb_channel
            self.active_nodes.add('LoadBalancer')
            print("✅ Load Balancer: Connected")
        else:
            print("❌ Load Balancer: Failed")
        
        # Test individual nodes
        for config in self.node_configs:
            conn, channel = self.create_connection(config)
            if conn:
                self.connections[config['name']] = conn
                self.channels[config['name']] = channel
                self.active_nodes.add(config['name'])
                print(f"✅ {config['name']}: Connected")
            else:
                print(f"❌ {config['name']}: Failed")
        
        print(f"\n📊 Active connections: {len(self.active_nodes)}")
        return len(self.active_nodes) > 0

    def send_test_messages(self, node_name: str, count: int = 10):
        """Send test messages through a specific node"""
        if node_name not in self.channels:
            print(f"❌ No channel for {node_name}")
            return False
            
        channel = self.channels[node_name]
        
        print(f"📤 Sending {count} messages via {node_name}...")
        
        try:
            for i in range(count):
                message = {
                    'id': f"{node_name}_{i}",
                    'timestamp': datetime.now().isoformat(),
                    'sender_node': node_name,
                    'message': f'Test message {i} from {node_name}',
                    'test_data': random.randint(1, 1000)
                }
                
                channel.basic_publish(
                    exchange='failover_test',
                    routing_key='test_messages',
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent
                        message_id=message['id'],
                        timestamp=int(time.time())
                    )
                )
                
                if (i + 1) % 5 == 0:
                    print(f"  📨 Sent {i + 1}/{count} messages")
                    
            print(f"✅ Successfully sent {count} messages via {node_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send messages via {node_name}: {e}")
            return False

    def simulate_node_failure(self, node_name: str):
        """Simulate node failure by closing connection"""
        if node_name not in self.connections:
            print(f"⚠️  {node_name} not connected")
            return
            
        try:
            self.connections[node_name].close()
            del self.connections[node_name]
            del self.channels[node_name]
            self.active_nodes.discard(node_name)
            print(f"💥 Simulated failure of {node_name}")
            
        except Exception as e:
            print(f"❌ Error simulating failure of {node_name}: {e}")

    def test_message_persistence(self):
        """Test that messages persist across node failures"""
        print("\n🧪 Testing Message Persistence...")
        
        # Send messages through different nodes
        message_counts = {}
        for node in list(self.active_nodes):
            if node != 'LoadBalancer':  # Skip load balancer for this test
                count = 5
                if self.send_test_messages(node, count):
                    message_counts[node] = count
        
        total_sent = sum(message_counts.values())
        print(f"📊 Total messages sent: {total_sent}")
        
        # Check queue depth
        time.sleep(2)  # Allow messages to settle
        if 'LoadBalancer' in self.channels:
            try:
                method = self.channels['LoadBalancer'].queue_declare(
                    queue='failover_queue', 
                    passive=True
                )
                queue_depth = method.method.message_count
                print(f"📈 Current queue depth: {queue_depth}")
                
                if queue_depth >= total_sent:
                    print("✅ All messages persisted in queue")
                else:
                    print(f"⚠️  Expected {total_sent}, found {queue_depth}")
                    
            except Exception as e:
                print(f"❌ Error checking queue depth: {e}")

    def test_failover_recovery(self):
        """Test recovery after simulated failures"""
        print("\n🔄 Testing Failover Recovery...")
        
        if len(self.active_nodes) < 2:
            print("⚠️  Need at least 2 active nodes for failover test")
            return
            
        # Pick a node to fail (not load balancer)
        available_nodes = [n for n in self.active_nodes if n != 'LoadBalancer']
        if not available_nodes:
            print("⚠️  No individual nodes available for failover test")
            return
            
        failed_node = available_nodes[0]
        
        # Send messages before failure
        print(f"📤 Sending messages before failing {failed_node}...")
        self.send_test_messages(failed_node, 3)
        
        # Simulate failure
        self.simulate_node_failure(failed_node)
        
        # Try to send through load balancer (should still work)
        if 'LoadBalancer' in self.active_nodes:
            print("🔄 Testing load balancer after node failure...")
            if self.send_test_messages('LoadBalancer', 5):
                print("✅ Load balancer routing successful after node failure")
            else:
                print("❌ Load balancer failed after node failure")
        
        # Attempt to reconnect to the failed node
        print(f"🔄 Attempting to reconnect to {failed_node}...")
        for config in self.node_configs:
            if config['name'] == failed_node:
                conn, channel = self.create_connection(config)
                if conn:
                    self.connections[failed_node] = conn
                    self.channels[failed_node] = channel
                    self.active_nodes.add(failed_node)
                    print(f"✅ {failed_node} reconnected successfully")
                    
                    # Test sending after recovery
                    if self.send_test_messages(failed_node, 2):
                        print(f"✅ {failed_node} fully operational after recovery")
                else:
                    print(f"❌ Failed to reconnect to {failed_node}")
                break

    def consume_test_messages(self, max_messages: int = 50):
        """Consume and display test messages"""
        print(f"\n👂 Consuming up to {max_messages} test messages...")
        
        if 'LoadBalancer' not in self.channels:
            print("❌ No load balancer connection for consuming")
            return
            
        channel = self.channels['LoadBalancer']
        messages_consumed = 0
        
        def callback(ch, method, properties, body):
            nonlocal messages_consumed
            try:
                message = json.loads(body)
                print(f"📨 [{messages_consumed + 1}] From {message.get('sender_node', 'Unknown')}: {message.get('message', 'No message')[:50]}...")
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
                messages_consumed += 1
                
                if messages_consumed >= max_messages:
                    ch.stop_consuming()
                    
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        try:
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(
                queue='failover_queue',
                on_message_callback=callback
            )
            
            # Set a timeout for consumption
            timeout = 30  # 30 seconds
            start_time = time.time()
            
            while channel._consumer_infos and (time.time() - start_time) < timeout:
                channel.connection.process_data_events(time_limit=1)
                
            print(f"✅ Consumed {messages_consumed} messages")
            
        except Exception as e:
            print(f"❌ Error during consumption: {e}")

    def cleanup(self):
        """Clean up all connections"""
        print("\n🧹 Cleaning up connections...")
        for name, connection in list(self.connections.items()):
            try:
                connection.close()
                print(f"🔌 Closed connection to {name}")
            except:
                pass
        
        self.connections.clear()
        self.channels.clear()
        self.active_nodes.clear()

def main():
    tester = FailoverTester()
    
    try:
        print("🎯 RabbitMQ Cluster Failover Test")
        print("=" * 50)
        
        # Test initial connections
        if not tester.test_all_connections():
            print("❌ No connections available - cannot proceed")
            return
        
        # Test message persistence
        tester.test_message_persistence()
        
        # Test failover and recovery
        tester.test_failover_recovery()
        
        # Consume some messages to verify persistence
        tester.consume_test_messages(20)
        
        print("\n✅ Failover test completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()

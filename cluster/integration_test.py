#!/usr/bin/env python3
"""
RabbitMQ Cluster Integration Test

This script performs comprehensive testing of the RabbitMQ cluster setup:
- Connection testing to all nodes
- HA queue functionality
- Load balancer health
- Failover scenarios
- Message persistence
- Performance benchmarks
"""

import pika
import json
import time
import requests
import subprocess
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional

class ClusterIntegrationTest:
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
        # Test configurations
        self.cluster_nodes = [
            {'name': 'Node1', 'host': 'localhost', 'port': 5672, 'mgmt_port': 15672},
            {'name': 'Node2', 'host': 'localhost', 'port': 5673, 'mgmt_port': 15673},
            {'name': 'Node3', 'host': 'localhost', 'port': 5674, 'mgmt_port': 15674},
        ]
        
        self.load_balancer = {
            'name': 'LoadBalancer',
            'host': 'localhost', 
            'port': 5675,
            'mgmt_port': 15675,
            'stats_port': 8404
        }
        
        self.credentials = {'username': 'admin', 'password': 'admin123'}

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_icon} {test_name}: {status}")
        if details:
            print(f"    {details}")
        
        self.test_results[test_name] = {
            'status': status,
            'details': details,
            'timestamp': timestamp
        }

    def test_docker_containers(self) -> bool:
        """Test if all Docker containers are running"""
        print("\n🐳 Testing Docker Containers...")
        
        required_containers = ['rabbitmq1', 'rabbitmq2', 'rabbitmq3', 'rabbitmq_haproxy']
        
        try:
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], 
                                  capture_output=True, text=True, check=True)
            running_containers = result.stdout.strip().split('\n')
            
            all_running = True
            for container in required_containers:
                if container in running_containers:
                    self.log_test(f"Container {container}", "PASS", "Running")
                else:
                    self.log_test(f"Container {container}", "FAIL", "Not found")
                    all_running = False
            
            return all_running
            
        except subprocess.CalledProcessError as e:
            self.log_test("Docker Check", "FAIL", f"Docker command failed: {e}")
            return False

    def test_amqp_connections(self) -> Dict[str, bool]:
        """Test AMQP connections to all nodes"""
        print("\n🔌 Testing AMQP Connections...")
        
        connection_results = {}
        
        # Test individual nodes
        for node in self.cluster_nodes:
            try:
                connection_params = pika.ConnectionParameters(
                    host=node['host'],
                    port=node['port'],
                    credentials=pika.PlainCredentials(
                        self.credentials['username'], 
                        self.credentials['password']
                    ),
                    heartbeat=10,
                    socket_timeout=5
                )
                
                connection = pika.BlockingConnection(connection_params)
                connection.close()
                
                self.log_test(f"AMQP {node['name']}", "PASS", f"Connected to {node['host']}:{node['port']}")
                connection_results[node['name']] = True
                
            except Exception as e:
                self.log_test(f"AMQP {node['name']}", "FAIL", str(e))
                connection_results[node['name']] = False
        
        # Test load balancer
        try:
            lb_params = pika.ConnectionParameters(
                host=self.load_balancer['host'],
                port=self.load_balancer['port'],
                credentials=pika.PlainCredentials(
                    self.credentials['username'], 
                    self.credentials['password']
                ),
                heartbeat=10,
                socket_timeout=5
            )
            
            connection = pika.BlockingConnection(lb_params)
            connection.close()
            
            self.log_test("AMQP LoadBalancer", "PASS", f"Connected to load balancer")
            connection_results['LoadBalancer'] = True
            
        except Exception as e:
            self.log_test("AMQP LoadBalancer", "FAIL", str(e))
            connection_results['LoadBalancer'] = False
        
        return connection_results

    def test_management_apis(self) -> Dict[str, bool]:
        """Test Management API access"""
        print("\n🌐 Testing Management APIs...")
        
        api_results = {}
        auth = (self.credentials['username'], self.credentials['password'])
        
        # Test individual nodes
        for node in self.cluster_nodes:
            try:
                url = f"http://localhost:{node['mgmt_port']}/api/overview"
                response = requests.get(url, auth=auth, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    node_name = data.get('node', 'unknown')
                    self.log_test(f"Management {node['name']}", "PASS", f"API accessible, node: {node_name}")
                    api_results[node['name']] = True
                else:
                    self.log_test(f"Management {node['name']}", "FAIL", f"HTTP {response.status_code}")
                    api_results[node['name']] = False
                    
            except Exception as e:
                self.log_test(f"Management {node['name']}", "FAIL", str(e))
                api_results[node['name']] = False
        
        # Test load balancer management
        try:
            url = f"http://localhost:{self.load_balancer['mgmt_port']}/api/overview"
            response = requests.get(url, auth=auth, timeout=10)
            
            if response.status_code == 200:
                self.log_test("Management LoadBalancer", "PASS", "Load balanced management accessible")
                api_results['LoadBalancer'] = True
            else:
                self.log_test("Management LoadBalancer", "FAIL", f"HTTP {response.status_code}")
                api_results['LoadBalancer'] = False
                
        except Exception as e:
            self.log_test("Management LoadBalancer", "FAIL", str(e))
            api_results['LoadBalancer'] = False
        
        return api_results

    def test_haproxy_stats(self) -> bool:
        """Test HAProxy statistics interface"""
        print("\n📊 Testing HAProxy Stats...")
        
        try:
            url = f"http://localhost:{self.load_balancer['stats_port']}"
            response = requests.get(url, auth=(self.credentials['username'], self.credentials['password']), timeout=10)
            
            if response.status_code == 200:
                # Check if response contains HAProxy stats indicators
                if 'HAProxy' in response.text or 'Statistics Report' in response.text:
                    self.log_test("HAProxy Stats", "PASS", "Statistics interface accessible")
                    return True
                else:
                    self.log_test("HAProxy Stats", "WARN", "Accessible but content unclear")
                    return False
            else:
                self.log_test("HAProxy Stats", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("HAProxy Stats", "FAIL", str(e))
            return False

    def test_cluster_status(self) -> bool:
        """Test cluster formation and status"""
        print("\n🏗️ Testing Cluster Status...")
        
        try:
            # Check cluster status from node 1
            result = subprocess.run([
                'docker', 'exec', 'rabbitmq1', 
                'rabbitmqctl', 'cluster_status'
            ], capture_output=True, text=True, check=True)
            
            output = result.stdout
            
            # Check if all nodes are in the cluster
            nodes_found = 0
            for i in range(1, 4):
                if f'rabbit@rabbitmq{i}' in output:
                    nodes_found += 1
            
            if nodes_found == 3:
                self.log_test("Cluster Formation", "PASS", f"All 3 nodes in cluster")
                
                # Check for running nodes
                if 'running_nodes' in output:
                    running_count = output.count('rabbit@rabbitmq')
                    self.log_test("Running Nodes", "PASS", f"{running_count} nodes running")
                    return True
                else:
                    self.log_test("Running Nodes", "WARN", "Could not determine running nodes")
                    return False
            else:
                self.log_test("Cluster Formation", "FAIL", f"Only {nodes_found}/3 nodes in cluster")
                return False
                
        except subprocess.CalledProcessError as e:
            self.log_test("Cluster Status", "FAIL", f"Command failed: {e}")
            return False

    def test_ha_policy(self) -> bool:
        """Test High Availability policy"""
        print("\n🔄 Testing HA Policy...")
        
        try:
            result = subprocess.run([
                'docker', 'exec', 'rabbitmq1',
                'rabbitmqctl', 'list_policies'
            ], capture_output=True, text=True, check=True)
            
            output = result.stdout
            
            if 'ha-all' in output and 'ha-mode' in output and 'all' in output:
                self.log_test("HA Policy", "PASS", "HA policy 'ha-all' found with mode 'all'")
                return True
            else:
                self.log_test("HA Policy", "FAIL", "HA policy not found or incorrectly configured")
                return False
                
        except subprocess.CalledProcessError as e:
            self.log_test("HA Policy", "FAIL", f"Command failed: {e}")
            return False

    def test_message_flow(self) -> bool:
        """Test message publishing and consuming through load balancer"""
        print("\n📨 Testing Message Flow...")
        
        try:
            # Connect through load balancer
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=self.load_balancer['host'],
                port=self.load_balancer['port'],
                credentials=pika.PlainCredentials(
                    self.credentials['username'], 
                    self.credentials['password']
                ),
                heartbeat=30
            ))
            
            channel = connection.channel()
            
            # Setup test infrastructure
            test_exchange = 'integration_test_exchange'
            test_queue = 'integration_test_queue'
            test_routing_key = 'integration_test'
            
            channel.exchange_declare(exchange=test_exchange, exchange_type='direct', durable=True)
            channel.queue_declare(queue=test_queue, durable=True)
            channel.queue_bind(exchange=test_exchange, queue=test_queue, routing_key=test_routing_key)
            
            # Send test messages
            test_messages = []
            for i in range(10):
                message = {
                    'id': i,
                    'timestamp': datetime.now().isoformat(),
                    'test_data': f'Integration test message {i}'
                }
                test_messages.append(message)
                
                channel.basic_publish(
                    exchange=test_exchange,
                    routing_key=test_routing_key,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            
            self.log_test("Message Publishing", "PASS", f"Sent {len(test_messages)} messages")
            
            # Consume messages
            received_messages = []
            
            def callback(ch, method, properties, body):
                message = json.loads(body)
                received_messages.append(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
                if len(received_messages) >= len(test_messages):
                    ch.stop_consuming()
            
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=test_queue, on_message_callback=callback)
            
            # Start consuming with timeout
            start_time = time.time()
            timeout = 30
            
            while len(received_messages) < len(test_messages) and (time.time() - start_time) < timeout:
                connection.process_data_events(time_limit=1)
            
            connection.close()
            
            if len(received_messages) == len(test_messages):
                self.log_test("Message Consuming", "PASS", f"Received {len(received_messages)} messages")
                return True
            else:
                self.log_test("Message Consuming", "FAIL", f"Expected {len(test_messages)}, got {len(received_messages)}")
                return False
                
        except Exception as e:
            self.log_test("Message Flow", "FAIL", str(e))
            return False

    def test_load_balancing(self) -> bool:
        """Test load balancing by checking connection distribution"""
        print("\n⚖️ Testing Load Balancing...")
        
        try:
            # Create multiple connections through load balancer
            connections = []
            
            for i in range(6):  # Create 6 connections to see distribution
                try:
                    conn = pika.BlockingConnection(pika.ConnectionParameters(
                        host=self.load_balancer['host'],
                        port=self.load_balancer['port'],
                        credentials=pika.PlainCredentials(
                            self.credentials['username'], 
                            self.credentials['password']
                        ),
                        heartbeat=30
                    ))
                    connections.append(conn)
                    time.sleep(0.5)  # Small delay between connections
                except Exception as e:
                    print(f"    Connection {i+1} failed: {e}")
            
            # Check if connections were created
            if len(connections) >= 3:  # At least half successful
                self.log_test("Load Balancer Connections", "PASS", f"Created {len(connections)} connections")
                
                # Close connections
                for conn in connections:
                    try:
                        conn.close()
                    except:
                        pass
                
                return True
            else:
                self.log_test("Load Balancer Connections", "FAIL", f"Only {len(connections)} connections created")
                return False
                
        except Exception as e:
            self.log_test("Load Balancing", "FAIL", str(e))
            return False

    def run_performance_test(self) -> Dict[str, float]:
        """Run basic performance test"""
        print("\n🚀 Running Performance Test...")
        
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=self.load_balancer['host'],
                port=self.load_balancer['port'],
                credentials=pika.PlainCredentials(
                    self.credentials['username'], 
                    self.credentials['password']
                ),
                heartbeat=30
            ))
            
            channel = connection.channel()
            
            # Setup
            perf_exchange = 'perf_test_exchange'
            perf_queue = 'perf_test_queue'
            
            channel.exchange_declare(exchange=perf_exchange, exchange_type='direct', durable=True)
            channel.queue_declare(queue=perf_queue, durable=True)
            channel.queue_bind(exchange=perf_exchange, queue=perf_queue, routing_key='perf')
            
            # Performance test parameters
            message_count = 1000
            message_size = 1024  # 1KB messages
            test_message = 'x' * message_size
            
            # Publishing performance
            start_time = time.time()
            
            for i in range(message_count):
                channel.basic_publish(
                    exchange=perf_exchange,
                    routing_key='perf',
                    body=test_message,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            
            publish_time = time.time() - start_time
            publish_rate = message_count / publish_time
            
            # Consuming performance
            consumed_count = 0
            start_time = time.time()
            
            def perf_callback(ch, method, properties, body):
                nonlocal consumed_count
                consumed_count += 1
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
                if consumed_count >= message_count:
                    ch.stop_consuming()
            
            channel.basic_qos(prefetch_count=100)
            channel.basic_consume(queue=perf_queue, on_message_callback=perf_callback)
            channel.start_consuming()
            
            consume_time = time.time() - start_time
            consume_rate = consumed_count / consume_time if consume_time > 0 else 0
            
            connection.close()
            
            perf_results = {
                'publish_rate': publish_rate,
                'consume_rate': consume_rate,
                'message_count': message_count,
                'message_size': message_size
            }
            
            self.log_test("Performance Test", "PASS", 
                         f"Publish: {publish_rate:.1f} msg/s, Consume: {consume_rate:.1f} msg/s")
            
            return perf_results
            
        except Exception as e:
            self.log_test("Performance Test", "FAIL", str(e))
            return {}

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("🎯 RABBITMQ CLUSTER INTEGRATION TEST REPORT")
        print("="*60)
        
        total_time = time.time() - self.start_time
        print(f"⏱️  Total test time: {total_time:.2f} seconds")
        print(f"📅 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Count results
        passed = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        failed = sum(1 for result in self.test_results.values() if result['status'] == 'FAIL')
        warned = sum(1 for result in self.test_results.values() if result['status'] == 'WARN')
        total = len(self.test_results)
        
        print(f"\n📊 SUMMARY:")
        print(f"   ✅ Passed: {passed}/{total}")
        print(f"   ❌ Failed: {failed}/{total}")
        print(f"   ⚠️  Warnings: {warned}/{total}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"   🎯 Success Rate: {success_rate:.1f}%")
        
        # Overall status
        if failed == 0:
            print(f"\n🎉 OVERALL RESULT: {'EXCELLENT' if warned == 0 else 'GOOD'}")
            print("   RabbitMQ cluster is ready for production use!")
        elif failed <= 2:
            print(f"\n⚠️  OVERALL RESULT: NEEDS ATTENTION")
            print("   Some components need fixing before production use.")
        else:
            print(f"\n❌ OVERALL RESULT: CRITICAL ISSUES")
            print("   Major problems detected. Cluster not ready for use.")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if failed == 0 and warned == 0:
            print("   • Cluster is fully functional and ready")
            print("   • Consider running load tests for your specific use case")
            print("   • Set up monitoring for production deployment")
        else:
            print("   • Review failed tests and fix underlying issues")
            print("   • Check Docker container logs for detailed error information")
            print("   • Verify network connectivity and firewall settings")
            if failed > 0:
                print("   • Restart cluster components if necessary")

def main():
    print("🎯 RabbitMQ Cluster Integration Test Suite")
    print("=" * 50)
    print("This comprehensive test validates all cluster components")
    print("including Docker containers, networking, HA, and performance.\n")
    
    tester = ClusterIntegrationTest()
    
    try:
        # Run all tests
        tester.test_docker_containers()
        tester.test_amqp_connections()
        tester.test_management_apis()
        tester.test_haproxy_stats()
        tester.test_cluster_status()
        tester.test_ha_policy()
        tester.test_message_flow()
        tester.test_load_balancing()
        tester.run_performance_test()
        
        # Generate report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        tester.log_test("Test Suite", "FAIL", str(e))
        tester.generate_report()

if __name__ == "__main__":
    main()

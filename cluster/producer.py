#!/usr/bin/env python3
import pika
import json
import time
import sys
from datetime import datetime

class ClusterProducer:
    def __init__(self, host='localhost', port=5675):
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        """Create or recreate connection"""
        while True:
            try:
                print(f"🔌 Connecting to {self.host}:{self.port} ...")
                connection_params = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=pika.PlainCredentials('admin', 'admin123'),
                    heartbeat=30
                )
                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()
                self.setup_infrastructure()
                print("✅ Connected and channel ready!")
                break
            except Exception as e:
                print(f"❌ Connection error: {e}")
                time.sleep(2)

    def setup_infrastructure(self):
        """Declare exchange and queue"""
        self.channel.exchange_declare(
            exchange='cluster_exchange',
            exchange_type='direct',
            durable=True
        )
        self.channel.queue_declare(
            queue='cluster_queue',
            durable=True,
            arguments={'x-message-ttl': 300000}
        )
        self.channel.queue_bind(
            exchange='cluster_exchange',
            queue='cluster_queue',
            routing_key='cluster_messages'
        )

    def send_message(self, message_body, message_id):
        """Publish a single message with retry on failure"""
        try:
            self.channel.basic_publish(
                exchange='cluster_exchange',
                routing_key='cluster_messages',
                body=json.dumps(message_body),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    message_id=str(message_id),
                    timestamp=int(time.time())
                )
            )
            print(f"✅ Sent message {message_id}")
        except (pika.exceptions.AMQPError, Exception) as e:
            print(f"⚠️ Publish failed: {e}")
            print("🔄 Reconnecting and retrying...")
            self.connect()
            self.send_message(message_body, message_id)

    def send_messages(self, total=10):
        print(f"📤 Sending {total} messages...")
        for i in range(total):
            message = {
                'id': i,
                'timestamp': datetime.now().isoformat(),
                'message': f'Cluster message #{i}',
                'sender': 'cluster_producer'
            }
            self.send_message(message, i)
            time.sleep(0.5)

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("🔌 Connection closed")

def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    producer = ClusterProducer()
    try:
        producer.send_messages(count)
    finally:
        producer.close()

if __name__ == "__main__":
    main()

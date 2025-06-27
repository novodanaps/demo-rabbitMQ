#!/usr/bin/env python3
"""
Test script to demonstrate retry functionality
Send different types of messages to test the consumer retry mechanism
"""

import subprocess
import time
import sys

def send_message(routing_key, message):
    """Send a test message using the producer"""
    cmd = ['python', 'producer.py', routing_key, message]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Sent: {message}")
    if result.returncode != 0:
        print(f"Error: {result.stderr}")

def run_retry_tests():
    """Run a series of tests to demonstrate retry functionality"""
    print("=== RabbitMQ Consumer Retry Test ===\n")
    
    test_cases = [
        ("info", "Normal message - should process successfully"),
        ("warning", "temporary_error - should retry 3 times then go to DLQ"),
        ("error", "critical_error - should go directly to DLQ (permanent error)"),
        ("info", "random_fail - may succeed or fail randomly"),
        ("warning", "another temporary_error - testing retry mechanism"),
        ("error", "invalid json {broken - testing JSON parsing error"),
    ]
    
    print("Test cases to be sent:")
    for i, (routing_key, message) in enumerate(test_cases, 1):
        print(f"{i}. [{routing_key}] {message}")
    
    print(f"\nSending {len(test_cases)} test messages with 2-second intervals...")
    print("Make sure you have the consumer running in another terminal:")
    print("python consumer.py info warning error\n")
    
    input("Press Enter to start sending test messages...")
    
    for i, (routing_key, message) in enumerate(test_cases, 1):
        print(f"\n--- Test {i}/{len(test_cases)} ---")
        send_message(routing_key, message)
        time.sleep(2)  # Wait between messages
    
    print("\n=== All test messages sent! ===")
    print("Check your consumer terminal to see the retry behavior.")
    print("\nExpected behavior:")
    print("- Normal messages: ✓ Processed successfully")
    print("- temporary_error: ↻ Retried 3 times, then 💀 sent to DLQ")
    print("- critical_error: 💀 Sent directly to DLQ (no retries)")
    print("- random_fail: May succeed ✓ or fail and retry ↻")
    print("- Invalid JSON: 💀 Sent to DLQ with JSON error")

if __name__ == '__main__':
    run_retry_tests()

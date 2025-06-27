#!/usr/bin/env python3
"""
Test script to verify channel error handling fixes
"""

import subprocess
import time
import sys

def test_channel_resilience():
    """Test that the consumer handles channel errors gracefully"""
    print("=== Channel Resilience Test ===")
    print("This test sends messages that should trigger different error scenarios")
    print("to ensure the consumer doesn't crash due to channel state issues.\n")
    
    test_messages = [
        ("info", "normal message - should work fine"),
        ("error", "critical_error - permanent failure test"),
        ("warning", "temporary_error - retry mechanism test"),
        ("info", "random_fail - random failure test"),
        ("error", "another critical_error - second permanent failure"),
    ]
    
    print("Messages to be sent:")
    for i, (routing_key, message) in enumerate(test_messages, 1):
        print(f"{i}. [{routing_key}] {message}")
    
    print(f"\nMake sure your consumer is running:")
    print("python consumer.py info warning error")
    print("\nExpected behavior:")
    print("- Consumer should handle all messages without crashing")
    print("- No 'Channel is closed' errors should occur")
    print("- Messages should be properly acknowledged or sent to DLQ")
    
    input("\nPress Enter to start sending test messages...")
    
    for i, (routing_key, message) in enumerate(test_messages, 1):
        print(f"\n--- Sending message {i}/{len(test_messages)} ---")
        cmd = ['python', 'producer.py', routing_key, message]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Sent: [{routing_key}] {message}")
        else:
            print(f"❌ Failed to send: {result.stderr}")
        
        time.sleep(1)  # Small delay between messages
    
    print("\n=== Test completed! ===")
    print("Check your consumer output:")
    print("- Look for [✓] [↻] [💀] indicators")
    print("- Ensure no 'Channel is closed' errors occurred")
    print("- Consumer should still be running and responsive")

if __name__ == '__main__':
    test_channel_resilience()

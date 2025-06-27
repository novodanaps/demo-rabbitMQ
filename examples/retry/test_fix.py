#!/usr/bin/env python3
"""
Quick test script to verify the retry mechanism fix
"""

import subprocess
import time

def send_test_message():
    """Send a test message that will trigger the error handling"""
    cmd = ['python', 'producer.py', 'error', 'critical_error test message']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Test message sent successfully")
        print("Expected behavior: Message should go directly to dead letter queue")
        print("Check your consumer output for the [💀] indicator")
    else:
        print(f"❌ Failed to send test message: {result.stderr}")

if __name__ == '__main__':
    print("=== Testing Fixed Retry Mechanism ===")
    print("Make sure you have the consumer running:")
    print("python consumer.py error warning info")
    print()
    
    input("Press Enter to send test message...")
    send_test_message()
    
    print("\nTest completed!")
    print("If no errors occurred, the fix is working correctly.")

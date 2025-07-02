#!/usr/bin/env python3
"""
Simple test script to verify QuantServer functionality
"""

import threading
import time
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from QuantServer import QuantServer


import zmq
import json
from datetime import datetime


class TestClient:
    """Simple test client for QuantServer"""
    
    def __init__(self, server_host="localhost", server_port=5557):
        """Initialize the test client"""
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{server_host}:{server_port}")
        print(f"Connected to QuantServer at {server_host}:{server_port}")
    
    def send_request(self, message):
        """Send request and get response"""
        try:
            self.socket.send_json(message)
            response = self.socket.recv_json()
            return response
        except Exception as e:
            print(f"Error sending request: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        self.socket.close()
        self.context.term()


def run_server():
    """Run the server in a separate thread"""
    server = QuantServer(port=5557)  # Use different port for testing
    try:
        server.start_server()
    except Exception as e:
        print(f"Server error: {e}")


def test_basic_functionality():
    """Test basic server functionality"""
    print("Starting QuantServer test...")
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Create client and test basic functionality
        client = TestClient(server_port=5557)
        
        # Test heartbeat
        print("Testing heartbeat...")
        response = client.send_request({
            'type': 'heartbeat',
            'client_time': datetime.now().isoformat()
        })
        
        if response and isinstance(response, dict) and response.get('status') == 'success':
            print("✓ Heartbeat test passed")
        else:
            print("✗ Heartbeat test failed")
            print(f"Response: {response}")
            return False
        
        # Test server info
        print("Testing server info...")
        response = client.send_request({
            'type': 'control',
            'control_type': 'server_info'
        })
        
        if response and isinstance(response, dict) and response.get('status') == 'success':
            print("✓ Server info test passed")
            info = response.get('info', {})
            if isinstance(info, dict):
                indicators = info.get('available_indicators', [])
                print(f"  Available indicators: {indicators}")
        else:
            print("✗ Server info test failed")
            print(f"Response: {response}")
            return False
        
        # Test simple indicator
        print("Testing SMA indicator...")
        response = client.send_request({
            'type': 'api_call',
            'requests': [
                {
                    'indicator_name': 'SMA Test',
                    'indicator_function_name': 'sma',
                    'parameters': {
                        'data': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                        'period': 3
                    },
                    'result_required': True
                }
            ]
        })
        
        if response and isinstance(response, dict) and response.get('status') == 'success':
            print("✓ SMA indicator test passed")
            results = response.get('results', [])
            if isinstance(results, list) and len(results) > 0:
                result = results[0]
                if isinstance(result, dict) and result.get('status') == 'success':
                    result_data = result.get('result', {})
                    if isinstance(result_data, dict):
                        sma_values = result_data.get('values', [])
                        print(f"  SMA values: {sma_values}")
                else:
                    error_msg = result.get('message', 'Unknown error') if isinstance(result, dict) else 'Invalid result format'
                    print(f"  SMA calculation error: {error_msg}")
        else:
            print("✗ SMA indicator test failed")
            print(f"Response: {response}")
            return False
        
        # Test kbar data
        print("Testing kbar data...")
        response = client.send_request({
            'type': 'kbar_data',
            'data': {
                'symbol': 'TEST',
                'timestamp': '2024-01-15T10:30:00',
                'open': 100.0,
                'high': 101.0,
                'low': 99.0,
                'close': 100.5,
                'volume': 1000
            }
        })
        
        if response and isinstance(response, dict) and response.get('status') == 'success':
            print("✓ Kbar data test passed")
        else:
            print("✗ Kbar data test failed")
            print(f"Response: {response}")
            return False
        
        client.cleanup()
        print("\n✓ All basic tests passed! Server is working correctly.")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_basic_functionality()
    if success:
        print("\n🎉 QuantServer is ready for use!")
        sys.exit(0)
    else:
        print("\n❌ QuantServer tests failed!")
        sys.exit(1) 
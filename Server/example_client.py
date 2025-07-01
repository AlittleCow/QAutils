#!/usr/bin/env python3
"""
Example client for QuantServer demonstrating all message types
"""

import zmq
import json
import time
from datetime import datetime


class QuantClient:
    """Example client for QuantServer"""
    
    def __init__(self, server_host="localhost", server_port=5555):
        """Initialize the client"""
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
    
    def test_heartbeat(self):
        """Test heartbeat functionality"""
        print("\n=== Testing Heartbeat ===")
        message = {
            'type': 'heartbeat',
            'client_time': datetime.now().isoformat()
        }
        response = self.send_request(message)
        print(f"Response: {json.dumps(response, indent=2)}")
    
    def test_single_kbar(self):
        """Test single kbar data"""
        print("\n=== Testing Single Kbar Data ===")
        message = {
            'type': 'kbar_data',
            'data': {
                'symbol': 'AAPL',
                'timestamp': '2024-01-15T10:30:00',
                'open': 150.25,
                'high': 151.80,
                'low': 149.90,
                'close': 151.50,
                'volume': 1000000
            }
        }
        response = self.send_request(message)
        print(f"Response: {json.dumps(response, indent=2)}")
    
    def test_kbar_series(self):
        """Test kbar data series"""
        print("\n=== Testing Kbar Series Data ===")
        message = {
            'type': 'kbar_series',
            'symbol': 'AAPL',
            'data': [
                {
                    'timestamp': '2024-01-15T10:00:00',
                    'open': 150.00,
                    'high': 150.50,
                    'low': 149.50,
                    'close': 150.25,
                    'volume': 500000
                },
                {
                    'timestamp': '2024-01-15T10:30:00',
                    'open': 150.25,
                    'high': 151.80,
                    'low': 149.90,
                    'close': 151.50,
                    'volume': 1000000
                },
                {
                    'timestamp': '2024-01-15T11:00:00',
                    'open': 151.50,
                    'high': 152.20,
                    'low': 151.00,
                    'close': 151.75,
                    'volume': 750000
                }
            ]
        }
        response = self.send_request(message)
        print(f"Response: {json.dumps(response, indent=2)}")
    
    def test_api_calls(self):
        """Test side band API calls for indicators"""
        print("\n=== Testing API Calls (Indicators) ===")
        
        # Sample price data for indicators
        price_data = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 
                     111, 110, 112, 114, 113, 115, 117, 116, 118, 120]
        
        message = {
            'type': 'api_call',
            'requests': [
                {
                    'indicator_name': 'Simple Moving Average',
                    'indicator_function_name': 'sma',
                    'parameters': {
                        'data': price_data,
                        'period': 5
                    },
                    'result_required': True
                },
                {
                    'indicator_name': 'RSI',
                    'indicator_function_name': 'rsi',
                    'parameters': {
                        'data': price_data,
                        'period': 14
                    },
                    'result_required': True
                },
                {
                    'indicator_name': 'EMA',
                    'indicator_function_name': 'ema',
                    'parameters': {
                        'data': price_data,
                        'period': 10
                    },
                    'result_required': False  # This should be skipped
                }
            ]
        }
        response = self.send_request(message)
        print(f"Response: {json.dumps(response, indent=2)}")
    
    def test_control_messages(self):
        """Test server control messages"""
        print("\n=== Testing Control Messages ===")
        
        # Set a parameter
        print("Setting parameter...")
        message = {
            'type': 'control',
            'control_type': 'set_param',
            'parameters': {
                'name': 'max_connections',
                'value': 100
            }
        }
        response = self.send_request(message)
        print(f"Set param response: {json.dumps(response, indent=2)}")
        
        # Get the parameter back
        print("\nGetting parameter...")
        message = {
            'type': 'control',
            'control_type': 'get_param',
            'parameters': {
                'name': 'max_connections'
            }
        }
        response = self.send_request(message)
        print(f"Get param response: {json.dumps(response, indent=2)}")
        
        # Get server info
        print("\nGetting server info...")
        message = {
            'type': 'control',
            'control_type': 'server_info'
        }
        response = self.send_request(message)
        print(f"Server info response: {json.dumps(response, indent=2)}")
        
        # Get all parameters
        print("\nGetting all parameters...")
        message = {
            'type': 'control',
            'control_type': 'get_all_params'
        }
        response = self.send_request(message)
        print(f"All params response: {json.dumps(response, indent=2)}")
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        print("\n=== Testing Bollinger Bands ===")
        
        # Generate sample price data
        price_data = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 
                     111, 110, 112, 114, 113, 115, 117, 116, 118, 120,
                     122, 121, 123, 125, 124, 126, 128, 127, 129, 131]
        
        message = {
            'type': 'api_call',
            'requests': [
                {
                    'indicator_name': 'Bollinger Bands',
                    'indicator_function_name': 'bollinger',
                    'parameters': {
                        'data': price_data,
                        'period': 20,
                        'std_dev': 2
                    },
                    'result_required': True
                }
            ]
        }
        response = self.send_request(message)
        print(f"Response: {json.dumps(response, indent=2)}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.socket.close()
        self.context.term()


def main():
    """Main function to run all tests"""
    client = QuantClient()
    
    try:
        # Run all tests
        client.test_heartbeat()
        client.test_single_kbar()
        client.test_kbar_series()
        client.test_api_calls()
        client.test_control_messages()
        client.test_bollinger_bands()
        
        print("\n=== All tests completed ===")
        
    except KeyboardInterrupt:
        print("\nClient interrupted")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.cleanup()


if __name__ == '__main__':
    main() 
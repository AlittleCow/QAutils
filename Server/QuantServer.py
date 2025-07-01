#!/usr/bin/env python3
"""
QuantServer.py - ZeroMQ based server for handling TDX client requests

This server handles:
1. Kbar data series or single kbar data
2. Side band data for remote API calling (indicator functions)
3. Result responses back to client
4. Side band data for server parameter control
"""

import zmq
import json
import logging
import threading
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import traceback


class QuantServer:
    """ZeroMQ based server for TDX client communication"""
    
    def __init__(self, port: int = 5555, log_level: int = logging.INFO):
        """
        Initialize the QuantServer
        
        Args:
            port: Server port number
            log_level: Logging level
        """
        self.port = port
        self.context = zmq.Context()
        self.socket = None
        self.running = False
        self.server_params = {}
        
        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Message type constants
        self.MSG_TYPES = {
            'KBAR_DATA': 'kbar_data',
            'KBAR_SERIES': 'kbar_series',
            'API_CALL': 'api_call',
            'CONTROL': 'control',
            'HEARTBEAT': 'heartbeat'
        }
        
        # Initialize indicator functions registry
        self.indicator_registry = {}
        self._register_default_indicators()
    
    def _register_default_indicators(self):
        """Register default indicator functions"""
        self.indicator_registry.update({
            'sma': self._calculate_sma,
            'ema': self._calculate_ema,
            'rsi': self._calculate_rsi,
            'macd': self._calculate_macd,
            'bollinger': self._calculate_bollinger_bands
        })
    
    def start_server(self):
        """Start the ZeroMQ server"""
        try:
            self.socket = self.context.socket(zmq.REP)
            self.socket.bind(f"tcp://*:{self.port}")
            self.running = True
            
            self.logger.info(f"QuantServer started on port {self.port}")
            
            while self.running:
                try:
                    # Wait for request with timeout
                    if self.socket.poll(1000):  # 1 second timeout
                        message = self.socket.recv_json(zmq.NOBLOCK)
                        response = self._handle_message(message)
                        self.socket.send_json(response)
                    
                except zmq.Again:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    error_response = {
                        'status': 'error',
                        'message': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    try:
                        self.socket.send_json(error_response)
                    except:
                        pass
                        
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self._cleanup()
    
    def stop_server(self):
        """Stop the server"""
        self.running = False
        self.logger.info("Server stop requested")
    
    def _cleanup(self):
        """Cleanup resources"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        self.logger.info("Server cleanup completed")
    
    def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming messages from TDX client
        
        Args:
            message: Incoming message dictionary
            
        Returns:
            Response dictionary
        """
        try:
            msg_type = message.get('type', 'unknown')
            self.logger.info(f"Received message type: {msg_type}")
            
            if msg_type == self.MSG_TYPES['KBAR_DATA']:
                return self._handle_kbar_data(message)
            elif msg_type == self.MSG_TYPES['KBAR_SERIES']:
                return self._handle_kbar_series(message)
            elif msg_type == self.MSG_TYPES['API_CALL']:
                return self._handle_api_call(message)
            elif msg_type == self.MSG_TYPES['CONTROL']:
                return self._handle_control(message)
            elif msg_type == self.MSG_TYPES['HEARTBEAT']:
                return self._handle_heartbeat(message)
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown message type: {msg_type}',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            }
    
    def _handle_kbar_data(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle single kbar data request
        
        Args:
            message: Message containing kbar data request
            
        Returns:
            Response with processed kbar data
        """
        try:
            kbar_data = message.get('data', {})
            symbol = kbar_data.get('symbol', '')
            timestamp = kbar_data.get('timestamp', '')
            open_price = kbar_data.get('open', 0)
            high_price = kbar_data.get('high', 0)
            low_price = kbar_data.get('low', 0)
            close_price = kbar_data.get('close', 0)
            volume = kbar_data.get('volume', 0)
            
            # Process the kbar data (add your processing logic here)
            processed_data = {
                'symbol': symbol,
                'timestamp': timestamp,
                'ohlcv': {
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                },
                'processed_time': datetime.now().isoformat()
            }
            
            return {
                'status': 'success',
                'type': 'kbar_data_response',
                'data': processed_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error processing kbar data: {e}")
    
    def _handle_kbar_series(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle kbar data series request
        
        Args:
            message: Message containing kbar series data
            
        Returns:
            Response with processed kbar series
        """
        try:
            series_data = message.get('data', [])
            symbol = message.get('symbol', '')
            
            processed_series = []
            for kbar in series_data:
                processed_kbar = {
                    'timestamp': kbar.get('timestamp', ''),
                    'open': kbar.get('open', 0),
                    'high': kbar.get('high', 0),
                    'low': kbar.get('low', 0),
                    'close': kbar.get('close', 0),
                    'volume': kbar.get('volume', 0)
                }
                processed_series.append(processed_kbar)
            
            return {
                'status': 'success',
                'type': 'kbar_series_response',
                'symbol': symbol,
                'data': processed_series,
                'count': len(processed_series),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error processing kbar series: {e}")
    
    def _handle_api_call(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle side band API call requests
        
        Args:
            message: Message containing API call information
            
        Returns:
            Response with API call results
        """
        try:
            api_requests = message.get('requests', [])
            results = []
            
            for request in api_requests:
                indicator_name = request.get('indicator_name', '')
                function_name = request.get('indicator_function_name', '')
                parameters = request.get('parameters', {})
                require_result = request.get('result_required', True)
                
                if not require_result:
                    results.append({
                        'indicator_name': indicator_name,
                        'function_name': function_name,
                        'status': 'skipped',
                        'message': 'Result not required'
                    })
                    continue
                
                try:
                    # Execute the indicator function
                    if function_name in self.indicator_registry:
                        result = self.indicator_registry[function_name](parameters)
                        results.append({
                            'indicator_name': indicator_name,
                            'function_name': function_name,
                            'status': 'success',
                            'result': result,
                            'parameters': parameters
                        })
                    else:
                        results.append({
                            'indicator_name': indicator_name,
                            'function_name': function_name,
                            'status': 'error',
                            'message': f'Unknown function: {function_name}',
                            'available_functions': list(self.indicator_registry.keys())
                        })
                        
                except Exception as func_error:
                    results.append({
                        'indicator_name': indicator_name,
                        'function_name': function_name,
                        'status': 'error',
                        'message': str(func_error),
                        'parameters': parameters
                    })
            
            return {
                'status': 'success',
                'type': 'api_call_response',
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error processing API calls: {e}")
    
    def _handle_control(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle server control messages
        
        Args:
            message: Control message
            
        Returns:
            Control response
        """
        try:
            control_type = message.get('control_type', '')
            parameters = message.get('parameters', {})
            
            if control_type == 'set_param':
                param_name = parameters.get('name', '')
                param_value = parameters.get('value', '')
                self.server_params[param_name] = param_value
                
                return {
                    'status': 'success',
                    'type': 'control_response',
                    'message': f'Parameter {param_name} set to {param_value}',
                    'timestamp': datetime.now().isoformat()
                }
                
            elif control_type == 'get_param':
                param_name = parameters.get('name', '')
                param_value = self.server_params.get(param_name, None)
                
                return {
                    'status': 'success',
                    'type': 'control_response',
                    'parameter': {
                        'name': param_name,
                        'value': param_value
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
            elif control_type == 'get_all_params':
                return {
                    'status': 'success',
                    'type': 'control_response',
                    'parameters': self.server_params,
                    'timestamp': datetime.now().isoformat()
                }
                
            elif control_type == 'server_info':
                return {
                    'status': 'success',
                    'type': 'control_response',
                    'info': {
                        'port': self.port,
                        'running': self.running,
                        'available_indicators': list(self.indicator_registry.keys()),
                        'parameter_count': len(self.server_params)
                    },
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown control type: {control_type}',
                    'available_controls': ['set_param', 'get_param', 'get_all_params', 'server_info'],
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            raise Exception(f"Error processing control message: {e}")
    
    def _handle_heartbeat(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle heartbeat messages
        
        Args:
            message: Heartbeat message
            
        Returns:
            Heartbeat response
        """
        return {
            'status': 'success',
            'type': 'heartbeat_response',
            'server_time': datetime.now().isoformat(),
            'client_time': message.get('client_time', ''),
            'timestamp': datetime.now().isoformat()
        }
    
    # Indicator calculation functions
    def _calculate_sma(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Simple Moving Average"""
        data = params.get('data', [])
        period = params.get('period', 20)
        
        if len(data) < period:
            return {'error': 'Insufficient data for SMA calculation'}
        
        sma_values = []
        for i in range(period - 1, len(data)):
            sma = sum(data[i - period + 1:i + 1]) / period
            sma_values.append(sma)
        
        return {
            'indicator': 'SMA',
            'period': period,
            'values': sma_values
        }
    
    def _calculate_ema(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Exponential Moving Average"""
        data = params.get('data', [])
        period = params.get('period', 20)
        
        if len(data) < period:
            return {'error': 'Insufficient data for EMA calculation'}
        
        alpha = 2 / (period + 1)
        ema_values = [data[0]]
        
        for price in data[1:]:
            ema = alpha * price + (1 - alpha) * ema_values[-1]
            ema_values.append(ema)
        
        return {
            'indicator': 'EMA',
            'period': period,
            'values': ema_values
        }
    
    def _calculate_rsi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Relative Strength Index"""
        data = params.get('data', [])
        period = params.get('period', 14)
        
        if len(data) < period + 1:
            return {'error': 'Insufficient data for RSI calculation'}
        
        gains = []
        losses = []
        
        for i in range(1, len(data)):
            change = data[i] - data[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = []
        
        for i in range(period, len(gains)):
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
            
            # Update averages
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        return {
            'indicator': 'RSI',
            'period': period,
            'values': rsi_values
        }
    
    def _calculate_macd(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate MACD"""
        data = params.get('data', [])
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        signal_period = params.get('signal_period', 9)
        
        if len(data) < slow_period + signal_period:
            return {'error': 'Insufficient data for MACD calculation'}
        
        # Calculate EMAs
        fast_ema = self._calculate_ema({'data': data, 'period': fast_period})['values']
        slow_ema = self._calculate_ema({'data': data, 'period': slow_period})['values']
        
        # Calculate MACD line
        macd_line = []
        for i in range(len(slow_ema)):
            macd_line.append(fast_ema[i + (len(fast_ema) - len(slow_ema))] - slow_ema[i])
        
        # Calculate signal line
        signal_line = self._calculate_ema({'data': macd_line, 'period': signal_period})['values']
        
        # Calculate histogram
        histogram = []
        for i in range(len(signal_line)):
            histogram.append(macd_line[i + (len(macd_line) - len(signal_line))] - signal_line[i])
        
        return {
            'indicator': 'MACD',
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        }
    
    def _calculate_bollinger_bands(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Bollinger Bands"""
        data = params.get('data', [])
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2)
        
        if len(data) < period:
            return {'error': 'Insufficient data for Bollinger Bands calculation'}
        
        sma_result = self._calculate_sma({'data': data, 'period': period})
        sma_values = sma_result['values']
        
        upper_band = []
        lower_band = []
        
        for i in range(len(sma_values)):
            # Calculate standard deviation for the period
            start_idx = i + (len(data) - len(sma_values))
            period_data = data[start_idx - period + 1:start_idx + 1]
            mean = sum(period_data) / len(period_data)
            variance = sum((x - mean) ** 2 for x in period_data) / len(period_data)
            std = variance ** 0.5
            
            upper_band.append(sma_values[i] + (std_dev * std))
            lower_band.append(sma_values[i] - (std_dev * std))
        
        return {
            'indicator': 'Bollinger Bands',
            'period': period,
            'std_dev': std_dev,
            'upper_band': upper_band,
            'middle_band': sma_values,
            'lower_band': lower_band
        }
    
    def register_indicator(self, name: str, function):
        """
        Register a custom indicator function
        
        Args:
            name: Indicator name
            function: Indicator calculation function
        """
        self.indicator_registry[name] = function
        self.logger.info(f"Registered indicator: {name}")


def main():
    """Main function to start the server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='QuantServer - ZeroMQ based server for TDX clients')
    parser.add_argument('--port', type=int, default=5555, help='Server port (default: 5555)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Log level (default: INFO)')
    
    args = parser.parse_args()
    
    log_level = getattr(logging, args.log_level)
    server = QuantServer(port=args.port, log_level=log_level)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop_server()


if __name__ == '__main__':
    main()

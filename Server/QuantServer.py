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
import pandas as pd

# Import database manager
from module.database.db import DatabaseManager, create_database_manager

# Import Chan Indicator
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from ChanPy.chan import ChanIndicator
    CHAN_INDICATOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Chan Indicator not available: {e}")
    ChanIndicator = None
    CHAN_INDICATOR_AVAILABLE = False


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

        # Initialize Chan indicators registry
        self.chan_indicators = {}  # symbol.exchange -> ChanIndicator instance
        self.chan_enabled = True  # Enable/disable Chan analysis

        # Initialize database manager with default configuration
        try:
            self.db_manager = create_database_manager()
            self.logger.info("Database manager initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize database manager: {e}")
            self.db_manager = None
    
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
                        raw_message = self.socket.recv_json(zmq.NOBLOCK)
                        
                        # Ensure message is a dictionary
                        if not isinstance(raw_message, dict):
                            error_response = {
                                'status': 'error',
                                'message': f'Invalid message format: expected dict, got {type(raw_message).__name__}',
                                'timestamp': datetime.now().isoformat()
                            }
                            self.socket.send_json(error_response)
                            continue
                            
                        response = self._handle_message(raw_message)
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
        if self.db_manager:
            try:
                self.db_manager.close()
                self.logger.info("Database manager closed")
            except Exception as e:
                self.logger.error(f"Error closing database manager: {e}")
        
        # Cleanup Chan indicators
        if hasattr(self, 'chan_indicators'):
            try:
                self.chan_indicators.clear()
                self.logger.info(f"Chan indicators cleared")
            except Exception as e:
                self.logger.error(f"Error clearing Chan indicators: {e}")
                
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
            exchange = kbar_data.get('exchange', 'SH')  # Default to Shanghai exchange
            raw_period = message.get('period', '1min')  # Default to 1-minute period
            
            # Convert period code to proper period string
            period = self._convert_period_code_to_string(raw_period)
            
            timestamp = kbar_data.get('timestamp', '')
            open_price = round(kbar_data.get('open', 0), 3)
            high_price = round(kbar_data.get('high', 0), 3)
            low_price = round(kbar_data.get('low', 0), 3)
            close_price = round(kbar_data.get('close', 0), 3)
            volume = kbar_data.get('volume', 0)
            
            # debug print
            print(f"Received kbar data: \nsymbol={symbol}, exchange={exchange}, period={period}, "
                  f"timestamp={timestamp}, open={open_price:.2f}, high={high_price:.2f}, "
                  f"low={low_price:.2f}, close={close_price:.2f}, volume={volume}")

            # Process the kbar data
            processed_data = {
                'symbol': symbol,
                'exchange': exchange,
                'period': period,
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
            
            # Store in database if available
            db_status = "not_available"
            if self.db_manager:
                try:
                    # Ensure stock exists in database
                    stock_name = kbar_data.get('name', symbol)
                    if not self.setup_stock_if_needed(symbol, exchange, stock_name):
                        db_status = "error: failed to setup stock"
                    else:
                        # Prepare data in the format expected by the database
                        db_kbar_data = {
                            'timestamp': timestamp,
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price,
                            'volume': volume
                        }
                        
                        # Store the kbar data
                        self.db_manager.store_kbar_data(symbol, exchange, period, db_kbar_data)
                        db_status = "stored"
                        self.logger.debug(f"Stored kbar data for {symbol}.{exchange} in database")
                    
                except Exception as db_error:
                    db_status = f"error: {str(db_error)}"
                    self.logger.error(f"Failed to store kbar data in database: {db_error}")
            
            # Add database status to response
            processed_data['database_status'] = db_status
            
            # Perform Chan analysis if enabled
            chan_analysis = None
            if self.chan_enabled:
                try:
                    chan_indicator = self._get_or_create_chan_indicator(symbol, exchange, period)
                    if chan_indicator:
                        chan_result = chan_indicator.onKbar({
                            'timestamp': timestamp,
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price,
                            'volume': volume
                        })
                        
                        if chan_result.get('status') == 'success':
                            chan_analysis = chan_result.get('analysis_results', {})
                            self.logger.debug(f"Chan analysis completed for {symbol}.{exchange}")
                        else:
                            self.logger.warning(f"Chan analysis failed: {chan_result.get('message', 'Unknown error')}")
                    
                except Exception as chan_error:
                    self.logger.error(f"Error in Chan analysis: {chan_error}")
            
            # Add Chan analysis to response
            processed_data['chan_analysis'] = chan_analysis
            
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
            exchange = message.get('exchange', 'SH')  # Default to Shanghai exchange
            raw_period = message.get('period', '1min')  # Default to 1-minute period
            
            # Convert period code to proper period string
            period = self._convert_period_code_to_string(raw_period)
            
            # debug print
            print(f"Received kbar series: \nsymbol={symbol}, exchange={exchange}, period={period}, count={len(series_data)}")

            processed_series = []
            for kbar in series_data:
                processed_kbar = {
                    'timestamp': kbar.get('timestamp', ''),
                    'open': round(kbar.get('open', 0), 3),
                    'high': round(kbar.get('high', 0), 3),
                    'low': round(kbar.get('low', 0), 3),
                    'close': round(kbar.get('close', 0), 3),
                    'volume': kbar.get('volume', 0)
                }
                processed_series.append(processed_kbar)
            
            # debug print - only print the last kbar
            if processed_series:
                last_kbar = processed_series[-1]
                print(f"Processed last kbar: timestamp={last_kbar['timestamp']}, "
                      f"open={last_kbar['open']:.2f}, "
                      f"high={last_kbar['high']:.2f}, "
                      f"low={last_kbar['low']:.2f}, "
                      f"close={last_kbar['close']:.2f}, "
                      f"volume={last_kbar['volume']}")

            # Store in database if available
            db_status = "not_available"
            if self.db_manager and processed_series:
                try:
                    # Ensure stock exists in database
                    stock_name = message.get('name', symbol)
                    if not self.setup_stock_if_needed(symbol, exchange, stock_name):
                        db_status = "error: failed to setup stock"
                    else:
                        # Convert processed series to DataFrame for database storage
                        df_data = []
                        for kbar in processed_series:
                            df_data.append({
                                'timestamp': kbar['timestamp'],
                                'open': kbar['open'],
                                'high': kbar['high'],
                                'low': kbar['low'],
                                'close': kbar['close'],
                                'volume': kbar['volume']
                            })
                        
                        # Create DataFrame
                        df = pd.DataFrame(df_data)
                        
                        # Store the kbar series data
                        self.db_manager.store_kbar_data(symbol, exchange, period, df)
                        db_status = "stored"
                        self.logger.info(f"Stored {len(processed_series)} kbar records for {symbol}.{exchange} ({period}) in database")
                    
                except Exception as db_error:
                    db_status = f"error: {str(db_error)}"
                    self.logger.error(f"Failed to store kbar series in database: {db_error}")

            # Perform Chan analysis if enabled
            chan_analysis = None
            if self.chan_enabled and processed_series:
                try:
                    chan_indicator = self._get_or_create_chan_indicator(symbol, exchange, period)
                    if chan_indicator:
                        # For series data, we process the last kbar for Chan analysis
                        last_kbar = processed_series[-1]
                        chan_result = chan_indicator.onKbar({
                            'timestamp': last_kbar['timestamp'],
                            'open': last_kbar['open'],
                            'high': last_kbar['high'],
                            'low': last_kbar['low'],
                            'close': last_kbar['close'],
                            'volume': last_kbar['volume']
                        })
                        
                        if chan_result.get('status') == 'success':
                            chan_analysis = chan_result.get('analysis_results', {})
                            self.logger.debug(f"Chan analysis completed for {symbol}.{exchange} series")
                        else:
                            self.logger.warning(f"Chan analysis failed for series: {chan_result.get('message', 'Unknown error')}")
                    
                except Exception as chan_error:
                    self.logger.error(f"Error in Chan analysis for series: {chan_error}")

            return {
                'status': 'success',
                'type': 'kbar_series_response',
                'symbol': symbol,
                'exchange': exchange,
                'period': period,
                'data': processed_series,
                'count': len(processed_series),
                'database_status': db_status,
                'chan_analysis': chan_analysis,
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
                        'parameter_count': len(self.server_params),
                        'database_available': self.db_manager is not None,
                        'chan_enabled': self.chan_enabled,
                        'chan_indicators_count': len(self.chan_indicators),
                        'chan_available': CHAN_INDICATOR_AVAILABLE
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
            elif control_type == 'database_stats':
                if not self.db_manager:
                    return {
                        'status': 'error',
                        'message': 'Database manager not available',
                        'timestamp': datetime.now().isoformat()
                    }
                
                try:
                    stats = self.db_manager.get_database_stats()
                    return {
                        'status': 'success',
                        'type': 'control_response',
                        'database_stats': stats,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        'status': 'error',
                        'message': f'Failed to get database stats: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }
                    
            elif control_type == 'get_symbols':
                if not self.db_manager:
                    return {
                        'status': 'error',
                        'message': 'Database manager not available',
                        'timestamp': datetime.now().isoformat()
                    }
                
                try:
                    symbols = self.db_manager.get_symbols_with_data()
                    return {
                        'status': 'success',
                        'type': 'control_response',
                        'symbols': symbols,
                        'count': len(symbols),
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        'status': 'error',
                        'message': f'Failed to get symbols: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }
                    
            elif control_type == 'get_chan_analysis':
                symbol = parameters.get('symbol', '')
                exchange = parameters.get('exchange', 'SH')
                period = parameters.get('period', '1min')
                
                if not symbol:
                    return {
                        'status': 'error',
                        'message': 'Symbol parameter required',
                        'timestamp': datetime.now().isoformat()
                    }
                
                try:
                    chan_indicator = self._get_or_create_chan_indicator(symbol, exchange, period)
                    if chan_indicator:
                        analysis_results = chan_indicator.get_analysis_results()
                        return {
                            'status': 'success',
                            'type': 'control_response',
                            'chan_analysis': analysis_results,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': 'Chan indicator not available or disabled',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                except Exception as e:
                    return {
                        'status': 'error',
                        'message': f'Failed to get Chan analysis: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }
                    
            elif control_type == 'enable_chan':
                self.chan_enabled = True
                return {
                    'status': 'success',
                    'type': 'control_response',
                    'message': 'Chan analysis enabled',
                    'timestamp': datetime.now().isoformat()
                }
                
            elif control_type == 'disable_chan':
                self.chan_enabled = False
                return {
                    'status': 'success',
                    'type': 'control_response',
                    'message': 'Chan analysis disabled',
                    'timestamp': datetime.now().isoformat()
                }
                
            elif control_type == 'reset_chan_analysis':
                symbol = parameters.get('symbol', '')
                exchange = parameters.get('exchange', 'SH')
                period = parameters.get('period', '1min')
                
                if symbol:
                    # Reset specific symbol
                    indicator_key = f"{symbol}.{exchange}.{period}"
                    if indicator_key in self.chan_indicators:
                        self.chan_indicators[indicator_key].reset_analysis()
                        return {
                            'status': 'success',
                            'type': 'control_response',
                            'message': f'Chan analysis reset for {symbol}.{exchange} ({period})',
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f'No Chan indicator found for {symbol}.{exchange} ({period})',
                            'timestamp': datetime.now().isoformat()
                        }
                else:
                    # Reset all indicators
                    for indicator in self.chan_indicators.values():
                        indicator.reset_analysis()
                    return {
                        'status': 'success',
                        'type': 'control_response',
                        'message': f'Chan analysis reset for all {len(self.chan_indicators)} indicators',
                        'timestamp': datetime.now().isoformat()
                    }
                    
            elif control_type == 'get_chan_indicators':
                indicator_list = []
                for key, indicator in self.chan_indicators.items():
                    parts = key.split('.')
                    if len(parts) >= 3:
                        symbol = parts[0]
                        exchange = parts[1]
                        period = '.'.join(parts[2:])
                        
                        indicator_list.append({
                            'symbol': symbol,
                            'exchange': exchange,
                            'period': period,
                            'key': key,
                            'data_summary': indicator._get_data_summary()
                        })
                
                return {
                    'status': 'success',
                    'type': 'control_response',
                    'chan_indicators': indicator_list,
                    'total_indicators': len(indicator_list),
                    'chan_enabled': self.chan_enabled,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown control type: {control_type}',
                    'available_controls': ['set_param', 'get_param', 'get_all_params', 'server_info', 'database_stats', 'get_symbols', 'get_chan_analysis', 'enable_chan', 'disable_chan', 'reset_chan_analysis', 'get_chan_indicators'],
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
    
    def setup_stock_if_needed(self, symbol: str, exchange: str, name: Optional[str] = None) -> bool:
        """
        Setup stock in database if it doesn't exist
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            name: Stock name (optional, defaults to symbol if not provided)
            
        Returns:
            True if stock was setup successfully or already exists, False otherwise
        """
        if not self.db_manager:
            self.logger.warning("Database manager not available for stock setup")
            return False
            
        try:
            # Check if stock already exists
            stock_info = self.db_manager.get_stock_info(symbol, exchange)
            if stock_info:
                self.logger.debug(f"Stock {symbol}.{exchange} already exists in database")
                return True
            
            # Setup new stock
            stock_name = name if name is not None else symbol
            stock_id = self.db_manager.setup_stock(symbol, exchange, stock_name)
            self.logger.info(f"Setup new stock {symbol}.{exchange} with ID {stock_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup stock {symbol}.{exchange}: {e}")
            return False
    
    def _convert_period_code_to_string(self, period: Union[str, int]) -> str:
        """
        Convert period code to standard period string format.
        This is equivalent to the C++ ConvertPeriodToStr function.
        
        Args:
            period: Period code (as string or int) or period string to convert
            
        Returns:
            Standard period string (e.g., "1min", "5min", "daily", etc.)
        """
        # If it's already a proper period string, return as-is
        if isinstance(period, str):
            if period in ["1min", "5min", "15min", "30min", "1hour", "daily", "weekly", "monthly", "yearly", "quarterly", "5sec", "1sec"]:
                return period
        
        # Try to convert to integer code
        try:
            if isinstance(period, str):
                period_code = int(period)  # Keep as 1-based to match TDX client
            else:
                period_code = int(period)
        except (ValueError, TypeError):
            # If conversion fails, default to daily
            self.logger.warning(f"Unknown period format: {period}, defaulting to daily")
            return "daily"
        
        # Convert period code to standard period string
        # Based on TDX period codes: 1-based indexing to match client
        period_mapping = {
            1: "1min",      # M1 - 1 minute
            2: "5min",      # M5 - 5 minutes  
            3: "15min",     # M15 - 15 minutes
            4: "30min",     # M30 - 30 minutes
            5: "1hour",     # H1 - 1 hour
            6: "daily",     # Day - daily
            7: "weekly",    # Week - weekly
            8: "monthly",   # Month - monthly
            9: "1min",      # M-Min - multi-minute (default to 1min)
            10: "daily",    # M-Day - multi-day (default to daily)
            11: "quarterly", # Season - quarterly
            12: "yearly",   # Year - yearly
            13: "5sec",     # Sec5 - 5 seconds
            14: "1sec",     # M-Sec - multi-second (default to 1sec)
        }
        
        result = period_mapping.get(period_code, "daily")
        self.logger.debug(f"Converted period code {period} to {result}")
        return result

    def _get_or_create_chan_indicator(self, symbol: str, exchange: str, period: str):
        """
        Get or create Chan indicator for a symbol
        
        Args:
            symbol: Stock symbol
            exchange: Exchange code
            period: Time period
            
        Returns:
            ChanIndicator instance or None if not available
        """
        if not self.chan_enabled or not CHAN_INDICATOR_AVAILABLE:
            return None
            
        if not self.db_manager:
            self.logger.warning("Database manager not available for Chan indicator")
            return None
        
        # Create unique key for this symbol/exchange/period combination
        indicator_key = f"{symbol}.{exchange}.{period}"
        
        # Return existing indicator if available
        if indicator_key in self.chan_indicators:
            return self.chan_indicators[indicator_key]
        
        try:
            # Create new Chan indicator
            if ChanIndicator is None:
                raise ImportError("ChanIndicator class not available")
                
            chan_indicator = ChanIndicator(
                db_manager=self.db_manager,
                symbol=symbol,
                exchange=exchange,
                period=period
            )
            
            self.chan_indicators[indicator_key] = chan_indicator
            self.logger.info(f"Created Chan indicator for {symbol}.{exchange} ({period})")
            
            return chan_indicator
            
        except Exception as e:
            self.logger.error(f"Failed to create Chan indicator for {symbol}.{exchange}: {e}")
            return None


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

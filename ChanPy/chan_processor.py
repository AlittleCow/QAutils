"""
Chan Algorithm Processor

This module coordinates all Chan algorithm components to implement the complete
Chan analysis process as specified:

1. Merge kbar process for two consecutive kbars
2. Check two consecutive merged kbars to identify top/bottom fractals  
3. Process raw kbars from start fractal to end fractal to identify chanpen
4. Process chanpen breaking type and breaking status, form chanlines based on standards
"""

import logging
from typing import List, Dict, Any, Optional
from .mergekbar import KbarMerger, MergedKbar
from .fractal import FractalIdentifier, Fractal
from .pen import PenProcessor, ChanPen
from .line import LineProcessor, ChanLine
from .chan import Kbar  # Import Kbar from existing chan module


class ChanProcessor:
    """
    Main Chan Algorithm Processor
    
    Coordinates all components to perform complete Chan analysis following
    the specified four-step process.
    """
    
    def __init__(self, 
                 strict_fractal_mode: bool = True,
                 min_pen_length: float = 0.0,
                 min_kbar_count: int = 5,
                 min_line_pens: int = 3):
        """
        Initialize Chan Processor
        
        Args:
            strict_fractal_mode: Use strict fractal identification rules
            min_pen_length: Minimum pen length for validation
            min_kbar_count: Minimum kbars for valid pen
            min_line_pens: Minimum pens for valid line
        """
        self.logger = logging.getLogger(f"{__name__}")
        
        # Initialize all processors
        self.kbar_merger = KbarMerger()
        self.fractal_identifier = FractalIdentifier(strict_mode=strict_fractal_mode)
        self.pen_processor = PenProcessor(
            min_pen_length=min_pen_length, 
            min_kbar_count=min_kbar_count
        )
        self.line_processor = LineProcessor(min_line_pens=min_line_pens)
        
        # Data storage
        self.raw_kbars: List[Kbar] = []
        self.merged_kbars: List[MergedKbar] = []
        self.fractals: List[Fractal] = []
        self.pens: List[ChanPen] = []
        self.lines: List[ChanLine] = []
        
        self.logger.info("ChanProcessor initialized with all components")
    
    def process_kbars(self, kbars: List[Kbar]) -> Dict[str, Any]:
        """
        Process raw kbars through the complete Chan algorithm pipeline
        
        Args:
            kbars: List of raw kbars in chronological order
            
        Returns:
            Complete analysis results
        """
        self.raw_kbars = kbars
        results = {}
        
        try:
            # Step 1: Merge kbar process for consecutive kbars
            self.logger.info("Step 1: Processing kbar merging")
            self.merged_kbars = self.kbar_merger.process_kbar_sequence(kbars)
            results['step1_merge'] = {
                'original_kbars': len(kbars),
                'merged_kbars': len(self.merged_kbars),
                'compression_ratio': len(self.merged_kbars) / len(kbars) if kbars else 0
            }
            
            if len(self.merged_kbars) < 3:
                self.logger.warning("Insufficient merged kbars for fractal analysis")
                return self._build_results(results, "Insufficient merged kbars")
            
            # Step 2: Check consecutive merged kbars for fractals
            self.logger.info("Step 2: Identifying fractals from merged kbars")  
            self.fractals = self.fractal_identifier.process_merged_kbars(self.merged_kbars)
            results['step2_fractals'] = {
                'total_fractals': len(self.fractals),
                'top_fractals': len(self.fractal_identifier.get_top_fractals()),
                'bottom_fractals': len(self.fractal_identifier.get_bottom_fractals()),
                'fractal_summary': self.fractal_identifier.get_fractal_summary()
            }
            
            if len(self.fractals) < 2:
                self.logger.warning("Insufficient fractals for pen analysis")
                return self._build_results(results, "Insufficient fractals")
            
            # Step 3: Process raw kbars from fractal to fractal to identify chanpen
            self.logger.info("Step 3: Creating pens from fractals with raw kbar validation")
            self.pen_processor.set_raw_kbars(kbars)
            self.pens = self.pen_processor.process_fractals(self.fractals)
            results['step3_pens'] = {
                'total_pens': len(self.pens),
                'upward_pens': len(self.pen_processor.get_upward_pens()),
                'downward_pens': len(self.pen_processor.get_downward_pens()),
                'pen_statistics': self.pen_processor.get_pen_statistics()
            }
            
            if len(self.pens) < 3:
                self.logger.warning("Insufficient pens for line analysis")
                return self._build_results(results, "Insufficient pens")
            
            # Step 4: Process chanpen breaking and chanline formation
            self.logger.info("Step 4: Forming lines and analyzing breaking patterns")
            self.lines = self.line_processor.process_pens(self.pens)
            
            # Analyze pen breaking for existing lines
            if self.lines:
                for line in self.lines:
                    recent_pens = self.pens[-3:] if len(self.pens) >= 3 else self.pens
                    break_type = self.line_processor.analyze_line_breaking(line, recent_pens)
                    if break_type.value > 0:  # Some breaking detected
                        self.logger.info(f"Line breaking detected: {break_type.name} for "
                                       f"{line.direction.name} line")
                
                # Update global line status
                recent_pens = self.pens[-5:] if len(self.pens) >= 5 else self.pens
                self.line_processor.update_global_line_status(recent_pens)
            
            results['step4_lines'] = {
                'total_lines': len(self.lines),
                'upward_lines': len(self.line_processor.get_upward_lines()),
                'downward_lines': len(self.line_processor.get_downward_lines()),
                'broken_lines': len(self.line_processor.get_broken_lines()),
                'global_line_info': self._get_global_line_info(),
                'line_statistics': self.line_processor.get_line_statistics()
            }
            
            return self._build_results(results, "Success")
            
        except Exception as e:
            self.logger.error(f"Error in Chan processing: {e}")
            return self._build_results(results, f"Error: {str(e)}")
    
    def process_new_kbar(self, new_kbar: Kbar) -> Dict[str, Any]:
        """
        Process a single new kbar incrementally
        
        Args:
            new_kbar: New kbar to process
            
        Returns:
            Incremental analysis results
        """
        self.raw_kbars.append(new_kbar)
        
        # For incremental processing, we'll re-process the last N kbars
        # In a production system, this could be optimized for true incremental processing
        recent_kbars = self.raw_kbars[-100:] if len(self.raw_kbars) > 100 else self.raw_kbars
        
        return self.process_kbars(recent_kbars)
    
    def analyze_current_market_state(self, current_price: float) -> Dict[str, Any]:
        """
        Analyze current market state based on existing structures
        
        Args:
            current_price: Current market price
            
        Returns:
            Current market analysis
        """
        analysis = {
            'current_price': current_price,
            'latest_fractal': None,
            'latest_pen': None,
            'latest_line': None,
            'global_line': None,
            'breaking_analysis': {}
        }
        
        # Latest fractal analysis
        if self.fractals:
            latest_fractal = self.fractals[-1]
            analysis['latest_fractal'] = {
                'type': latest_fractal.fractal_type.name,
                'price': latest_fractal.price,
                'timestamp': latest_fractal.timestamp,
                'strength': latest_fractal.strength
            }
        
        # Latest pen analysis
        if self.pens:
            latest_pen = self.pens[-1]
            analysis['latest_pen'] = {
                'direction': latest_pen.direction.name,
                'start_price': latest_pen.start_price,
                'end_price': latest_pen.end_price,
                'length': latest_pen.length,
                'confirmed': latest_pen.confirmed
            }
            
            # Analyze pen breaking
            break_type = self.pen_processor.analyze_pen_breaking(latest_pen, current_price)
            analysis['breaking_analysis']['pen_breaking'] = break_type.name
        
        # Latest line analysis  
        if self.lines:
            latest_line = self.lines[-1]
            analysis['latest_line'] = {
                'direction': latest_line.direction.name,
                'status': latest_line.status.name,
                'pen_count': latest_line.pen_count,
                'length': latest_line.length
            }
        
        # Global line analysis
        global_line = self.line_processor.get_global_line()
        if global_line:
            analysis['global_line'] = {
                'direction': global_line.direction.name,
                'status': global_line.status.name,
                'broken': global_line.status.name == 'BROKEN',
                'break_price': global_line.break_price
            }
        
        return analysis
    
    def _get_global_line_info(self) -> Dict[str, Any]:
        """Get information about the global line"""
        global_line = self.line_processor.get_global_line()
        if not global_line:
            return {'exists': False}
        
        return {
            'exists': True,
            'direction': global_line.direction.name,
            'status': global_line.status.name,
            'start_time': global_line.start_time,
            'end_time': global_line.end_time,
            'pen_count': global_line.pen_count,
            'length': global_line.length,
            'broken': global_line.status.name == 'BROKEN',
            'break_price': global_line.break_price,
            'break_type': global_line.break_type.name if global_line.break_type else None
        }
    
    def _build_results(self, results: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Build comprehensive results dictionary"""
        global_line = self.line_processor.get_global_line()
        return {
            'status': status,
            'processing_steps': results,
            'summary': {
                'raw_kbars': len(self.raw_kbars),
                'merged_kbars': len(self.merged_kbars),
                'fractals': len(self.fractals),
                'pens': len(self.pens),
                'lines': len(self.lines),
                'global_line_active': (
                    global_line is not None and 
                    global_line.status.name != 'BROKEN'
                )
            },
            'latest_structures': self._get_latest_structures()
        }
    
    def _get_latest_structures(self) -> Dict[str, Any]:
        """Get latest identified structures"""
        return {
            'latest_fractal': {
                'type': self.fractals[-1].fractal_type.name if self.fractals else None,
                'price': self.fractals[-1].price if self.fractals else None,
                'strength': self.fractals[-1].strength if self.fractals else None
            } if self.fractals else None,
            
            'latest_pen': {
                'direction': self.pens[-1].direction.name if self.pens else None,
                'length': self.pens[-1].length if self.pens else None,
                'kbar_count': self.pens[-1].kbar_count if self.pens else None
            } if self.pens else None,
            
            'latest_line': {
                'direction': self.lines[-1].direction.name if self.lines else None,
                'pen_count': self.lines[-1].pen_count if self.lines else None,
                'status': self.lines[-1].status.name if self.lines else None
            } if self.lines else None
        }
    
    def get_complete_analysis(self) -> Dict[str, Any]:
        """
        Get complete analysis of all identified structures
        
        Returns:
            Complete analysis dictionary
        """
        return {
            'merged_kbars': [
                {
                    'timestamp_start': mkbar.timestamp_start,
                    'timestamp_end': mkbar.timestamp_end,
                    'high': mkbar.high,
                    'low': mkbar.low,
                    'close': mkbar.close,
                    'original_count': mkbar.original_count
                } for mkbar in self.merged_kbars[-10:]  # Last 10 merged kbars
            ],
            
            'fractals': [
                {
                    'index': fractal.index,
                    'timestamp': fractal.timestamp,
                    'type': fractal.fractal_type.name,
                    'price': fractal.price,
                    'strength': fractal.strength
                } for fractal in self.fractals[-10:]  # Last 10 fractals
            ],
            
            'pens': [
                {
                    'direction': pen.direction.name,
                    'start_price': pen.start_price,
                    'end_price': pen.end_price,
                    'length': pen.length,
                    'start_time': pen.start_time,
                    'end_time': pen.end_time,
                    'kbar_count': pen.kbar_count,
                    'break_type': pen.break_type.name
                } for pen in self.pens[-5:]  # Last 5 pens
            ],
            
            'lines': [
                {
                    'direction': line.direction.name,
                    'pen_count': line.pen_count,
                    'length': line.length,
                    'status': line.status.name,
                    'start_time': line.start_time,
                    'end_time': line.end_time,
                    'break_type': line.break_type.name,
                    'is_global': line.is_global
                } for line in self.lines
            ],
            
            'statistics': {
                'fractal_stats': self.fractal_identifier.get_fractal_summary(),
                'pen_stats': self.pen_processor.get_pen_statistics(),
                'line_stats': self.line_processor.get_line_statistics()
            }
        }
    
    def clear_all(self):
        """Clear all analysis data"""
        self.raw_kbars.clear()
        self.merged_kbars.clear()
        self.fractals.clear()
        self.pens.clear()
        self.lines.clear()
        
        self.kbar_merger.clear()
        self.fractal_identifier.clear()
        self.pen_processor.clear()
        self.line_processor.clear()
        
        self.logger.info("Cleared all Chan analysis data")
    
    def set_parameters(self, **kwargs):
        """
        Set parameters for all processors
        
        Args:
            **kwargs: Parameter name-value pairs
        """
        # Fractal parameters
        if 'min_fractal_strength' in kwargs:
            self.fractal_identifier.set_minimum_strength(kwargs['min_fractal_strength'])
        
        # Pen parameters
        pen_params = {}
        if 'min_pen_length' in kwargs:
            pen_params['min_pen_length'] = kwargs['min_pen_length']
        if 'min_kbar_count' in kwargs:
            pen_params['min_kbar_count'] = kwargs['min_kbar_count']
        if pen_params:
            self.pen_processor.set_parameters(**pen_params)
        
        # Line parameters
        line_params = {}
        if 'min_line_pens' in kwargs:
            line_params['min_line_pens'] = kwargs['min_line_pens']
        if 'break_confirmation_pens' in kwargs:
            line_params['break_confirmation_pens'] = kwargs['break_confirmation_pens']
        if line_params:
            self.line_processor.set_parameters(**line_params)
        
        self.logger.info(f"Updated Chan processor parameters: {kwargs}")

    def validate_analysis_integrity(self) -> Dict[str, bool]:
        """
        Validate the integrity of the complete analysis
        
        Returns:
            Dictionary with validation results
        """
        return {
            'fractal_sequence_valid': self.fractal_identifier.validate_fractal_sequence(),
            'pen_sequence_valid': self.pen_processor.get_pen_sequence_validity(),
            'line_sequence_valid': self.line_processor.validate_line_sequence(),
            'overall_valid': (
                self.fractal_identifier.validate_fractal_sequence() and
                self.pen_processor.get_pen_sequence_validity() and
                self.line_processor.validate_line_sequence()
            )
        } 
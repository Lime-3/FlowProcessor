"""
Processing Controller for handling data processing workflows.

This controller manages the processing workflow, including:
- Data parsing and validation
- Processing pipeline coordination
- Result handling and export
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot

from ....domain.parsing.service import ParseService
from ....domain.processing.service import DataProcessingService
from ....domain.export.service import ExportService
from ....core.models import ProcessingOptions, ProcessingResult

logger = logging.getLogger(__name__)


class ProcessingController(QObject):
    """
    Controller for managing data processing workflows.
    
    This controller coordinates between the GUI and the domain services
    to handle the complete processing pipeline.
    """
    
    # Signals
    parsing_started = Signal()
    parsing_completed = Signal(dict)
    parsing_error = Signal(str)
    
    processing_started = Signal()
    processing_completed = Signal(dict)
    processing_error = Signal(str)
    
    export_started = Signal()
    export_completed = Signal(str)
    export_error = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # Initialize domain services
        self.parse_service = ParseService()
        self.processing_service = DataProcessingService()
        self.export_service = ExportService()
        
        # Processing state
        self.current_data = None
        self.processing_options = None
        
    def parse_input_files(self, input_paths: List[Path], 
                         options: ProcessingOptions) -> bool:
        """
        Parse input files and prepare data for processing.
        
        Args:
            input_paths: List of input file paths
            options: Processing options and configuration
            
        Returns:
            True if parsing was successful, False otherwise
        """
        try:
            self.parsing_started.emit()
            logger.info(f"Starting to parse {len(input_paths)} input files")
            
            # Parse the input files
            parsed_data = self.parse_service.parse_files(
                file_paths=input_paths,
                options=options
            )
            
            if parsed_data is None or not parsed_data:
                self.parsing_error.emit("No valid data found in input files")
                return False
                
            self.current_data = parsed_data
            self.processing_options = options
            
            self.parsing_completed.emit({
                "file_count": len(input_paths),
                "data_shape": self._get_data_shape(parsed_data),
                "columns": self._get_data_columns(parsed_data)
            })
            
            logger.info("Parsing completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Parsing error: {e}")
            self.parsing_error.emit(f"Parsing failed: {str(e)}")
            return False
            
    def process_data(self) -> bool:
        """
        Process the parsed data according to the current options.
        
        Returns:
            True if processing was successful, False otherwise
        """
        if self.current_data is None:
            self.processing_error.emit("No data available for processing")
            return False
            
        try:
            self.processing_started.emit()
            logger.info("Starting data processing")
            
            # Process the data
            processed_data = self.processing_service.process_data(
                data=self.current_data,
                options=self.processing_options
            )
            
            if processed_data is None:
                self.processing_error.emit("Processing failed to produce valid results")
                return False
                
            # Update current data with processed results
            self.current_data = processed_data
            
            self.processing_completed.emit({
                "processed_count": len(processed_data) if hasattr(processed_data, '__len__') else 1,
                "metrics": self._get_processing_metrics(processed_data)
            })
            
            logger.info("Data processing completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.processing_error.emit(f"Processing failed: {str(e)}")
            return False
            
    def export_results(self, output_path: Path, format_type: str = "excel") -> bool:
        """
        Export the processed results to the specified output location.
        
        Args:
            output_path: Path where to save the exported results
            format_type: Type of export format (excel, csv, etc.)
            
        Returns:
            True if export was successful, False otherwise
        """
        if self.current_data is None:
            self.export_error.emit("No processed data available for export")
            return False
            
        try:
            self.export_started.emit()
            logger.info(f"Starting export to {output_path}")
            
            # Export the data
            export_result = self.export_service.export_data(
                data=self.current_data,
                output_path=output_path,
                format_type=format_type,
                options=self.processing_options
            )
            
            if not export_result.success:
                self.export_error.emit(f"Export failed: {export_result.error_message}")
                return False
                
            self.export_completed.emit(str(output_path))
            logger.info("Export completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            self.export_error.emit(f"Export failed: {str(e)}")
            return False
            
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current processing state.
        
        Returns:
            Dictionary containing processing summary information
        """
        summary = {
            "has_data": self.current_data is not None,
            "has_options": self.processing_options is not None,
            "data_shape": self._get_data_shape(self.current_data) if self.current_data else None,
            "options": self.processing_options.to_dict() if self.processing_options else None
        }
        
        return summary
        
    def clear_data(self) -> None:
        """Clear the current data and reset the controller state."""
        self.current_data = None
        self.processing_options = None
        logger.info("Processing controller data cleared")
        
    def _get_data_shape(self, data) -> Optional[tuple]:
        """Get the shape of the data if it's a DataFrame or similar."""
        if hasattr(data, 'shape'):
            return data.shape
        elif hasattr(data, '__len__'):
            return (len(data),)
        return None
        
    def _get_data_columns(self, data) -> Optional[List[str]]:
        """Get the column names if the data has columns."""
        if hasattr(data, 'columns'):
            return list(data.columns)
        return None
        
    def _get_processing_metrics(self, data) -> Dict[str, Any]:
        """Get processing metrics from the processed data."""
        metrics = {}
        
        if hasattr(data, 'shape'):
            metrics['rows'] = data.shape[0]
            metrics['columns'] = data.shape[1]
            
        if hasattr(data, 'describe'):
            try:
                desc = data.describe()
                metrics['summary'] = desc.to_dict()
            except:
                pass
                
        return metrics
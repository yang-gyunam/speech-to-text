"""
Text export functionality for speech-to-text application.

This module provides classes and methods for saving transcription results
to various text formats with proper encoding and metadata support.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import TranscriptionResult
from .exceptions import FileSystemError


class TextExporter:
    """
    Handles exporting transcription results to text files.
    
    Supports saving transcribed text with metadata, creating summary reports,
    and handling various output formats with proper encoding.
    """
    
    DEFAULT_ENCODING = 'utf-8'
    
    def __init__(self, encoding: str = DEFAULT_ENCODING):
        """
        Initialize TextExporter.
        
        Args:
            encoding: Text encoding to use for output files (default: utf-8)
        """
        self.encoding = encoding
    
    def save_as_txt(self, text: str, output_path: str, 
                   include_metadata: bool = False, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save transcribed text as a plain text file.
        
        Args:
            text: The transcribed text content
            output_path: Path where the text file will be saved
            include_metadata: Whether to include metadata in the file
            metadata: Optional metadata dictionary to include
            
        Returns:
            Absolute path to the saved file
            
        Raises:
            FileSystemError: If file saving fails
        """
        try:
            output_file = Path(output_path)
            
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare content
            content = text
            
            if include_metadata and metadata:
                content = self._add_metadata_to_text(text, metadata)
            
            # Write file with proper encoding
            with open(output_file, 'w', encoding=self.encoding) as f:
                f.write(content)
            
            return str(output_file.resolve())
            
        except Exception as e:
            raise FileSystemError(f"Failed to save text file {output_path}: {str(e)}")
    
    def save_transcription_result(self, result: TranscriptionResult, 
                                output_path: str, 
                                include_metadata: bool = True) -> str:
        """
        Save a TranscriptionResult to a text file.
        
        Args:
            result: TranscriptionResult object to save
            output_path: Path where the text file will be saved
            include_metadata: Whether to include metadata in the file
            
        Returns:
            Absolute path to the saved file
            
        Raises:
            FileSystemError: If file saving fails
        """
        try:
            metadata = self._extract_metadata_from_result(result)
            
            return self.save_as_txt(
                text=result.transcribed_text,
                output_path=output_path,
                include_metadata=include_metadata,
                metadata=metadata
            )
            
        except Exception as e:
            raise FileSystemError(f"Failed to save transcription result to {output_path}: {str(e)}")
    
    def save_with_metadata(self, result: TranscriptionResult, output_path: str) -> str:
        """
        Save transcription result with detailed metadata.
        
        Args:
            result: TranscriptionResult object to save
            output_path: Path where the text file will be saved
            
        Returns:
            Absolute path to the saved file
            
        Raises:
            FileSystemError: If file saving fails
        """
        return self.save_transcription_result(result, output_path, include_metadata=True)
    
    def save_as_json(self, result: TranscriptionResult, output_path: str) -> str:
        """
        Save transcription result as JSON file.
        
        Args:
            result: TranscriptionResult object to save
            output_path: Path where the JSON file will be saved
            
        Returns:
            Absolute path to the saved file
            
        Raises:
            FileSystemError: If file saving fails
        """
        try:
            output_file = Path(output_path)
            
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert result to dictionary
            result_dict = {
                'original_file': result.original_file,
                'transcribed_text': result.transcribed_text,
                'language': result.language,
                'confidence_score': result.confidence_score,
                'processing_time': result.processing_time,
                'timestamp': result.timestamp.isoformat(),
                'error_message': result.error_message
            }
            
            # Write JSON file
            with open(output_file, 'w', encoding=self.encoding) as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            return str(output_file.resolve())
            
        except Exception as e:
            raise FileSystemError(f"Failed to save JSON file {output_path}: {str(e)}")
    
    def create_summary_report(self, results: List[TranscriptionResult], 
                            output_path: str) -> str:
        """
        Create a summary report for multiple transcription results.
        
        Args:
            results: List of TranscriptionResult objects
            output_path: Path where the summary report will be saved
            
        Returns:
            Absolute path to the saved report
            
        Raises:
            FileSystemError: If report creation fails
        """
        try:
            output_file = Path(output_path)
            
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate summary content
            summary_content = self._generate_summary_content(results)
            
            # Write summary file
            with open(output_file, 'w', encoding=self.encoding) as f:
                f.write(summary_content)
            
            return str(output_file.resolve())
            
        except Exception as e:
            raise FileSystemError(f"Failed to create summary report {output_path}: {str(e)}")
    
    def save_batch_results(self, results: List[TranscriptionResult], 
                          output_dir: str, 
                          create_summary: bool = True) -> Dict[str, str]:
        """
        Save multiple transcription results to individual files.
        
        Args:
            results: List of TranscriptionResult objects
            output_dir: Directory where files will be saved
            create_summary: Whether to create a summary report
            
        Returns:
            Dictionary mapping original file paths to output file paths
            
        Raises:
            FileSystemError: If batch saving fails
        """
        try:
            output_directory = Path(output_dir)
            output_directory.mkdir(parents=True, exist_ok=True)
            
            saved_files = {}
            
            # Save individual results
            for result in results:
                if result.error_message:
                    # Skip failed transcriptions
                    continue
                
                # Generate output filename
                original_name = Path(result.original_file).stem
                output_filename = f"{original_name}_transcription.txt"
                output_path = output_directory / output_filename
                
                # Save the result
                saved_path = self.save_transcription_result(result, str(output_path))
                saved_files[result.original_file] = saved_path
            
            # Create summary report if requested
            if create_summary:
                summary_path = output_directory / "transcription_summary.txt"
                self.create_summary_report(results, str(summary_path))
                saved_files['_summary'] = str(summary_path)
            
            return saved_files
            
        except Exception as e:
            raise FileSystemError(f"Failed to save batch results to {output_dir}: {str(e)}")
    
    def _extract_metadata_from_result(self, result: TranscriptionResult) -> Dict[str, Any]:
        """
        Extract metadata from TranscriptionResult.
        
        Args:
            result: TranscriptionResult object
            
        Returns:
            Dictionary containing metadata
        """
        return {
            'original_file': result.original_file,
            'language': result.language,
            'confidence_score': result.confidence_score,
            'processing_time': result.processing_time,
            'timestamp': result.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': result.error_message
        }
    
    def _add_metadata_to_text(self, text: str, metadata: Dict[str, Any]) -> str:
        """
        Add metadata header to text content.
        
        Args:
            text: Original text content
            metadata: Metadata dictionary
            
        Returns:
            Text with metadata header
        """
        header_lines = [
            "=" * 50,
            "TRANSCRIPTION METADATA",
            "=" * 50
        ]
        
        for key, value in metadata.items():
            if value is not None:
                header_lines.append(f"{key.replace('_', ' ').title()}: {value}")
        
        header_lines.extend([
            "=" * 50,
            "",
            "TRANSCRIBED TEXT:",
            "-" * 20,
            ""
        ])
        
        return "\n".join(header_lines) + text
    
    def _generate_summary_content(self, results: List[TranscriptionResult]) -> str:
        """
        Generate summary report content.
        
        Args:
            results: List of TranscriptionResult objects
            
        Returns:
            Summary report content as string
        """
        if not results:
            return "No transcription results to summarize.\n"
        
        # Calculate statistics
        total_files = len(results)
        successful_files = len([r for r in results if not r.error_message])
        failed_files = total_files - successful_files
        
        total_processing_time = sum(r.processing_time for r in results if not r.error_message)
        avg_processing_time = total_processing_time / successful_files if successful_files > 0 else 0
        
        avg_confidence = sum(r.confidence_score for r in results if not r.error_message) / successful_files if successful_files > 0 else 0
        
        # Generate report
        report_lines = [
            "TRANSCRIPTION BATCH SUMMARY REPORT",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "STATISTICS:",
            f"  Total files processed: {total_files}",
            f"  Successful transcriptions: {successful_files}",
            f"  Failed transcriptions: {failed_files}",
            f"  Success rate: {(successful_files/total_files*100):.1f}%" if total_files > 0 else "  Success rate: 0.0%",
            "",
            "PERFORMANCE:",
            f"  Total processing time: {total_processing_time:.2f} seconds",
            f"  Average processing time: {avg_processing_time:.2f} seconds",
            f"  Average confidence score: {avg_confidence:.3f}",
            "",
            "FILE DETAILS:",
            "-" * 30
        ]
        
        # Add individual file details
        for i, result in enumerate(results, 1):
            status = "SUCCESS" if not result.error_message else "FAILED"
            file_name = Path(result.original_file).name
            
            report_lines.append(f"{i:3d}. {file_name}")
            report_lines.append(f"     Status: {status}")
            
            if not result.error_message:
                report_lines.append(f"     Language: {result.language}")
                report_lines.append(f"     Confidence: {result.confidence_score:.3f}")
                report_lines.append(f"     Processing time: {result.processing_time:.2f}s")
                report_lines.append(f"     Text length: {len(result.transcribed_text)} characters")
            else:
                report_lines.append(f"     Error: {result.error_message}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
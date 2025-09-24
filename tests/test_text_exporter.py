"""
Unit tests for the TextExporter class.

Tests text export functionality including saving transcription results,
creating summary reports, and handling various output formats.
"""

import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import pytest

from src.speech_to_text.text_exporter import TextExporter
from src.speech_to_text.models import TranscriptionResult
from src.speech_to_text.exceptions import FileSystemError


class TestTextExporter:
    """Test cases for TextExporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.text_exporter = TextExporter()
        
        # Create sample transcription results
        self.sample_result = TranscriptionResult(
            original_file="/path/to/audio.m4a",
            transcribed_text="안녕하세요. 이것은 테스트 음성입니다.",
            language="ko",
            confidence_score=0.95,
            processing_time=12.5,
            timestamp=datetime(2023, 12, 1, 14, 30, 0)
        )
        
        self.failed_result = TranscriptionResult(
            original_file="/path/to/failed.m4a",
            transcribed_text="",
            language="ko",
            confidence_score=0.0,
            processing_time=0.0,
            timestamp=datetime(2023, 12, 1, 14, 35, 0),
            error_message="File not found"
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_default_encoding(self):
        """Test TextExporter initialization with default encoding."""
        exporter = TextExporter()
        assert exporter.encoding == 'utf-8'
    
    def test_init_custom_encoding(self):
        """Test TextExporter initialization with custom encoding."""
        exporter = TextExporter(encoding='utf-16')
        assert exporter.encoding == 'utf-16'
    
    def test_save_as_txt_basic(self):
        """Test saving basic text file."""
        output_path = Path(self.temp_dir) / "output.txt"
        test_text = "Hello, world!"
        
        result_path = self.text_exporter.save_as_txt(test_text, str(output_path))
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == test_text
    
    def test_save_as_txt_with_metadata(self):
        """Test saving text file with metadata."""
        output_path = Path(self.temp_dir) / "output_with_metadata.txt"
        test_text = "Test content"
        metadata = {
            'original_file': 'test.m4a',
            'language': 'ko',
            'confidence_score': 0.95
        }
        
        result_path = self.text_exporter.save_as_txt(
            test_text, str(output_path), 
            include_metadata=True, metadata=metadata
        )
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "TRANSCRIPTION METADATA" in content
        assert "Original File: test.m4a" in content
        assert "Language: ko" in content
        assert "Confidence Score: 0.95" in content
        assert test_text in content
    
    def test_save_as_txt_creates_directory(self):
        """Test that save_as_txt creates output directory."""
        nested_path = Path(self.temp_dir) / "nested" / "dir" / "output.txt"
        test_text = "Test content"
        
        result_path = self.text_exporter.save_as_txt(test_text, str(nested_path))
        
        assert result_path == str(nested_path.resolve())
        assert nested_path.exists()
        assert nested_path.parent.exists()
    
    def test_save_as_txt_permission_error(self):
        """Test save_as_txt with permission error."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            output_path = Path(self.temp_dir) / "output.txt"
            
            with pytest.raises(FileSystemError) as exc_info:
                self.text_exporter.save_as_txt("test", str(output_path))
            
            assert "Failed to save text file" in str(exc_info.value)
    
    def test_save_transcription_result_basic(self):
        """Test saving TranscriptionResult to text file."""
        output_path = Path(self.temp_dir) / "transcription.txt"
        
        result_path = self.text_exporter.save_transcription_result(
            self.sample_result, str(output_path), include_metadata=False
        )
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == self.sample_result.transcribed_text
    
    def test_save_transcription_result_with_metadata(self):
        """Test saving TranscriptionResult with metadata."""
        output_path = Path(self.temp_dir) / "transcription_with_metadata.txt"
        
        result_path = self.text_exporter.save_transcription_result(
            self.sample_result, str(output_path), include_metadata=True
        )
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "TRANSCRIPTION METADATA" in content
        assert self.sample_result.original_file in content
        assert self.sample_result.language in content
        assert str(self.sample_result.confidence_score) in content
        assert self.sample_result.transcribed_text in content
    
    def test_save_with_metadata(self):
        """Test save_with_metadata method."""
        output_path = Path(self.temp_dir) / "with_metadata.txt"
        
        result_path = self.text_exporter.save_with_metadata(self.sample_result, str(output_path))
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "TRANSCRIPTION METADATA" in content
    
    def test_save_as_json(self):
        """Test saving TranscriptionResult as JSON."""
        output_path = Path(self.temp_dir) / "transcription.json"
        
        result_path = self.text_exporter.save_as_json(self.sample_result, str(output_path))
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['original_file'] == self.sample_result.original_file
        assert data['transcribed_text'] == self.sample_result.transcribed_text
        assert data['language'] == self.sample_result.language
        assert data['confidence_score'] == self.sample_result.confidence_score
        assert data['processing_time'] == self.sample_result.processing_time
        assert data['timestamp'] == self.sample_result.timestamp.isoformat()
        assert data['error_message'] == self.sample_result.error_message
    
    def test_save_as_json_creates_directory(self):
        """Test that save_as_json creates output directory."""
        nested_path = Path(self.temp_dir) / "nested" / "transcription.json"
        
        result_path = self.text_exporter.save_as_json(self.sample_result, str(nested_path))
        
        assert result_path == str(nested_path.resolve())
        assert nested_path.exists()
        assert nested_path.parent.exists()
    
    def test_create_summary_report_empty_list(self):
        """Test creating summary report with empty results list."""
        output_path = Path(self.temp_dir) / "summary.txt"
        
        result_path = self.text_exporter.create_summary_report([], str(output_path))
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "No transcription results to summarize" in content
    
    def test_create_summary_report_single_result(self):
        """Test creating summary report with single result."""
        output_path = Path(self.temp_dir) / "summary.txt"
        results = [self.sample_result]
        
        result_path = self.text_exporter.create_summary_report(results, str(output_path))
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "TRANSCRIPTION BATCH SUMMARY REPORT" in content
        assert "Total files processed: 1" in content
        assert "Successful transcriptions: 1" in content
        assert "Failed transcriptions: 0" in content
        assert "Success rate: 100.0%" in content
        assert "audio.m4a" in content
        assert "Status: SUCCESS" in content
    
    def test_create_summary_report_mixed_results(self):
        """Test creating summary report with mixed success/failure results."""
        output_path = Path(self.temp_dir) / "summary.txt"
        results = [self.sample_result, self.failed_result]
        
        result_path = self.text_exporter.create_summary_report(results, str(output_path))
        
        assert result_path == str(output_path.resolve())
        assert output_path.exists()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Total files processed: 2" in content
        assert "Successful transcriptions: 1" in content
        assert "Failed transcriptions: 1" in content
        assert "Success rate: 50.0%" in content
        assert "Status: SUCCESS" in content
        assert "Status: FAILED" in content
        assert "Error: File not found" in content
    
    def test_save_batch_results_success_only(self):
        """Test saving batch results with successful transcriptions only."""
        output_dir = Path(self.temp_dir) / "batch_output"
        results = [self.sample_result]
        
        saved_files = self.text_exporter.save_batch_results(results, str(output_dir))
        
        assert len(saved_files) == 2  # 1 transcription + 1 summary
        assert self.sample_result.original_file in saved_files
        assert '_summary' in saved_files
        
        # Check transcription file
        transcription_file = Path(saved_files[self.sample_result.original_file])
        assert transcription_file.exists()
        
        # Check summary file
        summary_file = Path(saved_files['_summary'])
        assert summary_file.exists()
    
    def test_save_batch_results_with_failures(self):
        """Test saving batch results with some failures."""
        output_dir = Path(self.temp_dir) / "batch_output"
        results = [self.sample_result, self.failed_result]
        
        saved_files = self.text_exporter.save_batch_results(results, str(output_dir))
        
        # Only successful result should be saved, plus summary
        assert len(saved_files) == 2
        assert self.sample_result.original_file in saved_files
        assert self.failed_result.original_file not in saved_files
        assert '_summary' in saved_files
    
    def test_save_batch_results_no_summary(self):
        """Test saving batch results without summary."""
        output_dir = Path(self.temp_dir) / "batch_output"
        results = [self.sample_result]
        
        saved_files = self.text_exporter.save_batch_results(
            results, str(output_dir), create_summary=False
        )
        
        assert len(saved_files) == 1
        assert self.sample_result.original_file in saved_files
        assert '_summary' not in saved_files
    
    def test_extract_metadata_from_result(self):
        """Test extracting metadata from TranscriptionResult."""
        metadata = self.text_exporter._extract_metadata_from_result(self.sample_result)
        
        assert metadata['original_file'] == self.sample_result.original_file
        assert metadata['language'] == self.sample_result.language
        assert metadata['confidence_score'] == self.sample_result.confidence_score
        assert metadata['processing_time'] == self.sample_result.processing_time
        assert metadata['timestamp'] == "2023-12-01 14:30:00"
        assert metadata['error_message'] == self.sample_result.error_message
    
    def test_add_metadata_to_text(self):
        """Test adding metadata header to text."""
        text = "Original text content"
        metadata = {
            'original_file': 'test.m4a',
            'language': 'ko',
            'confidence_score': 0.95
        }
        
        result = self.text_exporter._add_metadata_to_text(text, metadata)
        
        assert "TRANSCRIPTION METADATA" in result
        assert "Original File: test.m4a" in result
        assert "Language: ko" in result
        assert "Confidence Score: 0.95" in result
        assert "TRANSCRIBED TEXT:" in result
        assert text in result
    
    def test_add_metadata_to_text_with_none_values(self):
        """Test adding metadata with None values."""
        text = "Original text content"
        metadata = {
            'original_file': 'test.m4a',
            'language': 'ko',
            'error_message': None
        }
        
        result = self.text_exporter._add_metadata_to_text(text, metadata)
        
        assert "Original File: test.m4a" in result
        assert "Language: ko" in result
        assert "Error Message: None" not in result  # None values should be skipped
    
    def test_generate_summary_content_empty(self):
        """Test generating summary content with empty results."""
        content = self.text_exporter._generate_summary_content([])
        
        assert "No transcription results to summarize" in content
    
    def test_generate_summary_content_with_results(self):
        """Test generating summary content with results."""
        results = [self.sample_result, self.failed_result]
        
        content = self.text_exporter._generate_summary_content(results)
        
        assert "TRANSCRIPTION BATCH SUMMARY REPORT" in content
        assert "Total files processed: 2" in content
        assert "Successful transcriptions: 1" in content
        assert "Failed transcriptions: 1" in content
        assert "audio.m4a" in content
        assert "failed.m4a" in content
    
    def test_custom_encoding(self):
        """Test using custom encoding."""
        exporter = TextExporter(encoding='utf-16')
        output_path = Path(self.temp_dir) / "encoded.txt"
        test_text = "한글 텍스트"
        
        result_path = exporter.save_as_txt(test_text, str(output_path))
        
        assert output_path.exists()
        
        # Read with the same encoding
        with open(output_path, 'r', encoding='utf-16') as f:
            content = f.read()
        
        assert content == test_text
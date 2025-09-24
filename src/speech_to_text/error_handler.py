"""
Comprehensive error handling system for the speech-to-text application.

This module provides centralized error handling, recovery strategies,
and user-friendly error messages with suggestions for common scenarios.
"""

import os
import shutil
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .exceptions import (
    SpeechToTextError,
    FileError,
    UnsupportedFormatError,
    ProcessingError,
    AudioProcessingError,
    AudioConversionError,
    ModelLoadError,
    TranscriptionError,
    SystemError,
    FileSystemError,
    DiskSpaceError
)


class ErrorHandler:
    """
    Centralized error handling system with recovery strategies and user guidance.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the error handler.
        
        Args:
            logger: Optional logger instance for error logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self._error_counts = {}
        self._recovery_attempts = {}
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Tuple[bool, str, List[str]]:
        """
        Handle an error with appropriate recovery strategy and user guidance.
        
        Args:
            error: The exception that occurred
            context: Additional context information about the error
            
        Returns:
            Tuple of (can_recover, user_message, suggestions)
        """
        context = context or {}
        error_type = type(error).__name__
        
        # Log the error
        self._log_error(error, context)
        
        # Track error occurrence
        self._track_error(error_type)
        
        # Determine recovery strategy based on error type
        # Handle built-in Python exceptions first
        if isinstance(error, FileNotFoundError):
            return self._handle_file_not_found_error(error, context)
        elif isinstance(error, PermissionError):
            return self._handle_permission_error(error, context)
        elif isinstance(error, MemoryError):
            return self._handle_memory_error(error, context)
        # Then handle our custom exceptions
        elif isinstance(error, FileError):
            return self._handle_file_error(error, context)
        elif isinstance(error, ProcessingError):
            return self._handle_processing_error(error, context)
        elif isinstance(error, SystemError):
            return self._handle_system_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_file_not_found_error(self, error: FileNotFoundError, context: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """Handle FileNotFoundError."""
        file_path = context.get('file_path', str(error))
        message = f"파일을 찾을 수 없습니다: {file_path}"
        suggestions = [
            "파일 경로가 올바른지 확인해주세요",
            "파일이 존재하는지 확인해주세요",
            "상대 경로 대신 절대 경로를 사용해보세요",
            "파일명에 특수문자가 있는지 확인해주세요"
        ]
        return False, message, suggestions
    
    def _handle_permission_error(self, error: PermissionError, context: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """Handle PermissionError."""
        file_path = context.get('file_path', str(error))
        message = f"파일에 접근할 권한이 없습니다: {file_path}"
        suggestions = [
            "파일 권한을 확인하고 읽기 권한을 부여해주세요",
            "관리자 권한으로 실행해보세요",
            "파일이 다른 프로그램에서 사용 중인지 확인해주세요"
        ]
        return True, message, suggestions
    
    def _handle_memory_error(self, error: MemoryError, context: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """Handle MemoryError."""
        message = "메모리가 부족합니다"
        suggestions = [
            "다른 프로그램을 종료하여 메모리를 확보해주세요",
            "더 작은 Whisper 모델을 사용해보세요 (tiny, base)",
            "파일을 더 작은 단위로 나누어 처리해보세요",
            "시스템을 재시작해보세요"
        ]
        return True, message, suggestions

    def _handle_file_error(self, error: FileError, context: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """Handle file-related errors."""
        if isinstance(error, UnsupportedFormatError):
            message = f"파일 형식이 지원되지 않습니다: {error.format_name}"
            suggestions = [
                f"지원되는 형식으로 변환해주세요: {', '.join(error.supported_formats)}",
                "FFmpeg를 사용하여 파일을 변환할 수 있습니다",
                "아이폰에서 녹음할 때 설정에서 파일 형식을 확인해주세요"
            ]
            return False, message, suggestions
        
        else:
            message = f"파일 처리 중 오류가 발생했습니다: {str(error)}"
            suggestions = [
                "파일이 손상되지 않았는지 확인해주세요",
                "다른 파일로 테스트해보세요",
                "파일 크기가 너무 크지 않은지 확인해주세요"
            ]
            return True, message, suggestions
    
    def _handle_processing_error(self, error: ProcessingError, context: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """Handle processing-related errors."""
        if isinstance(error, AudioConversionError):
            message = f"오디오 변환에 실패했습니다: {error.source_file}"
            suggestions = [
                "FFmpeg가 올바르게 설치되어 있는지 확인해주세요",
                "원본 파일이 손상되지 않았는지 확인해주세요",
                "디스크 공간이 충분한지 확인해주세요",
                "다른 오디오 플레이어에서 파일이 재생되는지 확인해주세요"
            ]
            return True, message, suggestions
        
        elif isinstance(error, ModelLoadError):
            message = f"Whisper 모델 로드에 실패했습니다: {error.model_name}"
            suggestions = [
                "인터넷 연결을 확인해주세요 (모델 다운로드 필요)",
                "디스크 공간이 충분한지 확인해주세요",
                "더 작은 모델 크기를 시도해보세요 (tiny, base)",
                "Whisper 패키지가 올바르게 설치되어 있는지 확인해주세요"
            ]
            return True, message, suggestions
        
        elif isinstance(error, TranscriptionError):
            message = f"음성 인식에 실패했습니다: {error.file_path}"
            suggestions = [
                "오디오 파일의 음질을 확인해주세요",
                "파일 길이가 너무 길지 않은지 확인해주세요",
                "다른 언어 설정을 시도해보세요",
                "더 큰 모델 크기를 사용해보세요 (small, medium)"
            ]
            return True, message, suggestions
        
        else:
            message = f"처리 중 오류가 발생했습니다: {str(error)}"
            suggestions = [
                "잠시 후 다시 시도해주세요",
                "시스템 리소스 사용량을 확인해주세요",
                "다른 파일로 테스트해보세요"
            ]
            return True, message, suggestions
    
    def _handle_system_error(self, error: SystemError, context: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """Handle system-related errors."""
        if isinstance(error, DiskSpaceError):
            message = "디스크 공간이 부족합니다"
            suggestions = [
                "불필요한 파일을 삭제하여 공간을 확보해주세요",
                "다른 드라이브에 출력 디렉토리를 설정해주세요",
                "임시 파일들을 정리해주세요",
                f"최소 {error.required_space // (1024*1024)}MB의 공간이 필요합니다" if error.required_space else "충분한 공간을 확보해주세요"
            ]
            return False, message, suggestions
        
        else:
            message = f"시스템 오류가 발생했습니다: {str(error)}"
            suggestions = [
                "시스템 리소스를 확인해주세요",
                "관리자 권한으로 실행해보세요",
                "시스템을 재시작해보세요"
            ]
            return True, message, suggestions
    
    def _handle_generic_error(self, error: Exception, context: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """Handle generic/unknown errors."""
        message = f"예상치 못한 오류가 발생했습니다: {str(error)}"
        suggestions = [
            "잠시 후 다시 시도해주세요",
            "입력 파일과 설정을 확인해주세요",
            "로그를 확인하여 자세한 오류 정보를 확인해주세요",
            "문제가 지속되면 개발자에게 문의해주세요"
        ]
        return True, message, suggestions
    
    def attempt_recovery(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """
        Attempt to recover from an error automatically.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            True if recovery was successful, False otherwise
        """
        context = context or {}
        error_key = f"{type(error).__name__}_{context.get('file_path', 'unknown')}"
        
        # Limit recovery attempts
        if self._recovery_attempts.get(error_key, 0) >= 3:
            self.logger.warning(f"Maximum recovery attempts reached for {error_key}")
            return False
        
        self._recovery_attempts[error_key] = self._recovery_attempts.get(error_key, 0) + 1
        
        try:
            if isinstance(error, AudioConversionError):
                return self._recover_audio_conversion(error, context)
            elif isinstance(error, ModelLoadError):
                return self._recover_model_load(error, context)
            elif isinstance(error, PermissionError):
                return self._recover_permission_error(error, context)
            elif isinstance(error, DiskSpaceError):
                return self._recover_disk_space(error, context)
            else:
                return False
        except Exception as recovery_error:
            self.logger.error(f"Recovery attempt failed: {recovery_error}")
            return False
    
    def _recover_audio_conversion(self, error: AudioConversionError, context: Dict[str, Any]) -> bool:
        """Attempt to recover from audio conversion errors."""
        # Try with different conversion parameters
        self.logger.info(f"Attempting audio conversion recovery for {error.source_file}")
        # This would be implemented with actual recovery logic
        return False
    
    def _recover_model_load(self, error: ModelLoadError, context: Dict[str, Any]) -> bool:
        """Attempt to recover from model loading errors."""
        # Try loading a smaller model
        self.logger.info(f"Attempting model load recovery, trying smaller model")
        # This would be implemented with actual recovery logic
        return False
    
    def _recover_permission_error(self, error: PermissionError, context: Dict[str, Any]) -> bool:
        """Attempt to recover from permission errors."""
        # Try copying file to temp location
        file_path = context.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                temp_path = f"/tmp/{os.path.basename(file_path)}"
                shutil.copy2(file_path, temp_path)
                context['temp_file'] = temp_path
                self.logger.info(f"Copied file to temporary location: {temp_path}")
                return True
            except Exception:
                return False
        return False
    
    def _recover_disk_space(self, error: DiskSpaceError, context: Dict[str, Any]) -> bool:
        """Attempt to recover from disk space errors."""
        # Clean up temporary files
        temp_dir = context.get('temp_dir', '/tmp')
        try:
            # This is a simplified cleanup - in practice, you'd be more selective
            temp_files = [f for f in os.listdir(temp_dir) if f.startswith('speech_to_text_')]
            for temp_file in temp_files[:5]:  # Clean up first 5 temp files
                os.remove(os.path.join(temp_dir, temp_file))
            self.logger.info(f"Cleaned up {len(temp_files)} temporary files")
            return len(temp_files) > 0
        except Exception:
            return False
    
    def get_error_statistics(self) -> Dict[str, int]:
        """Get statistics about encountered errors."""
        return self._error_counts.copy()
    
    def reset_statistics(self):
        """Reset error statistics and recovery attempts."""
        self._error_counts.clear()
        self._recovery_attempts.clear()
    
    def _log_error(self, error: Exception, context: Dict[str, Any]):
        """Log error with context information."""
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        self.logger.error(f"Error occurred: {error_info}")
    
    def _track_error(self, error_type: str):
        """Track error occurrence for statistics."""
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
    
    @staticmethod
    def get_common_solutions() -> Dict[str, List[str]]:
        """Get common solutions for frequent issues."""
        return {
            "파일을 찾을 수 없음": [
                "파일 경로를 다시 확인해주세요",
                "파일이 실제로 존재하는지 확인해주세요",
                "절대 경로를 사용해보세요"
            ],
            "지원하지 않는 파일 형식": [
                "지원되는 형식: .m4a, .wav, .mp3, .aac, .flac",
                "FFmpeg를 사용하여 파일을 변환해주세요",
                "아이폰 녹음 설정을 확인해주세요"
            ],
            "메모리 부족": [
                "다른 프로그램을 종료해주세요",
                "더 작은 Whisper 모델을 사용해주세요",
                "파일을 작은 단위로 나누어 처리해주세요"
            ],
            "디스크 공간 부족": [
                "불필요한 파일을 삭제해주세요",
                "다른 드라이브를 사용해주세요",
                "임시 파일을 정리해주세요"
            ]
        }
"""
Implements observability for prompt guarding activities.

This module provides a callback that logs prompt guarding activities
to various observability platforms.
"""

import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import litellm
from litellm._logging import verbose_logger
from litellm.integrations.custom_logger import CustomLogger
from litellm.types.utils import StandardLoggingPayload


class PromptGuardObservability(CustomLogger):
    """
    A callback for logging prompt guarding activities to observability platforms.
    
    This class can be configured to log to various platforms including:
    - Local logs
    - Cloud logging services
    - Monitoring dashboards
    """

    def __init__(
        self,
        log_to_file: bool = False,
        log_file_path: Optional[str] = None,
        log_to_cloud: bool = False,
        cloud_service: Optional[str] = None,
        cloud_api_key: Optional[str] = None,
        cloud_endpoint: Optional[str] = None,
        include_prompt_text: bool = False,
    ):
        """
        Initialize the PromptGuardObservability callback.
        
        Args:
            log_to_file: Whether to log to a local file
            log_file_path: Path to the log file
            log_to_cloud: Whether to log to a cloud service
            cloud_service: Name of the cloud service (e.g., "datadog", "cloudwatch")
            cloud_api_key: API key for the cloud service
            cloud_endpoint: Endpoint for the cloud service
            include_prompt_text: Whether to include the full prompt text in logs
        """
        self.log_to_file = log_to_file
        self.log_file_path = log_file_path or "prompt_guard_logs.jsonl"
        self.log_to_cloud = log_to_cloud
        self.cloud_service = cloud_service
        self.cloud_api_key = cloud_api_key
        self.cloud_endpoint = cloud_endpoint
        self.include_prompt_text = include_prompt_text
        
        verbose_logger.debug(f"PromptGuardObservability initialized")
        
        if self.log_to_file:
            # Create the log file if it doesn't exist
            if not os.path.exists(os.path.dirname(self.log_file_path)) and os.path.dirname(self.log_file_path):
                os.makedirs(os.path.dirname(self.log_file_path))
            
            # Check if we can write to the log file
            try:
                with open(self.log_file_path, "a") as f:
                    pass
            except Exception as e:
                verbose_logger.warning(f"Cannot write to log file {self.log_file_path}: {str(e)}")
                self.log_to_file = False

    def _extract_prompt_guard_data(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract prompt guard data from the request parameters.
        
        Args:
            kwargs: Request parameters
            
        Returns:
            Dictionary with prompt guard data
        """
        metadata = kwargs.get("metadata", {})
        prompt_guard_analysis = metadata.get("prompt_guard_analysis", {})
        
        # Extract basic request info
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        
        # Create a log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4()),
            "model": model,
            "prompt_guard_analysis": prompt_guard_analysis,
            "is_safe": prompt_guard_analysis.get("is_safe", True),
            "issues": prompt_guard_analysis.get("issues", []),
            "details": prompt_guard_analysis.get("details", {}),
        }
        
        # Include prompt text if configured
        if self.include_prompt_text and messages:
            log_entry["messages"] = messages
        
        return log_entry

    def _log_to_file(self, log_entry: Dict[str, Any]) -> None:
        """
        Log the entry to a file.
        
        Args:
            log_entry: Log entry to write
        """
        try:
            with open(self.log_file_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            verbose_logger.exception(f"Error writing to log file: {str(e)}")

    def _log_to_cloud(self, log_entry: Dict[str, Any]) -> None:
        """
        Log the entry to a cloud service.
        
        Args:
            log_entry: Log entry to send
        """
        if not self.cloud_service or not self.cloud_api_key:
            return
        
        try:
            # Implement cloud service specific logging here
            if self.cloud_service.lower() == "datadog":
                # Example Datadog implementation
                pass
            elif self.cloud_service.lower() == "cloudwatch":
                # Example CloudWatch implementation
                pass
            else:
                verbose_logger.warning(f"Unsupported cloud service: {self.cloud_service}")
        except Exception as e:
            verbose_logger.exception(f"Error logging to cloud service: {str(e)}")

    async def async_pre_call_hook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-call hook to log prompt guarding activities.
        
        Args:
            params: Parameters for the LLM call
            
        Returns:
            Unmodified parameters
        """
        # We don't modify the parameters, just log them
        return params

    async def async_post_call_hook(self, params: Dict[str, Any], response: Any) -> Any:
        """
        Post-call hook to log prompt guarding activities.
        
        Args:
            params: Parameters for the LLM call
            response: Response from the LLM
            
        Returns:
            Unmodified response
        """
        try:
            # Extract prompt guard data
            log_entry = self._extract_prompt_guard_data(params)
            
            # Add response info
            if response:
                log_entry["response_id"] = getattr(response, "id", str(uuid.uuid4()))
                log_entry["response_model"] = getattr(response, "model", "unknown")
            
            # Log to file if configured
            if self.log_to_file:
                self._log_to_file(log_entry)
            
            # Log to cloud if configured
            if self.log_to_cloud:
                self._log_to_cloud(log_entry)
            
            # Log to console for debugging
            if not log_entry.get("is_safe", True):
                verbose_logger.warning(f"Prompt guard issues detected: {log_entry['issues']}")
        except Exception as e:
            verbose_logger.exception(f"Error in prompt guard observability: {str(e)}")
        
        # Return unmodified response
        return response

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        """
        Log a successful LLM call.
        
        Args:
            kwargs: Request parameters
            response_obj: Response from the LLM
            start_time: Start time of the request
            end_time: End time of the request
        """
        try:
            # Extract prompt guard data
            log_entry = self._extract_prompt_guard_data(kwargs)
            
            # Add response info
            if response_obj:
                log_entry["response_id"] = getattr(response_obj, "id", str(uuid.uuid4()))
                log_entry["response_model"] = getattr(response_obj, "model", "unknown")
            
            # Add timing info
            log_entry["start_time"] = start_time.isoformat()
            log_entry["end_time"] = end_time.isoformat()
            log_entry["duration_ms"] = (end_time - start_time).total_seconds() * 1000
            
            # Log to file if configured
            if self.log_to_file:
                self._log_to_file(log_entry)
            
            # Log to cloud if configured
            if self.log_to_cloud:
                self._log_to_cloud(log_entry)
        except Exception as e:
            verbose_logger.exception(f"Error logging success event: {str(e)}")

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        """
        Log a failed LLM call.
        
        Args:
            kwargs: Request parameters
            response_obj: Error response
            start_time: Start time of the request
            end_time: End time of the request
        """
        try:
            # Extract prompt guard data
            log_entry = self._extract_prompt_guard_data(kwargs)
            
            # Add error info
            log_entry["error"] = True
            log_entry["error_type"] = type(response_obj).__name__
            log_entry["error_message"] = str(response_obj)
            
            # Add timing info
            log_entry["start_time"] = start_time.isoformat()
            log_entry["end_time"] = end_time.isoformat()
            log_entry["duration_ms"] = (end_time - start_time).total_seconds() * 1000
            
            # Log to file if configured
            if self.log_to_file:
                self._log_to_file(log_entry)
            
            # Log to cloud if configured
            if self.log_to_cloud:
                self._log_to_cloud(log_entry)
        except Exception as e:
            verbose_logger.exception(f"Error logging failure event: {str(e)}")
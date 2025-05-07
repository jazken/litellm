"""
Implements a prompt guarding mechanism to detect and prevent prompt injection attacks.

This module provides a callback that can be used to analyze prompts for potential
injection attacks and other security concerns before they are sent to the LLM.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union

import litellm
from litellm._logging import verbose_logger
from litellm.types.guardrails import GuardrailEventHooks


class PromptGuardCallback:
    """
    A callback for detecting and preventing prompt injection attacks.
    
    This class implements various detection mechanisms for common prompt injection
    patterns and can be configured to either block requests or just log warnings.
    """

    def __init__(
        self,
        guardrail_name: str,
        event_hook: str,
        default_on: bool = False,
        block_requests: bool = True,
        injection_patterns: Optional[List[str]] = None,
        custom_patterns: Optional[List[str]] = None,
        max_prompt_length: Optional[int] = None,
        sensitive_terms: Optional[List[str]] = None,
        log_only: bool = False,
    ):
        """
        Initialize the PromptGuard callback.
        
        Args:
            guardrail_name: Name of the guardrail
            event_hook: When to run the guardrail (pre_call, post_call, etc.)
            default_on: Whether the guardrail is enabled by default
            block_requests: Whether to block requests that trigger the guardrail
            injection_patterns: List of regex patterns to detect prompt injections
            custom_patterns: List of custom regex patterns to detect
            max_prompt_length: Maximum allowed prompt length
            sensitive_terms: List of sensitive terms to detect
            log_only: If True, only log issues without blocking
        """
        self.guardrail_name = guardrail_name
        self.event_hook = event_hook
        self.default_on = default_on
        self.block_requests = block_requests and not log_only
        self.log_only = log_only
        
        # Default injection patterns
        self.injection_patterns = injection_patterns or [
            r"ignore previous instructions",
            r"ignore all previous instructions",
            r"disregard previous instructions",
            r"forget your instructions",
            r"ignore your programming",
            r"you are now",
            r"now you are",
            r"you're now",
            r"now you're",
            r"you are no longer",
            r"you're no longer",
        ]
        
        # Add custom patterns if provided
        if custom_patterns:
            self.injection_patterns.extend(custom_patterns)
            
        self.max_prompt_length = max_prompt_length
        self.sensitive_terms = sensitive_terms or []
        
        verbose_logger.debug(f"PromptGuard initialized with {len(self.injection_patterns)} patterns")

    def _extract_prompt_text(self, messages: List[Dict[str, Any]]) -> str:
        """
        Extract text from messages for analysis.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Combined text from all messages
        """
        combined_text = ""
        for message in messages:
            if isinstance(message, dict) and "content" in message:
                content = message["content"]
                if isinstance(content, str):
                    combined_text += content + " "
                elif isinstance(content, list):
                    # Handle content that might be a list of content parts
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            combined_text += part["text"] + " "
        return combined_text.strip()

    def _check_injection_patterns(self, text: str) -> List[str]:
        """
        Check for injection patterns in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected patterns
        """
        detected_patterns = []
        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_patterns.append(pattern)
        return detected_patterns

    def _check_sensitive_terms(self, text: str) -> List[str]:
        """
        Check for sensitive terms in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected sensitive terms
        """
        detected_terms = []
        for term in self.sensitive_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE):
                detected_terms.append(term)
        return detected_terms

    def _analyze_prompt(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the prompt for potential issues.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary with analysis results
        """
        text = self._extract_prompt_text(messages)
        
        result = {
            "is_safe": True,
            "issues": [],
            "details": {}
        }
        
        # Check prompt length
        if self.max_prompt_length and len(text) > self.max_prompt_length:
            result["is_safe"] = False
            result["issues"].append("prompt_too_long")
            result["details"]["prompt_length"] = {
                "actual": len(text),
                "max_allowed": self.max_prompt_length
            }
        
        # Check injection patterns
        detected_patterns = self._check_injection_patterns(text)
        if detected_patterns:
            result["is_safe"] = False
            result["issues"].append("injection_detected")
            result["details"]["detected_patterns"] = detected_patterns
        
        # Check sensitive terms
        detected_terms = self._check_sensitive_terms(text)
        if detected_terms:
            result["is_safe"] = False
            result["issues"].append("sensitive_terms_detected")
            result["details"]["detected_terms"] = detected_terms
        
        return result

    async def async_pre_call_hook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-call hook to analyze the prompt before sending to the LLM.
        
        Args:
            params: Parameters for the LLM call
            
        Returns:
            Modified parameters or raises exception if blocked
        """
        try:
            messages = params.get("messages", [])
            if not messages:
                return params
            
            analysis_result = self._analyze_prompt(messages)
            
            # Add analysis result to metadata for observability
            if "metadata" not in params:
                params["metadata"] = {}
            
            params["metadata"]["prompt_guard_analysis"] = analysis_result
            
            # If issues were found and we're not in log-only mode, block the request
            if not analysis_result["is_safe"] and self.block_requests:
                verbose_logger.warning(
                    f"PromptGuard blocked request: {json.dumps(analysis_result)}"
                )
                raise litellm.exceptions.ContentPolicyViolationError(
                    message=f"Prompt guard detected issues: {', '.join(analysis_result['issues'])}",
                    llm_provider="prompt_guard",
                    model=params.get("model", "unknown"),
                )
            
            # Log issues even if we're not blocking
            if not analysis_result["is_safe"]:
                verbose_logger.warning(
                    f"PromptGuard detected issues: {json.dumps(analysis_result)}"
                )
            
            return params
        except litellm.exceptions.ContentPolicyViolationError:
            # Re-raise content policy violations
            raise
        except Exception as e:
            verbose_logger.exception(f"PromptGuard error: {str(e)}")
            # Don't block the request if there's an error in the guardrail
            return params

    async def async_post_call_hook(self, params: Dict[str, Any], response: Any) -> Any:
        """
        Post-call hook to analyze the response.
        
        Args:
            params: Parameters for the LLM call
            response: Response from the LLM
            
        Returns:
            Modified response
        """
        # Currently, we're not modifying the response
        # This could be extended to analyze and sanitize responses
        return response
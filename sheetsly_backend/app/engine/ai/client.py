"""Server-side client wrappers for AI Providers: Alibaba Cloud DashScope (Qwen/DeepSeek) & Google Gemini."""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx

from app.core.config import settings

logger = logging.getLogger("sheetsly.ai.client")


class AIProviderError(Exception):
    """Raised when the AI provider is unavailable, unconfigured, or returns invalid data."""
    def __init__(self, message: str, is_configured: bool = True, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.is_configured = is_configured
        self.status_code = status_code


class GeminiClient:
    """Robust client for Google Gemini API (v1beta REST generateContent)."""

    def __init__(self):
        self.timeout = 45.0
        self.max_retries = 2

    @property
    def is_configured(self) -> bool:
        """Returns True if GEMINI_API_KEY is present and not a dummy placeholder."""
        key = settings.GEMINI_API_KEY.strip()
        return bool(key) and key != "your_gemini_api_key_here"

    def get_sanitized_key_prefix(self) -> str:
        """Returns safe masked key prefix (e.g. 'AQ.Ab8****' or 'AIza****') for diagnostics without leaking secret."""
        key = settings.GEMINI_API_KEY.strip()
        if not key:
            return "(not configured)"
        if len(key) >= 6:
            return f"{key[:6]}****"
        return f"{key[:3]}****"

    def get_endpoint(self, model: str) -> str:
        """Resolves the Gemini generateContent REST URL according to official API format."""
        base_url = settings.GEMINI_BASE_URL.strip().rstrip("/")
        model_name = model.strip()
        return f"{base_url}/models/{model_name}:generateContent"

    def _get_headers(self) -> Dict[str, str]:
        if not self.is_configured:
            raise AIProviderError(
                "AI Query Planning is unavailable: GEMINI_API_KEY is not configured in backend .env.",
                is_configured=False,
            )
        return {
            "Content-Type": "application/json",
            "X-goog-api-key": settings.GEMINI_API_KEY.strip(),
        }

    def _clean_json_output(self, raw_text: str) -> str:
        """Extracts JSON payload from potential markdown code fences."""
        text = raw_text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    def _classify_http_error(self, status_code: int, response_text: str, model: str) -> str:
        """Produces precise, actionable diagnostic messages for Gemini HTTP responses."""
        if status_code == 400:
            return f"Invalid request to Gemini API (HTTP 400): {response_text[:200]}"
        if status_code in (401, 403):
            return (
                f"Authentication failed (HTTP {status_code}): Invalid or unauthorized GEMINI_API_KEY. "
                "Please verify your Gemini API key."
            )
        if status_code == 404:
            return (
                f"Model or endpoint not found (HTTP 404): The requested Gemini model '{model}' was not found. "
                "Please check model availability."
            )
        if status_code == 429:
            return "Rate limit or quota exceeded (HTTP 429). Please check your Google Gemini API quota / billing."
        if status_code >= 500:
            return f"Google Gemini AI service encountered an internal error (HTTP {status_code})."

        detail = response_text[:200]
        return f"Gemini API returned HTTP {status_code}: {detail}"

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calls Google Gemini generateContent API requesting structured JSON output.
        Translates response into structured dictionary while strictly enforcing server-side timeout/retries.
        """
        if not self.is_configured:
            raise AIProviderError(
                "AI Query Planning is unavailable: GEMINI_API_KEY is not configured in backend .env.",
                is_configured=False,
            )

        target_model = (model or settings.GEMINI_DEFAULT_MODEL or "gemini-3.5-flash").strip()
        endpoint = self.get_endpoint(target_model)

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint,
                        headers=self._get_headers(),
                        json=payload,
                    )

                if response.status_code in (429, 503) and attempt < self.max_retries:
                    import asyncio
                    logger.warning(f"Gemini API returned HTTP {response.status_code} on attempt {attempt + 1}, retrying after backoff...")
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue

                if response.status_code != 200:
                    err_msg = self._classify_http_error(response.status_code, response.text, target_model)
                    raise AIProviderError(err_msg, is_configured=True, status_code=response.status_code)

                res_data = response.json()
                candidates = res_data.get("candidates", [])
                if not candidates:
                    raise AIProviderError("Gemini API returned empty candidates list.")

                content_parts = candidates[0].get("content", {}).get("parts", [])
                if not content_parts or "text" not in content_parts[0]:
                    raise AIProviderError("Gemini API returned empty candidate parts text.")

                raw_text = content_parts[0].get("text", "")
                cleaned_content = self._clean_json_output(raw_text)
                try:
                    return json.loads(cleaned_content)
                except json.JSONDecodeError as jde:
                    logger.error(f"Failed to parse Gemini output as JSON: {cleaned_content}")
                    raise AIProviderError(f"Gemini API returned malformed JSON: {str(jde)}")

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error = net_err
                logger.warning(f"Gemini network error on attempt {attempt + 1}: {str(net_err)}")
                if attempt == self.max_retries:
                    raise AIProviderError("Gemini API request timed out or network connection failed.")
            except AIProviderError:
                raise
            except Exception as e:
                logger.error(f"Unexpected Gemini client error: {str(e)}")
                raise AIProviderError(f"Unexpected error communicating with Gemini API: {str(e)}")

        raise AIProviderError(f"Gemini API request failed: {str(last_error)}")

    async def test_connectivity(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a minimal, safe connectivity probe against the configured Gemini endpoint.
        Returns detailed diagnostics WITHOUT exposing any API keys or secrets.
        """
        target_model = (model or settings.GEMINI_DEFAULT_MODEL or "gemini-3.5-flash").strip()
        endpoint = self.get_endpoint(target_model)

        info: Dict[str, Any] = {
            "configured": self.is_configured,
            "provider": "Google Gemini",
            "key_prefix": self.get_sanitized_key_prefix(),
            "endpoint": endpoint,
            "model": target_model,
            "connectivity": "UNTESTED",
            "status_code": None,
            "latency_ms": None,
            "message": None,
        }

        if not self.is_configured:
            info["connectivity"] = "UNCONFIGURED"
            info["message"] = "GEMINI_API_KEY is not set in backend .env."
            return info

        import time
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    endpoint,
                    headers=self._get_headers(),
                    json={
                        "contents": [
                            {"parts": [{"text": "Return exactly the word OK."}]}
                        ],
                    },
                )
            latency = round((time.perf_counter() - t0) * 1000, 1)
            info["latency_ms"] = latency
            info["status_code"] = resp.status_code

            if resp.status_code == 200:
                info["connectivity"] = "HEALTHY"
                info["message"] = f"Successfully connected to Gemini ({target_model}) ({latency}ms)."
            else:
                info["connectivity"] = "ERROR"
                info["message"] = self._classify_http_error(resp.status_code, resp.text, target_model)

        except Exception as ex:
            latency = round((time.perf_counter() - t0) * 1000, 1)
            info["latency_ms"] = latency
            info["connectivity"] = "NETWORK_ERROR"
            info["message"] = f"Network/Connection error: {str(ex)}"

        return info


class QwenClient:
    """Robust OpenAI-compatible client for Qwen / DashScope LLM APIs."""

    def __init__(self):
        self.timeout = 45.0
        self.max_retries = 1

    @property
    def is_configured(self) -> bool:
        """Returns True if DASHSCOPE_API_KEY is present and not a dummy placeholder."""
        key = settings.DASHSCOPE_API_KEY.strip()
        return bool(key) and key != "your_dashscope_api_key_here"

    def get_sanitized_key_prefix(self) -> str:
        """Returns safe masked key prefix (e.g. 'sk-ws-****') for diagnostics without leaking secret."""
        key = settings.DASHSCOPE_API_KEY.strip()
        if not key:
            return "(not configured)"
        if key.startswith("sk-ws-"):
            return "sk-ws-****"
        if key.startswith("sk-"):
            return "sk-****"
        return f"{key[:4]}****"

    def get_normalized_endpoint(self) -> str:
        """
        Resolves the full chat completions URL, normalizing common path typos.
        For Alibaba MaaS endpoints, ensures '/compatible-mode/v1' is targeted.
        """
        raw_url = settings.QWEN_BASE_URL.strip().rstrip("/")
        # If user accidentally configured /api/v1 instead of /compatible-mode/v1 on maas.aliyuncs.com
        if "maas.aliyuncs.com" in raw_url and raw_url.endswith("/api/v1"):
            raw_url = raw_url[:-7] + "/compatible-mode/v1"
        elif not raw_url.endswith("/v1") and not raw_url.endswith("/compatible-mode/v1"):
            if "maas.aliyuncs.com" in raw_url:
                raw_url = f"{raw_url}/compatible-mode/v1"
            else:
                raw_url = f"{raw_url}/v1"

        return f"{raw_url}/chat/completions"

    def _get_headers(self) -> Dict[str, str]:
        if not self.is_configured:
            raise AIProviderError(
                "AI Query Planning is unavailable: DASHSCOPE_API_KEY is not configured in backend .env.",
                is_configured=False,
            )
        return {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY.strip()}",
            "Content-Type": "application/json",
        }

    def _clean_json_output(self, raw_text: str) -> str:
        """Extracts JSON payload from potential markdown code fences."""
        text = raw_text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    def _classify_http_error(self, status_code: int, response_text: str) -> str:
        """Produces precise, actionable diagnostic messages based on exact HTTP status codes."""
        parsed = urlparse(settings.QWEN_BASE_URL)
        host = parsed.netloc

        if status_code == 401:
            return "Authentication failed (HTTP 401): Invalid or expired DASHSCOPE_API_KEY. Please verify your API key in Model Studio."
        if status_code == 403:
            return (
                f"Workspace access denied (HTTP 403): The configured API key does not have permissions for host '{host}'. "
                f"Ensure your workspace ID in QWEN_BASE_URL matches the workspace associated with your API key."
            )
        if status_code == 404:
            return (
                f"Endpoint not found (HTTP 404): Host '{host}' rejected the URL path. "
                f"Ensure QWEN_BASE_URL uses '/compatible-mode/v1'."
            )
        if status_code == 429:
            return "Rate limit or account quota exceeded (HTTP 429). Please check your Alibaba Cloud Model Studio tier / balance."
        if status_code >= 500:
            return f"Alibaba Cloud AI service encountered an internal error (HTTP {status_code})."
        
        detail = response_text[:200]
        return f"AI provider returned HTTP {status_code}: {detail}"

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calls LLM chat completions API requesting structured JSON output.
        Automatically routes to Gemini if model is a Gemini model, preserving backward compatibility.
        """
        target_model = (model or settings.QWEN_MODEL or "qwen3.5-397b-a17b").strip()

        # Route to Gemini if requested model is Gemini
        if target_model.startswith("gemini-"):
            return await gemini_client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                model=target_model,
            )

        if not self.is_configured:
            raise AIProviderError(
                "AI Query Planning is unavailable: DASHSCOPE_API_KEY is not configured in backend .env.",
                is_configured=False,
            )

        endpoint = self.get_normalized_endpoint()
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        # Enable thinking mode if configured and model is Qwen
        if "qwen" in target_model.lower():
            payload["extra_body"] = {"enable_thinking": bool(settings.QWEN_ENABLE_THINKING)}

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint,
                        headers=self._get_headers(),
                        json=payload,
                    )

                if response.status_code != 200:
                    err_msg = self._classify_http_error(response.status_code, response.text)
                    raise AIProviderError(err_msg, is_configured=True, status_code=response.status_code)

                res_data = response.json()
                choices = res_data.get("choices", [])
                if not choices:
                    raise AIProviderError("AI provider returned empty choices in response.")

                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    raise AIProviderError("AI provider returned empty message content.")

                cleaned_content = self._clean_json_output(content)
                try:
                    return json.loads(cleaned_content)
                except json.JSONDecodeError as jde:
                    logger.error(f"Failed to parse LLM output as JSON: {cleaned_content}")
                    raise AIProviderError(f"AI provider returned malformed JSON: {str(jde)}")

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error = net_err
                logger.warning(f"Network error on attempt {attempt + 1}: {str(net_err)}")
                if attempt == self.max_retries:
                    raise AIProviderError("AI provider request timed out or network connection failed.")
            except AIProviderError:
                raise
            except Exception as e:
                logger.error(f"Unexpected AI client error: {str(e)}")
                raise AIProviderError(f"Unexpected error communicating with AI provider: {str(e)}")

        raise AIProviderError(f"AI provider request failed: {str(last_error)}")

    async def test_connectivity(self) -> Dict[str, Any]:
        """
        Executes a minimal, safe connectivity probe against the configured Qwen endpoint.
        Returns detailed diagnostics WITHOUT exposing any API keys or secrets.
        """
        parsed = urlparse(settings.QWEN_BASE_URL)
        workspace_id = None
        region = "global"
        if "maas.aliyuncs.com" in parsed.netloc:
            parts = parsed.netloc.split(".")
            if len(parts) >= 3:
                workspace_id = parts[0]
                region = parts[1]

        info: Dict[str, Any] = {
            "configured": self.is_configured,
            "provider": "DashScope / Qwen",
            "key_prefix": self.get_sanitized_key_prefix(),
            "base_url_host": parsed.netloc,
            "base_url_path": parsed.path,
            "resolved_endpoint": self.get_normalized_endpoint(),
            "model": settings.QWEN_MODEL,
            "workspace_id": workspace_id,
            "region": region,
            "connectivity": "UNTESTED",
            "status_code": None,
            "latency_ms": None,
            "message": None,
        }

        if not self.is_configured:
            info["connectivity"] = "UNCONFIGURED"
            info["message"] = "DASHSCOPE_API_KEY is not set in backend .env."
            return info

        import time
        t0 = time.perf_counter()
        try:
            endpoint = self.get_normalized_endpoint()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    endpoint,
                    headers=self._get_headers(),
                    json={
                        "model": settings.QWEN_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a connectivity test. Respond with exactly: OK"},
                            {"role": "user", "content": "Connectivity test."},
                        ],
                        "max_tokens": 10,
                    },
                )
            latency = round((time.perf_counter() - t0) * 1000, 1)
            info["latency_ms"] = latency
            info["status_code"] = resp.status_code

            if resp.status_code == 200:
                info["connectivity"] = "HEALTHY"
                info["message"] = f"Successfully connected to {settings.QWEN_MODEL} via {parsed.netloc} ({latency}ms)."
            else:
                info["connectivity"] = "ERROR"
                info["message"] = self._classify_http_error(resp.status_code, resp.text)

        except Exception as ex:
            latency = round((time.perf_counter() - t0) * 1000, 1)
            info["latency_ms"] = latency
            info["connectivity"] = "NETWORK_ERROR"
            info["message"] = f"Network/Connection error: {str(ex)}"

        return info


class AIProviderRouter:
    """Unified provider router dispatching requests to Qwen or Gemini clients."""

    def __init__(self, qwen: QwenClient, gemini: GeminiClient):
        self.qwen = qwen
        self.gemini = gemini

    def is_configured(self, model: Optional[str] = None) -> bool:
        """Checks if the provider for the specified model (or at least one provider) is configured."""
        if model and model.strip().lower().startswith("gemini-"):
            return self.gemini.is_configured
        return self.qwen.is_configured

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Routes generate_json to the appropriate provider client."""
        target_model = (model or "").strip().lower()
        if target_model.startswith("gemini-"):
            return await self.gemini.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                model=target_model,
            )
        return await self.qwen.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            model=model,
        )

    async def get_diagnostics(self) -> Dict[str, Any]:
        """Collects connectivity diagnostics across all configured AI providers."""
        qwen_diag = await self.qwen.test_connectivity()
        gemini_diag = await self.gemini.test_connectivity()
        return {
            "qwen": qwen_diag,
            "gemini": gemini_diag,
            "active_default": "qwen" if self.qwen.is_configured else ("gemini" if self.gemini.is_configured else "none"),
        }


# Global singleton clients
gemini_client = GeminiClient()
qwen_client = QwenClient()
ai_client = AIProviderRouter(qwen=qwen_client, gemini=gemini_client)

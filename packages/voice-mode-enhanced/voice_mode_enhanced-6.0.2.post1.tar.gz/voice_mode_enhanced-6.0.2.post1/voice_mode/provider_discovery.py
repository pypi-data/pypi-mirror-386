"""
Provider discovery and registry management for voice-mode.

This module handles automatic discovery of TTS/STT endpoints, including:
- Health checks
- Model discovery
- Voice discovery
- Dynamic registry management
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import httpx
from openai import AsyncOpenAI

from . import config
from .config import TTS_BASE_URLS, STT_BASE_URLS, OPENAI_API_KEY

logger = logging.getLogger("voice-mode")


def detect_provider_type(base_url: str) -> str:
    """Detect provider type from base URL."""
    if not base_url:
        return "unknown"
    if "openai.com" in base_url:
        return "openai"
    elif ":8880" in base_url:
        return "kokoro"
    elif ":2022" in base_url:
        return "whisper"
    elif "127.0.0.1" in base_url or "localhost" in base_url:
        # Try to infer from port if not already detected
        if base_url.endswith("/v1"):
            port_part = base_url[:-3].split(":")[-1]
            if port_part == "8880":
                return "kokoro"
            elif port_part == "2022":
                return "whisper"
        return "local"  # Generic local provider
    else:
        return "unknown"


def is_local_provider(base_url: str) -> bool:
    """Check if a provider URL is for a local service."""
    if not base_url:
        return False
    provider_type = detect_provider_type(base_url)
    return provider_type in ["kokoro", "whisper", "local"] or \
           "127.0.0.1" in base_url or \
           "localhost" in base_url


@dataclass
class EndpointInfo:
    """Information about a discovered endpoint."""
    base_url: str
    models: List[str]
    voices: List[str]  # Only for TTS
    provider_type: Optional[str] = None  # e.g., "openai", "kokoro", "whisper"
    last_check: Optional[str] = None  # ISO format timestamp of last attempt
    last_error: Optional[str] = None  # Last error if any


class ProviderRegistry:
    """Manages discovery and selection of voice service providers."""
    
    def __init__(self):
        self.registry: Dict[str, Dict[str, EndpointInfo]] = {
            "tts": {},
            "stt": {}
        }
        self._discovery_lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the registry with configured endpoints."""
        if self._initialized:
            return

        async with self._discovery_lock:
            if self._initialized:  # Double-check after acquiring lock
                return

            logger.info("Initializing provider registry...")

            # Initialize TTS endpoints
            for url in TTS_BASE_URLS:
                provider_type = detect_provider_type(url)
                self.registry["tts"][url] = EndpointInfo(
                    base_url=url,
                    models=["gpt4o-mini-tts", "tts-1", "tts-1-hd"] if provider_type == "openai" else ["tts-1"],
                    voices=["alloy", "echo", "fable", "nova", "onyx", "shimmer"] if provider_type == "openai" else ["af_alloy", "af_aoede", "af_bella", "af_heart", "af_jadzia", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky", "af_v0", "af_v0bella", "af_v0irulan", "af_v0nicole", "af_v0sarah", "af_v0sky", "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa", "am_v0adam", "am_v0gurney", "am_v0michael", "bf_alice", "bf_emma", "bf_lily", "bf_v0emma", "bf_v0isabella", "bm_daniel", "bm_fable", "bm_george", "bm_lewis", "bm_v0george", "bm_v0lewis", "ef_dora", "em_alex", "em_santa", "ff_siwis", "hf_alpha", "hf_beta", "hm_omega", "hm_psi", "if_sara", "im_nicola", "jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo", "pf_dora", "pm_alex", "pm_santa", "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi", "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"],
                    provider_type=provider_type
                )
            
            # Initialize STT endpoints
            for url in STT_BASE_URLS:
                provider_type = detect_provider_type(url)
                self.registry["stt"][url] = EndpointInfo(
                    base_url=url,
                    models=["whisper-1"],
                    voices=[],  # STT doesn't have voices
                    provider_type=provider_type
                )

            self._initialized = True
            logger.info(f"Provider registry initialized with {len(self.registry['tts'])} TTS and {len(self.registry['stt'])} STT endpoints")
    
    async def _discover_endpoints(self, service_type: str, base_urls: List[str]):
        """Discover all endpoints for a service type."""
        tasks = []
        for url in base_urls:
            if url not in self.registry[service_type]:
                tasks.append(self._discover_endpoint(service_type, url))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for url, result in zip(base_urls, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to discover {service_type} endpoint {url}: {result}")
                    self.registry[service_type][url] = EndpointInfo(
                        base_url=url,
                        models=[],
                        voices=[],
                        provider_type=detect_provider_type(url),
                        last_check=datetime.now(timezone.utc).isoformat(),
                        last_error=str(result)
                    )
    
    async def _discover_endpoint(self, service_type: str, base_url: str) -> None:
        """Discover capabilities of a single endpoint."""
        logger.debug(f"Discovering {service_type} endpoint: {base_url}")
        start_time = time.time()
        
        try:
            # Create OpenAI client for the endpoint
            client = AsyncOpenAI(
                api_key=OPENAI_API_KEY or "dummy-key-for-local",
                base_url=base_url,
                timeout=10.0
            )
            
            # Try to list models
            models = []
            try:
                model_response = await client.models.list()
                models = [model.id for model in model_response.data]
                logger.debug(f"Found models at {base_url}: {models}")
            except Exception as e:
                logger.debug(f"Could not list models at {base_url}: {e}")
                # Not all endpoints support /v1/models, that's OK
                # For STT endpoints, we'll do a more specific health check
                if service_type == "stt":
                    # Try a minimal transcription request to check if endpoint is alive
                    try:
                        # For local whisper, check if it responds to basic requests
                        if "127.0.0.1" in base_url or "127.0.0.1" in base_url:
                            # Local whisper doesn't need auth, just check connectivity
                            import httpx
                            async with httpx.AsyncClient(timeout=5.0) as http_client:
                                response = await http_client.get(base_url.rstrip('/v1'))
                                if response.status_code == 200:
                                    logger.debug(f"Local whisper endpoint {base_url} is responding")
                                    models = ["whisper-1"]  # Default model name
                                else:
                                    raise Exception(f"Whisper endpoint returned status {response.status_code}")
                        else:
                            # For OpenAI, models.list failure likely means auth issue
                            # We'll still mark it as healthy since the endpoint exists
                            models = ["whisper-1"]  # OpenAI's whisper model
                            logger.debug(f"Assuming OpenAI whisper endpoint {base_url} is available")
                    except Exception as health_error:
                        logger.debug(f"STT health check failed for {base_url}: {health_error}")
                        raise health_error
            
            # Ensure STT endpoints have at least the default whisper model
            if service_type == "stt" and not models:
                models = ["whisper-1"]
            
            # For TTS, discover voices
            voices = []
            if service_type == "tts":
                voices = await self._discover_voices(base_url, client)
                logger.debug(f"Found voices at {base_url}: {voices}")
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            # Store endpoint info
            self.registry[service_type][base_url] = EndpointInfo(
                base_url=base_url,
                models=models,
                voices=voices,
                provider_type=detect_provider_type(base_url),
                last_check=datetime.now(timezone.utc).isoformat(),
                last_error=None
            )
            
            logger.info(f"Successfully discovered {service_type} endpoint {base_url} with {len(models)} models and {len(voices)} voices")
            
        except Exception as e:
            logger.warning(f"Endpoint {base_url} discovery failed: {e}")
            self.registry[service_type][base_url] = EndpointInfo(
                base_url=base_url,
                models=[],
                voices=[],
                provider_type=detect_provider_type(base_url),
                last_check=datetime.now(timezone.utc).isoformat(),
                last_error=str(e)
            )
    
    async def _discover_voices(self, base_url: str, client: AsyncOpenAI) -> List[str]:
        """Discover available voices for a TTS endpoint."""
        # If it's OpenAI, use known voices (they don't expose a voices endpoint)
        if "openai.com" in base_url:
            return ["alloy", "echo", "fable", "nova", "onyx", "shimmer"]
        
        # Try standard OpenAI-compatible voices endpoint
        try:
            # Use httpx directly for the voices endpoint
            async with httpx.AsyncClient(timeout=5.0) as http_client:
                response = await http_client.get(f"{base_url}/audio/voices")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "voices" in data:
                        return [v["id"] if isinstance(v, dict) else v for v in data["voices"]]
                    elif isinstance(data, list):
                        return [v["id"] if isinstance(v, dict) else v for v in data]
        except Exception as e:
            logger.debug(f"Could not fetch voices from {base_url}/audio/voices: {e}")
        
        # If we can't determine voices but the endpoint is healthy, return empty list
        # The system will use configured defaults instead
        return []
    
    
    def get_endpoints(self, service_type: str) -> List[EndpointInfo]:
        """Get all endpoints for a service type in priority order."""
        endpoints = []

        # Return endpoints in the order they were configured
        base_urls = TTS_BASE_URLS if service_type == "tts" else STT_BASE_URLS

        for url in base_urls:
            info = self.registry[service_type].get(url)
            if info:
                endpoints.append(info)

        return endpoints

    def get_healthy_endpoints(self, service_type: str) -> List[EndpointInfo]:
        """Deprecated: Use get_endpoints instead. Returns all endpoints."""
        return self.get_endpoints(service_type)
    
    def find_endpoint_with_voice(self, voice: str) -> Optional[EndpointInfo]:
        """Find the first TTS endpoint that supports a specific voice."""
        for endpoint in self.get_endpoints("tts"):
            if voice in endpoint.voices:
                return endpoint
        return None

    def find_endpoint_with_model(self, service_type: str, model: str) -> Optional[EndpointInfo]:
        """Find the first endpoint that supports a specific model."""
        for endpoint in self.get_endpoints(service_type):
            if model in endpoint.models:
                return endpoint
        return None
    
    def get_registry_for_llm(self) -> Dict[str, Any]:
        """Get registry data formatted for LLM inspection."""
        return {
            "tts": {
                url: {
                    "models": info.models,
                    "voices": info.voices,
                    "provider_type": info.provider_type,
                    "last_check": info.last_check,
                    "last_error": info.last_error
                }
                for url, info in self.registry["tts"].items()
            },
            "stt": {
                url: {
                    "models": info.models,
                    "provider_type": info.provider_type,
                    "last_check": info.last_check,
                    "last_error": info.last_error
                }
                for url, info in self.registry["stt"].items()
            }
        }
    
    async def mark_failed(self, service_type: str, base_url: str, error: str):
        """Record that an endpoint failed.

        This updates the last_error and last_check fields for diagnostics,
        but doesn't prevent the endpoint from being tried again.
        """
        if base_url in self.registry[service_type]:
            # Update error and last check time for diagnostics
            self.registry[service_type][base_url].last_error = error
            self.registry[service_type][base_url].last_check = datetime.now(timezone.utc).isoformat()
            logger.info(f"{service_type} endpoint {base_url} failed: {error}")


# Global registry instance
provider_registry = ProviderRegistry()

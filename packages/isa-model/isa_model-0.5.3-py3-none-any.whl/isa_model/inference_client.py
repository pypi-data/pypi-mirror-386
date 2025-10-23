#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ISA Model - Inference Client (OpenAI-Compatible)
=================================================

Ultra-simple inference client that matches OpenAI SDK patterns.
No complicated wrappers, no manual session management, just works.

This is the inference client. Future additions:
- inference_client.py (this file) - for model inference/serving
- training_client.py - for model training and fine-tuning (coming soon)

Usage:
    from isa_model.inference_client import ISAModel

    client = ISAModel()  # or ISAModel(api_key="key", base_url="url")

    # Chat
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)

    # Streaming
    for chunk in client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}],
        stream=True
    ):
        print(chunk.choices[0].delta.content or "", end="")
"""

import os
import asyncio
import json
from typing import Optional, List, Dict, Any, Union, Iterator, AsyncIterator
from dataclasses import dataclass

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None


# ============================================================================
# HTTP Client for API Communication
# ============================================================================

class HTTPClient:
    """Standalone HTTP client for ISA Model API communication"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp is required for API mode. Install with: pip install aiohttp")

        if self._session is None or self._session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def post_json(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a JSON POST request"""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Convert LangChain messages to dicts before sending
        if "input_data" in data:
            data["input_data"] = self._serialize_input(data["input_data"])

        async with session.post(url, json=data) as response:
            if not response.ok:
                error_text = await response.text()
                raise Exception(f"API request failed ({response.status}): {error_text}")
            return await response.json()

    def _serialize_input(self, input_data: Any) -> Any:
        """Serialize input data to JSON-compatible format"""
        # Handle LangChain messages - convert to OpenAI format
        if isinstance(input_data, list) and input_data:
            first_item = input_data[0]
            # Check if it's a LangChain message (has 'type' and 'content' attributes)
            if hasattr(first_item, 'type') and hasattr(first_item, 'content'):
                # Convert LangChain messages to OpenAI format for API compatibility
                # LangChain types: "human", "ai", "system", "function", "tool"
                # OpenAI roles: "user", "assistant", "system", "function", "tool"
                serialized = []
                for msg in input_data:
                    # Map LangChain message types to OpenAI roles
                    msg_type = msg.type.lower()
                    if msg_type == "human":
                        role = "user"
                    elif msg_type == "ai":
                        role = "assistant"
                    elif msg_type in ["system", "function", "tool"]:
                        role = msg_type
                    else:
                        # Fallback for unknown types
                        role = "user"

                    serialized.append({
                        "role": role,
                        "content": msg.content
                    })
                return serialized
        return input_data

    async def post_stream(self, endpoint: str, data: Dict[str, Any]) -> AsyncIterator[str]:
        """Make a streaming POST request (Server-Sent Events)"""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Convert LangChain messages to dicts before sending
        if "input_data" in data:
            data["input_data"] = self._serialize_input(data["input_data"])

        async with session.post(url, json=data) as response:
            if not response.ok:
                error_text = await response.text()
                raise Exception(f"Streaming request failed ({response.status}): {error_text}")

            # Read SSE stream line by line
            async for line in response.content:
                line_str = line.decode('utf-8').strip()

                # Skip empty lines
                if not line_str:
                    continue

                # Parse SSE format: "data: {...}"
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # Remove "data: " prefix

                    # Check for [DONE] marker
                    if data_str == "[DONE]":
                        break

                    try:
                        # Parse JSON chunk
                        chunk_data = json.loads(data_str)

                        # Extract content from OpenAI-compatible format
                        if 'choices' in chunk_data and chunk_data['choices']:
                            choice = chunk_data['choices'][0]

                            # Yield delta content
                            if 'delta' in choice and choice['delta']:
                                content = choice['delta'].get('content')
                                if content is not None:  # Can be empty string
                                    yield content

                            # Check for finish
                            if choice.get('finish_reason') in ['stop', 'length', 'tool_calls']:
                                break

                    except json.JSONDecodeError:
                        continue  # Skip invalid JSON

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Message:
    """Simple message object"""
    role: str
    content: str

    def __repr__(self):
        return f"Message(role='{self.role}', content='{self.content[:50]}...')"


@dataclass
class Choice:
    """Response choice"""
    message: Optional[Message] = None
    delta: Optional[Message] = None
    finish_reason: Optional[str] = None
    index: int = 0


@dataclass
class Usage:
    """Token usage information"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatCompletion:
    """Chat completion response"""
    id: str
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None

    @property
    def content(self) -> str:
        """Quick access to response content"""
        if self.choices and self.choices[0].message:
            return self.choices[0].message.content
        return ""


@dataclass
class Embedding:
    """Embedding object"""
    embedding: List[float]
    index: int = 0


@dataclass
class EmbeddingResponse:
    """Embedding response"""
    data: List[Embedding]
    model: str
    usage: Optional[Usage] = None


class ChatCompletions:
    """Chat completions endpoint"""

    def __init__(self, client):
        self._client = client

    def create(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> Union[ChatCompletion, Iterator[ChatCompletion]]:
        """
        Create chat completion (sync wrapper for async)

        Args:
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            messages: List of message dicts [{"role": "user", "content": "..."}]
            stream: Enable streaming
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            tools: Tool definitions for function calling
            **kwargs: Additional parameters

        Returns:
            ChatCompletion or Iterator[ChatCompletion] if streaming
        """
        if stream:
            # Return sync generator for streaming
            return self._sync_stream_wrapper(
                model, messages, temperature, max_tokens, tools, provider, **kwargs
            )
        else:
            # Run async call using asyncio.run with proper session management
            async def run():
                # Create a new async client for this request to avoid session reuse issues
                async with AsyncISAModel(
                    api_key=self._client._async_client._http_client.api_key,
                    base_url=self._client._base_url
                ) as client:
                    return await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=False,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        tools=tools,
                        provider=provider,
                        **kwargs
                    )

            return asyncio.run(run())

    def _run_async_in_new_loop(self, model, messages, temperature, max_tokens, tools, provider, **kwargs):
        """Run async operation in a new event loop with proper cleanup"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._create_async(model, messages, temperature, max_tokens, tools, provider, **kwargs)
            )
        finally:
            # Don't close the loop immediately to allow pending tasks to complete
            # This prevents "Session is closed" errors
            try:
                # Give a small grace period for cleanup
                loop.run_until_complete(asyncio.sleep(0.01))
            except:
                pass
            finally:
                loop.close()

    def _sync_stream_wrapper(self, model, messages, temperature, max_tokens, tools, provider, **kwargs):
        """Synchronous generator wrapper for async streaming"""
        import threading
        import queue

        result_queue = queue.Queue()
        exception_holder = []

        def run_async_gen():
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def stream_chunks():
                    try:
                        # Use the async client's streaming
                        gen = self._client._async_client.chat.completions.create(
                            model=model,
                            messages=messages,
                            stream=True,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            tools=tools,
                            provider=provider,
                            **kwargs
                        )
                        async for chunk in gen:
                            result_queue.put(chunk)
                    except Exception as e:
                        exception_holder.append(e)
                    finally:
                        result_queue.put(None)  # Sentinel value

                loop.run_until_complete(stream_chunks())

                # Properly close all pending tasks
                try:
                    # Cancel all remaining tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()

                    # Wait for tasks to finish cancelling
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass  # Ignore errors during cleanup

            except Exception as e:
                exception_holder.append(e)
                result_queue.put(None)
            finally:
                # Close the loop safely
                if loop is not None:
                    try:
                        loop.run_until_complete(asyncio.sleep(0.1))  # Allow cleanup
                    except:
                        pass
                    try:
                        loop.close()
                    except:
                        pass

        # Start streaming in background thread
        thread = threading.Thread(target=run_async_gen, daemon=True)
        thread.start()

        # Yield chunks as they arrive
        while True:
            chunk = result_queue.get()
            if chunk is None:
                break
            if exception_holder:
                raise exception_holder[0]
            yield chunk

    async def _create_async(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: Optional[float],
        max_tokens: Optional[int],
        tools: Optional[List[Dict]],
        provider: Optional[str],
        **kwargs
    ) -> ChatCompletion:
        """Async implementation"""
        # Convert messages to format expected by ISAModelClient
        input_data = messages

        # Build kwargs
        invoke_kwargs = {}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature
        if max_tokens is not None:
            invoke_kwargs["max_tokens"] = max_tokens
        if tools:
            invoke_kwargs["tools"] = tools
        if provider is not None:
            invoke_kwargs["provider"] = provider
        invoke_kwargs.update(kwargs)

        # Call underlying client
        response = await self._client._underlying_client.invoke(
            input_data=input_data,
            task="chat",
            service_type="text",
            model=model,
            stream=False,
            **invoke_kwargs
        )

        if not response.get("success"):
            raise Exception(f"API error: {response.get('error', 'Unknown error')}")

        # Convert to ChatCompletion format
        result = response.get("result", "")
        metadata = response.get("metadata", {})
        billing = metadata.get("billing", {})

        # Extract content from result (format varies based on input type)
        # - OpenAI chat input → OpenAI completion dict with choices
        # - String input → plain string
        # - LangChain input → AIMessage dict with content field
        if isinstance(result, dict) and "choices" in result:
            # OpenAI completion format - extract from choices
            content = result["choices"][0]["message"]["content"]
        elif isinstance(result, dict) and "content" in result:
            # LangChain AIMessage format (serialized) - extract content
            content = result["content"]
        elif isinstance(result, str):
            # Plain string result
            content = result
        else:
            # Fallback - convert to string
            content = str(result)

        # Extract usage information with proper defaults
        input_tokens = billing.get("input_tokens") or 0
        output_tokens = billing.get("output_tokens") or 0
        total_tokens = billing.get("total_tokens") or (input_tokens + output_tokens)

        return ChatCompletion(
            id=metadata.get("request_id", "unknown"),
            model=metadata.get("model_used", model),
            choices=[
                Choice(
                    message=Message(role="assistant", content=content),
                    finish_reason="stop",
                    index=0
                )
            ],
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=total_tokens
            ) if (input_tokens or output_tokens or total_tokens) else None
        )

    async def _create_stream_async(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: Optional[float],
        max_tokens: Optional[int],
        tools: Optional[List[Dict]],
        provider: Optional[str],
        **kwargs
    ):
        """Async streaming implementation"""
        input_data = messages

        # Build kwargs
        invoke_kwargs = {}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature
        if max_tokens is not None:
            invoke_kwargs["max_tokens"] = max_tokens
        if tools:
            invoke_kwargs["tools"] = tools
        if provider is not None:
            invoke_kwargs["provider"] = provider
        invoke_kwargs.update(kwargs)

        # Call underlying client with streaming
        response = await self._client._underlying_client.invoke(
            input_data=input_data,
            task="chat",
            service_type="text",
            model=model,
            stream=True,
            **invoke_kwargs
        )

        if not response.get("success"):
            raise Exception(f"API error: {response.get('error', 'Unknown error')}")

        # Stream tokens
        if "stream" in response:
            async for chunk in response["stream"]:
                if isinstance(chunk, str):
                    # Token chunk
                    yield ChatCompletion(
                        id="stream",
                        model=model,
                        choices=[
                            Choice(
                                delta=Message(role="assistant", content=chunk),
                                index=0
                            )
                        ]
                    )
                elif isinstance(chunk, dict):
                    # Final metadata chunk
                    break


class Chat:
    """Chat endpoint namespace"""

    def __init__(self, client):
        self.completions = ChatCompletions(client)


class Speech:
    """Audio speech endpoint"""

    def __init__(self, client):
        self._client = client

    def create(
        self,
        model: str,
        voice: str,
        input: str,
        **kwargs
    ) -> bytes:
        """
        Generate speech from text

        Args:
            model: TTS model (e.g., "tts-1")
            voice: Voice name (e.g., "alloy", "echo")
            input: Text to convert to speech

        Returns:
            Audio bytes
        """
        try:
            loop = asyncio.get_running_loop()
            # Already in async context, run in thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    self._run_in_new_loop,
                    model, voice, input, **kwargs
                )
                return future.result()
        except RuntimeError:
            return self._run_in_new_loop(model, voice, input, **kwargs)

    def _run_in_new_loop(self, model, voice, input, **kwargs):
        """Run async operation in a new event loop with proper cleanup"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._create_async(model, voice, input, **kwargs))
        finally:
            try:
                loop.run_until_complete(asyncio.sleep(0.01))
            except:
                pass
            finally:
                loop.close()

    async def _create_async(self, model, voice, input, **kwargs):
        """Async implementation"""
        response = await self._client._underlying_client.invoke(
            input_data=input,
            task="tts",
            service_type="audio",
            model=model,
            voice=voice,
            **kwargs
        )

        if not response.get("success"):
            raise Exception(f"API error: {response.get('error', 'Unknown error')}")

        result = response.get("result")

        # Handle different audio result formats
        if isinstance(result, dict):
            # Check for audio_data_base64 field (from TTS services)
            if 'audio_data_base64' in result:
                import base64
                return base64.b64decode(result['audio_data_base64'])
            # Check for audio_data field
            elif 'audio_data' in result:
                audio_data = result['audio_data']
                if isinstance(audio_data, str):
                    import base64
                    return base64.b64decode(audio_data)
                return audio_data
        elif isinstance(result, str):
            # Plain base64 string
            import base64
            try:
                return base64.b64decode(result)
            except Exception:
                # Might already be bytes encoded as string
                return result.encode('utf-8')
        elif isinstance(result, bytes):
            return result

        return result


class Transcriptions:
    """Audio transcription endpoint"""

    def __init__(self, client):
        self._client = client

    def create(
        self,
        model: str,
        file: Union[str, bytes],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text

        Args:
            model: STT model (e.g., "whisper-1")
            file: Audio file path or bytes

        Returns:
            Dict with "text" field
        """
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    self._run_in_new_loop,
                    model, file, **kwargs
                )
                return future.result()
        except RuntimeError:
            return self._run_in_new_loop(model, file, **kwargs)

    def _run_in_new_loop(self, model, file, **kwargs):
        """Run async operation in a new event loop with proper cleanup"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._create_async(model, file, **kwargs))
        finally:
            try:
                loop.run_until_complete(asyncio.sleep(0.01))
            except:
                pass
            finally:
                loop.close()

    async def _create_async(self, model, file, **kwargs):
        """Async implementation"""
        response = await self._client._underlying_client.invoke(
            input_data=file,
            task="transcribe",
            service_type="audio",
            model=model,
            **kwargs
        )

        if not response.get("success"):
            raise Exception(f"API error: {response.get('error', 'Unknown error')}")

        result = response.get("result", {})

        # Normalize response format
        if isinstance(result, dict):
            return {"text": result.get("text", "")}
        else:
            return {"text": str(result)}


class Audio:
    """Audio endpoint namespace"""

    def __init__(self, client):
        self.speech = Speech(client)
        self.transcriptions = Transcriptions(client)


class Embeddings:
    """Embeddings endpoint"""

    def __init__(self, client):
        self._client = client

    def create(
        self,
        model: str,
        input: Union[str, List[str]],
        **kwargs
    ) -> EmbeddingResponse:
        """
        Create embeddings

        Args:
            model: Embedding model (e.g., "text-embedding-3-small")
            input: Text or list of texts

        Returns:
            EmbeddingResponse with embeddings
        """
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    self._run_in_new_loop,
                    model, input, **kwargs
                )
                return future.result()
        except RuntimeError:
            return self._run_in_new_loop(model, input, **kwargs)

    def _run_in_new_loop(self, model, input, **kwargs):
        """Run async operation in a new event loop with proper cleanup"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._create_async(model, input, **kwargs))
        finally:
            try:
                loop.run_until_complete(asyncio.sleep(0.01))
            except:
                pass
            finally:
                loop.close()

    async def _create_async(self, model, input, **kwargs):
        """Async implementation"""
        response = await self._client._underlying_client.invoke(
            input_data=input,
            task="embed",
            service_type="embedding",
            model=model,
            **kwargs
        )

        if not response.get("success"):
            raise Exception(f"API error: {response.get('error', 'Unknown error')}")

        result = response.get("result")
        metadata = response.get("metadata", {})
        billing = metadata.get("billing", {})

        # Handle single or batch embeddings
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], list):
                # Batch embeddings
                embeddings = [Embedding(embedding=emb, index=i) for i, emb in enumerate(result)]
            else:
                # Single embedding
                embeddings = [Embedding(embedding=result, index=0)]
        else:
            embeddings = []

        return EmbeddingResponse(
            data=embeddings,
            model=metadata.get("model_used", model),
            usage=Usage(
                prompt_tokens=billing.get("input_tokens", 0),
                completion_tokens=0,
                total_tokens=billing.get("total_tokens", 0)
            ) if billing.get("input_tokens") else None
        )


class Images:
    """Image generation endpoint"""

    def __init__(self, client):
        self._client = client

    def generate(
        self,
        model: str,
        prompt: str,
        n: int = 1,
        size: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate images from prompt

        Args:
            model: Image model (e.g., "dall-e-3")
            prompt: Text prompt
            n: Number of images
            size: Image size

        Returns:
            Dict with "data" field containing image URLs
        """
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    self._run_in_new_loop,
                    model, prompt, n, size, **kwargs
                )
                return future.result()
        except RuntimeError:
            return self._run_in_new_loop(model, prompt, n, size, **kwargs)

    def _run_in_new_loop(self, model, prompt, n, size, **kwargs):
        """Run async operation in a new event loop with proper cleanup"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._generate_async(model, prompt, n, size, **kwargs))
        finally:
            try:
                loop.run_until_complete(asyncio.sleep(0.01))
            except:
                pass
            finally:
                loop.close()

    async def _generate_async(self, model, prompt, n, size, **kwargs):
        """Async implementation"""
        invoke_kwargs = kwargs.copy()
        if size:
            invoke_kwargs["size"] = size
        if n:
            invoke_kwargs["n"] = n

        response = await self._client._underlying_client.invoke(
            input_data=prompt,
            task="generate",
            service_type="image",
            model=model,
            **invoke_kwargs
        )

        if not response.get("success"):
            raise Exception(f"API error: {response.get('error', 'Unknown error')}")

        result = response.get("result", {})

        # Normalize response format
        if isinstance(result, dict) and "images" in result:
            images = result["images"]
        elif isinstance(result, list):
            images = result
        else:
            images = [result]

        return {
            "data": [{"url": img} for img in images]
        }


# ============================================================================
# ASYNC CLIENT (Pure async - no sync wrappers, like AsyncOpenAI)
# ============================================================================

class AsyncChatCompletions:
    """Async chat completions endpoint"""

    def __init__(self, client):
        self._client = client

    async def create(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> Union[ChatCompletion, AsyncIterator[ChatCompletion]]:
        """Create chat completion (async)"""
        # Build kwargs
        invoke_kwargs = {}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature
        if max_tokens is not None:
            invoke_kwargs["max_tokens"] = max_tokens
        if tools:
            invoke_kwargs["tools"] = tools
        if provider is not None:
            invoke_kwargs["provider"] = provider
        invoke_kwargs.update(kwargs)

        if stream:
            # Return the async generator directly - DO NOT await it
            # This allows the caller to use: async for chunk in client.chat.completions.create(...)
            return self._create_stream(model, messages, **invoke_kwargs)
        else:
            # Build request payload
            request_data = {
                "input_data": messages,
                "task": "chat",
                "service_type": "text",
                "model": model,
                "stream": False,
                **invoke_kwargs
            }

            # Make API request
            response = await self._client._http_client.post_json("api/v1/invoke", request_data)

            if not response.get("success"):
                raise Exception(f"API error: {response.get('error', 'Unknown error')}")

            result = response.get("result", "")
            metadata = response.get("metadata", {})

            # Extract token usage from top-level usage field (new format)
            usage_data = response.get("usage") or {}
            input_tokens = usage_data.get("prompt_tokens", 0)
            output_tokens = usage_data.get("completion_tokens", 0)
            total_tokens = usage_data.get("total_tokens", 0)

            # Fallback to old billing format if usage not present
            if not usage_data:
                billing = metadata.get("billing") or {}
                input_tokens = billing.get("input_tokens", 0)
                output_tokens = billing.get("output_tokens", 0)
                total_tokens = billing.get("total_tokens", 0)

            # Extract content from result (format varies based on input type)
            # - OpenAI chat input → OpenAI completion dict with choices
            # - String input → plain string
            # - LangChain input → AIMessage dict with content field
            if isinstance(result, dict) and "choices" in result:
                # OpenAI completion format - extract from choices
                content = result["choices"][0]["message"]["content"]
            elif isinstance(result, dict) and "content" in result:
                # LangChain AIMessage format (serialized) - extract content
                content = result["content"]
            elif isinstance(result, str):
                # Plain string result
                content = result
            else:
                # Fallback - convert to string
                content = str(result)

            return ChatCompletion(
                id=metadata.get("request_id", "unknown"),
                model=metadata.get("model_used", model),
                choices=[
                    Choice(
                        message=Message(role="assistant", content=content),
                        finish_reason="stop",
                        index=0
                    )
                ],
                usage=Usage(
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    total_tokens=total_tokens
                ) if (input_tokens or output_tokens or total_tokens) else None
            )

    async def _create_stream(self, model, messages, **kwargs):
        """Async streaming implementation - this is an async generator"""
        # Build request payload
        request_data = {
            "input_data": messages,
            "task": "chat",
            "service_type": "text",
            "model": model,
            "stream": True,
            **kwargs
        }

        # Stream tokens from API
        async for token in self._client._http_client.post_stream("api/v1/invoke", request_data):
            yield ChatCompletion(
                id="stream",
                model=model,
                choices=[
                    Choice(
                        delta=Message(role="assistant", content=token),
                        index=0
                    )
                ]
            )


class AsyncAudioTranscriptions:
    """Async audio transcriptions endpoint (OpenAI-compatible)"""

    def __init__(self, client):
        self._client = client

    async def create(
        self,
        file: Union[str, Any],
        model: str = "gpt-4o-mini-transcribe",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "json",
        enable_diarization: bool = False,
        known_speaker_names: Optional[List[str]] = None,
        known_speaker_references: Optional[List[str]] = None,
        chunking_strategy: Optional[str] = None,
        stream: bool = False,
        provider: str = "openai",
        **kwargs
    ):
        """
        Transcribe audio file using OpenAI-compatible API

        Args:
            file: Audio file path or file object
            model: Model name (gpt-4o-mini-transcribe, gpt-4o-transcribe, gpt-4o-transcribe-diarize, whisper-1)
            language: Optional language code
            prompt: Optional prompt to guide transcription
            response_format: Response format (json, text, srt, verbose_json, vtt, diarized_json)
            enable_diarization: Enable speaker diarization (for gpt-4o-transcribe-diarize)
            known_speaker_names: Optional list of speaker names for diarization
            known_speaker_references: Optional list of speaker reference audio (data URLs)
            chunking_strategy: Chunking strategy for diarization ("auto" recommended)
            stream: Enable streaming (for gpt-4o models)
            provider: Provider name (default: "openai")
            **kwargs: Additional parameters

        Returns:
            Transcription object with .text attribute and optional .segments
        """
        # Build parameters
        # Note: For STT, response_format is NOT sent as a parameter to the API
        # It's already baked into the model selection (e.g., diarized_json for diarize model)
        params = {}
        if language:
            params["language"] = language
        if prompt:
            params["prompt"] = prompt
        if enable_diarization:
            params["enable_diarization"] = enable_diarization
        if known_speaker_names:
            params["known_speaker_names"] = known_speaker_names
        if known_speaker_references:
            params["known_speaker_references"] = known_speaker_references
        if chunking_strategy:
            params["chunking_strategy"] = chunking_strategy
        if stream:
            params["stream"] = stream
        params.update(kwargs)

        # Handle file input - convert local file paths to base64 for API transmission
        # The STT service can handle: URLs, base64 strings, file paths (server-side), and file objects
        import os
        import base64

        if isinstance(file, str) and os.path.isfile(file):
            # Read local file and convert to base64 for transmission to API
            # (API server can't access client's local filesystem)
            with open(file, "rb") as f:
                audio_data = f.read()
            # Send as base64 string - the STT service will decode it
            audio_input = base64.b64encode(audio_data).decode("utf-8")
        else:
            # Pass through as-is (could be URL, base64 string already, or file object)
            audio_input = file

        # Call the API
        response = await self._client._underlying_client.invoke(
            input_data=audio_input,
            task="stt",
            service_type="audio",
            model=model,
            provider=provider,
            **params
        )

        if not response.get("success"):
            raise Exception(f"Transcription failed: {response.get('error', 'Unknown error')}")

        result = response["result"]

        # Create OpenAI-compatible response object
        class TranscriptionResponse:
            def __init__(self, data):
                self.text = data.get("text", "")
                self.language = data.get("language")
                self.duration = data.get("duration")
                self.segments = data.get("diarized_segments", data.get("segments", []))
                self.usage = data.get("usage")
                # Store raw result for debugging
                self._raw = data

            def __repr__(self):
                return f"Transcription(text='{self.text[:50]}...', language='{self.language}')"

        return TranscriptionResponse(result)


class AsyncAudio:
    """Async audio endpoint namespace (OpenAI-compatible)"""

    def __init__(self, client):
        self.transcriptions = AsyncAudioTranscriptions(client)
        # TODO: Add translations endpoint


class AsyncEmbeddings:
    """Async embeddings endpoint (OpenAI-compatible)"""

    def __init__(self, client):
        self._client = client

    async def create(
        self,
        input: Union[str, List[str]],
        model: str = "text-embedding-3-small",
        provider: str = "openai",
        **kwargs
    ):
        """
        Create embeddings using OpenAI-compatible API

        Args:
            input: Text or list of texts to embed
            model: Model name (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
            provider: Provider name (default: "openai")
            **kwargs: Additional parameters

        Returns:
            Embeddings object with .data list and .usage
        """
        # Call the API
        response = await self._client._underlying_client.invoke(
            input_data=input,
            task="embed",
            service_type="embedding",
            model=model,
            provider=provider,
            **kwargs
        )

        if not response.get("success"):
            raise Exception(f"Embedding failed: {response.get('error', 'Unknown error')}")

        result = response["result"]

        # Create OpenAI-compatible response object
        class EmbeddingData:
            def __init__(self, embedding, index):
                self.embedding = embedding
                self.index = index
                self.object = "embedding"

        class EmbeddingResponse:
            def __init__(self, embeddings_list, model_name):
                # Handle both single embedding and list of embeddings
                if isinstance(embeddings_list, list) and len(embeddings_list) > 0:
                    if isinstance(embeddings_list[0], list):
                        # List of embeddings
                        self.data = [EmbeddingData(emb, i) for i, emb in enumerate(embeddings_list)]
                    else:
                        # Single embedding (list of floats)
                        self.data = [EmbeddingData(embeddings_list, 0)]
                else:
                    self.data = []

                self.model = model_name
                self.object = "list"
                self.usage = {
                    "prompt_tokens": 0,  # TODO: Get from response if available
                    "total_tokens": 0
                }

            def __repr__(self):
                return f"EmbeddingResponse(model='{self.model}', embeddings={len(self.data)})"

        return EmbeddingResponse(result, model)


class AsyncImagesGenerations:
    """Async image generations endpoint (OpenAI-compatible)"""

    def __init__(self, client):
        self._client = client

    async def generate(
        self,
        prompt: str,
        model: str = "dall-e-3",
        n: int = 1,
        size: str = "1024x1024",
        quality: str = "standard",
        provider: str = "openai",
        **kwargs
    ):
        """
        Generate images using OpenAI-compatible API

        Args:
            prompt: Text description of desired image
            model: Model name (dall-e-3, dall-e-2)
            n: Number of images to generate
            size: Image size (1024x1024, 1024x1792, 1792x1024 for dall-e-3)
            quality: Image quality (standard, hd)
            provider: Provider name (default: "openai")
            **kwargs: Additional parameters

        Returns:
            Images object with .data list containing image URLs
        """
        # Call the API
        response = await self._client._underlying_client.invoke(
            input_data=prompt,
            task="generate",
            service_type="image",
            model=model,
            provider=provider,
            size=size,
            quality=quality,
            n=n,
            **kwargs
        )

        if not response.get("success"):
            raise Exception(f"Image generation failed: {response.get('error', 'Unknown error')}")

        result = response["result"]

        # Create OpenAI-compatible response object
        class ImageData:
            def __init__(self, url, revised_prompt=None):
                self.url = url
                self.revised_prompt = revised_prompt

        class ImagesResponse:
            def __init__(self, result_data, model_name):
                # Handle different response formats
                if isinstance(result_data, dict):
                    image_url = result_data.get('image_url', result_data.get('url'))
                    revised_prompt = result_data.get('revised_prompt')
                    self.data = [ImageData(image_url, revised_prompt)]
                elif isinstance(result_data, list):
                    self.data = [ImageData(url) for url in result_data]
                elif isinstance(result_data, str):
                    self.data = [ImageData(result_data)]
                else:
                    self.data = []

                self.created = int(asyncio.get_event_loop().time())
                self.model = model_name

            def __repr__(self):
                return f"ImagesResponse(model='{self.model}', images={len(self.data)})"

        return ImagesResponse(result, model)


class AsyncImages:
    """Async images endpoint namespace (OpenAI-compatible)"""

    def __init__(self, client):
        self.generate = AsyncImagesGenerations(client).generate
        # TODO: Add edit, variations endpoints


class AsyncVisionCompletions:
    """Async vision completions endpoint"""

    def __init__(self, client):
        self._client = client

    async def create(
        self,
        image: Union[str, bytes],
        prompt: str = "Describe this image in detail",
        model: str = "gpt-4o-mini",
        provider: str = "openai",
        **kwargs
    ):
        """
        Analyze an image using vision models

        Args:
            image: Image URL, file path, or bytes data
            prompt: Text prompt/question about the image
            model: Model name (gpt-4o-mini, gpt-4o, vision-model for ISA, etc.)
            provider: Provider name (openai, isa, replicate, yyds)
            **kwargs: Additional parameters

        Returns:
            Vision analysis response with .text attribute
        """
        # Handle local file paths - convert to base64 for API transmission
        import os
        import base64

        if isinstance(image, str) and os.path.isfile(image):
            # Read local file and convert to base64
            with open(image, "rb") as f:
                image_data = f.read()
            image_input = base64.b64encode(image_data).decode("utf-8")
        elif isinstance(image, bytes):
            # Convert bytes to base64
            image_input = base64.b64encode(image).decode("utf-8")
        else:
            # Pass through (URL or already base64)
            image_input = image

        # Call the API
        response = await self._client._underlying_client.invoke(
            input_data=image_input,
            task="analyze",
            service_type="vision",
            model=model,
            provider=provider,
            prompt=prompt,
            **kwargs
        )

        if not response.get("success"):
            raise Exception(f"Vision analysis failed: {response.get('error', 'Unknown error')}")

        result = response["result"]

        # Create response object
        class VisionResponse:
            def __init__(self, result_data, model_name, provider_name):
                # Handle different response formats
                if isinstance(result_data, dict):
                    self.text = result_data.get('text', str(result_data))
                    self.confidence = result_data.get('confidence')
                    self.detected_objects = result_data.get('detected_objects', [])
                    self.metadata = result_data.get('metadata', {})
                elif isinstance(result_data, str):
                    self.text = result_data
                    self.confidence = None
                    self.detected_objects = []
                    self.metadata = {}
                else:
                    self.text = str(result_data)
                    self.confidence = None
                    self.detected_objects = []
                    self.metadata = {}

                self.model = model_name
                self.provider = provider_name

            def __repr__(self):
                return f"VisionResponse(model='{self.model}', provider='{self.provider}', text_length={len(self.text)})"

        return VisionResponse(result, model, provider)


class AsyncVision:
    """Async vision endpoint namespace"""

    def __init__(self, client):
        self.completions = AsyncVisionCompletions(client)


class AsyncChat:
    """Async chat endpoint namespace"""

    def __init__(self, client):
        self.completions = AsyncChatCompletions(client)


class AsyncISAModel:
    """
    Async OpenAI-compatible client for ISA Model service (like AsyncOpenAI)

    Usage:
        # Create async client
        client = AsyncISAModel()

        # Must use await
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Streaming
        async for chunk in client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}],
            stream=True
        ):
            print(chunk.choices[0].delta.content or "", end="")

        # Context manager
        async with AsyncISAModel() as client:
            response = await client.chat.completions.create(...)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """Initialize async ISA Model client"""
        if api_key is None:
            api_key = os.getenv("ISA_API_KEY")

        if base_url is None:
            base_url = os.getenv("ISA_API_URL") or os.getenv("ISA_SERVICE_URL") or "http://localhost:8082"

        # Use standalone HTTP client (no dependency on old client.py)
        self._http_client = HTTPClient(base_url, api_key)
        self._base_url = base_url

        # For backward compatibility with examples that use _underlying_client
        # Create a simple object that has an invoke method
        class LegacyClientAdapter:
            def __init__(self, http_client):
                self._http = http_client

            async def invoke(self, **kwargs):
                """Compatibility method for legacy examples"""
                stream = kwargs.pop('stream', False)
                if stream:
                    # Not implemented for legacy adapter
                    raise NotImplementedError("Use client.chat.completions.create() for streaming")
                return await self._http.post_json("api/v1/invoke", kwargs)

        self._underlying_client = LegacyClientAdapter(self._http_client)

        self.chat = AsyncChat(self)
        self.audio = AsyncAudio(self)
        self.embeddings = AsyncEmbeddings(self)
        self.images = AsyncImages(self)
        self.vision = AsyncVision(self)

    async def close(self):
        """Close the client and cleanup resources"""
        await self._http_client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    def __repr__(self):
        return f"AsyncISAModel(base_url='{self._base_url}')"


# ============================================================================
# SYNC CLIENT (Wraps async, like OpenAI)
# ============================================================================

class ISAModel:
    """
    Sync OpenAI-compatible client for ISA Model service (like OpenAI)

    Usage:
        # Local mode (direct inference)
        client = ISAModel()

        # API mode (remote service)
        client = ISAModel(api_key="your-key", base_url="http://localhost:8082")

        # Chat
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)

        # Streaming
        for chunk in client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}],
            stream=True
        ):
            print(chunk.choices[0].delta.content or "", end="")

        # Audio
        audio = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input="Hello world"
        )

        # Embeddings
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="Your text"
        )
        print(response.data[0].embedding[:5])

        # Images
        response = client.images.generate(
            model="dall-e-3",
            prompt="A beautiful sunset"
        )
        print(response.data[0].url)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize ISA Model client (sync wrapper around AsyncISAModel)

        Args:
            api_key: API key (optional, uses ISA_API_KEY env var if not provided)
            base_url: Service URL (optional, uses http://localhost:8082 if not provided)
            **kwargs: Additional configuration
        """
        # Get API key from env if not provided
        if api_key is None:
            api_key = os.getenv("ISA_API_KEY")

        # Get base URL from env if not provided
        if base_url is None:
            base_url = os.getenv("ISA_API_URL") or os.getenv("ISA_SERVICE_URL") or "http://localhost:8082"

        # Use AsyncISAModel internally (we'll wrap calls with sync adapter)
        self._async_client = AsyncISAModel(api_key=api_key, base_url=base_url, **kwargs)
        self._base_url = base_url

        # Compatibility: Create a legacy adapter for Audio/Embeddings/Images
        # These still use the old invoke() method
        self._underlying_client = self._async_client._underlying_client

        # Initialize endpoint namespaces
        self.chat = Chat(self)
        self.audio = Audio(self)
        self.embeddings = Embeddings(self)
        self.images = Images(self)

    def __repr__(self):
        return f"ISAModel(base_url='{self._base_url}')"


# Export both sync and async clients
__all__ = ["ISAModel", "AsyncISAModel", "ChatCompletion", "Message", "Choice", "Usage"]

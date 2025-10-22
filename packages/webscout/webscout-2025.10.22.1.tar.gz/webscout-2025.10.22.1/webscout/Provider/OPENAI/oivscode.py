import random
import secrets
import requests
import json
import time
import uuid
import string
from typing import List, Dict, Optional, Union, Generator, Any

# Import base classes and utility structures
from webscout.Provider.OPENAI.base import OpenAICompatibleProvider, BaseChat, BaseCompletions
from webscout.Provider.OPENAI.utils import (
    ChatCompletionChunk, ChatCompletion, Choice, ChoiceDelta,
    ChatCompletionMessage, CompletionUsage
)

# --- oivscode Client ---

class Completions(BaseCompletions):
    def __init__(self, client: 'oivscode'):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = 2049,
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        timeout: Optional[int] = None,
        proxies: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        Creates a model response for the given chat conversation.
        Mimics openai.chat.completions.create
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p

        payload.update(kwargs)

        request_id = f"chatcmpl-{uuid.uuid4()}"
        created_time = int(time.time())

        if stream:
            return self._create_stream(request_id, created_time, model, payload, timeout, proxies)
        else:
            return self._create_non_stream(request_id, created_time, model, payload, timeout, proxies)

    def _post_with_retry(self, payload, stream=False, timeout=None, proxies=None):
        """
        Try all endpoints until one succeeds or all fail.
        """
        last_exception = None
        for endpoint in self._client.api_endpoints:
            try:
                response = self._client.session.post(
                    endpoint,
                    headers=self._client.headers,
                    json=payload,
                    stream=stream,
                    timeout=timeout or self._client.timeout,
                    proxies=proxies or getattr(self._client, "proxies", None)
                )
                response.raise_for_status()
                self._client.base_url = endpoint  # Update to working endpoint
                return response
            except requests.exceptions.RequestException as e:
                last_exception = e
                continue
        raise IOError(f"All oivscode endpoints failed: {last_exception}") from last_exception

    def _create_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any], timeout: Optional[int] = None, proxies: Optional[Dict[str, str]] = None
    ) -> Generator[ChatCompletionChunk, None, None]:
        try:
            response = self._post_with_retry(payload, stream=True, timeout=timeout, proxies=proxies)
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').strip()

                    if decoded_line.startswith("data: "):
                        json_str = decoded_line[6:]
                        if json_str == "[DONE]":
                            break
                        try:
                            data = json.loads(json_str)
                            choice_data = data.get('choices', [{}])[0]
                            delta_data = choice_data.get('delta', {})
                            finish_reason = choice_data.get('finish_reason')

                            usage_data = data.get('usage', {})
                            if usage_data:
                                prompt_tokens = usage_data.get('prompt_tokens', prompt_tokens)
                                completion_tokens = usage_data.get('completion_tokens', completion_tokens)
                                total_tokens = usage_data.get('total_tokens', total_tokens)

                            delta = ChoiceDelta(
                                content=delta_data.get('content'),
                                role=delta_data.get('role'),
                                tool_calls=delta_data.get('tool_calls')
                            )

                            choice = Choice(
                                index=choice_data.get('index', 0),
                                delta=delta,
                                finish_reason=finish_reason,
                                logprobs=choice_data.get('logprobs')
                            )

                            chunk = ChatCompletionChunk(
                                id=request_id,
                                choices=[choice],
                                created=created_time,
                                model=model,
                                system_fingerprint=data.get('system_fingerprint')
                            )

                            if hasattr(chunk, "model_dump"):
                                chunk_dict = chunk.model_dump(exclude_none=True)
                            else:
                                chunk_dict = chunk.dict(exclude_none=True)

                            usage_dict = {
                                "prompt_tokens": prompt_tokens or 10,
                                "completion_tokens": completion_tokens or (len(delta_data.get('content', '')) if delta_data.get('content') else 0),
                                "total_tokens": total_tokens or (10 + (len(delta_data.get('content', '')) if delta_data.get('content') else 0)),
                                "estimated_cost": None
                            }

                            if delta_data.get('content'):
                                completion_tokens += 1
                                total_tokens = prompt_tokens + completion_tokens
                                usage_dict["completion_tokens"] = completion_tokens
                                usage_dict["total_tokens"] = total_tokens

                            chunk_dict["usage"] = usage_dict

                            yield chunk
                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode JSON line: {json_str}")
                            continue
        except requests.exceptions.RequestException as e:
            print(f"Error during oivscode stream request: {e}")
            raise IOError(f"oivscode request failed: {e}") from e
        except Exception as e:
            print(f"Error processing oivscode stream: {e}")
            raise

    def _create_non_stream(
        self, request_id: str, created_time: int, model: str, payload: Dict[str, Any], timeout: Optional[int] = None, proxies: Optional[Dict[str, str]] = None
    ) -> ChatCompletion:
        try:
            response = self._post_with_retry(payload, stream=False, timeout=timeout, proxies=proxies)
            data = response.json()

            choices_data = data.get('choices', [])
            usage_data = data.get('usage', {})

            choices = []
            for choice_d in choices_data:
                message_d = choice_d.get('message', {})
                message = ChatCompletionMessage(
                    role=message_d.get('role', 'assistant'),
                    content=message_d.get('content', '')
                )
                choice = Choice(
                    index=choice_d.get('index', 0),
                    message=message,
                    finish_reason=choice_d.get('finish_reason', 'stop')
                )
                choices.append(choice)

            usage = CompletionUsage(
                prompt_tokens=usage_data.get('prompt_tokens', 0),
                completion_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0)
            )

            completion = ChatCompletion(
                id=request_id,
                choices=choices,
                created=created_time,
                model=data.get('model', model),
                usage=usage,
            )
            return completion

        except requests.exceptions.RequestException as e:
            print(f"Error during oivscode non-stream request: {e}")
            raise IOError(f"oivscode request failed: {e}") from e
        except Exception as e:
            print(f"Error processing oivscode response: {e}")
            raise

class Chat(BaseChat):
    def __init__(self, client: 'oivscode'):
        self.completions = Completions(client)

class oivscode(OpenAICompatibleProvider):
    
    AVAILABLE_MODELS = [
        "*",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-20241022",
        "claude-3-7-sonnet-20250219",
        "custom/blackbox-base",
        "custom/blackbox-pro",
        "custom/blackbox-pro-designer",
        "custom/blackbox-pro-plus",
        "deepseek-r1",
        "deepseek-v3",
        "deepseek/deepseek-chat",
        "gemini-2.5-pro-preview-03-25",
        "gpt-4o-mini",
        "grok-3-beta",
        "image-gen",
        "llama-4-maverick-17b-128e-instruct-fp8",
        "o1",
        "o3-mini",
        "o4-mini",
        "transcribe",
        "anthropic/claude-sonnet-4"
    ]

    def __init__(self, timeout: Optional[int] = None):
        self.timeout = timeout
        self.api_endpoints = [
            "https://oi-vscode-server.onrender.com/v1/chat/completions",
            "https://oi-vscode-server-2.onrender.com/v1/chat/completions",
            "https://oi-vscode-server-5.onrender.com/v1/chat/completions",
            "https://oi-vscode-server-0501.onrender.com/v1/chat/completions"
        ]
        self.api_endpoint = random.choice(self.api_endpoints)
        self.base_url = self.api_endpoint
        self.session = requests.Session()
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,en-GB;q=0.8,en-IN;q=0.7",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }
        self.userid = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(21))
        self.headers["userid"] = self.userid
        self.session.headers.update(self.headers)
        self.chat = Chat(self)

    @property
    def models(self):
        class _ModelList:
            def list(inner_self):
                return type(self).AVAILABLE_MODELS
        return _ModelList()

if __name__ == "__main__":
    # Example usage
    client = oivscode()
    chat = client.chat
    response = chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct-Turbo",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        max_tokens=50,
        stream=False
    )
    print(response)

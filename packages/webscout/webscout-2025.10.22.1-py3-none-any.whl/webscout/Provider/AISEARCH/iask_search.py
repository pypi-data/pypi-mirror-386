import aiohttp
import asyncio
import lxml.html
import re
import urllib.parse
from markdownify import markdownify as md
from typing import Dict, Optional, Generator, Union, AsyncIterator, Literal

from webscout.AIbase import AISearch, SearchResponse
from webscout import exceptions
from webscout.scout import Scout


def cache_find(diff: Union[dict, list]) -> Optional[str]:
    """Find HTML content in a nested dictionary or list structure.

    Args:
        diff (Union[dict, list]): The nested structure to search

    Returns:
        Optional[str]: The found HTML content, or None if not found
    """
    values = diff if isinstance(diff, list) else diff.values()
    for value in values:
        if isinstance(value, (list, dict)):
            cache = cache_find(value)
            if cache:
                return cache
        if isinstance(value, str) and re.search(r"<p>.+?</p>", value):
            return md(value).strip()

    return None


ModeType = Literal["question", "academic", "fast", "forums", "wiki", "advanced"]
DetailLevelType = Literal["concise", "detailed", "comprehensive"]


class IAsk(AISearch):
    """A class to interact with the IAsk AI search API.

    IAsk provides a powerful search interface that returns AI-generated responses
    based on web content. It supports both streaming and non-streaming responses,
    as well as different search modes and detail levels.

    Basic Usage:
        >>> from webscout import IAsk
        >>> ai = IAsk()
        >>> # Non-streaming example
        >>> response = ai.search("What is Python?")
        >>> print(response)
        Python is a high-level programming language...

        >>> # Streaming example
        >>> for chunk in ai.search("Tell me about AI", stream=True):
        ...     print(chunk, end="", flush=True)
        Artificial Intelligence is...

        >>> # With specific mode and detail level
        >>> response = ai.search("Climate change", mode="academic", detail_level="detailed")
        >>> print(response)
        Climate change refers to...

    Args:
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
        proxies (dict, optional): Proxy configuration for requests. Defaults to None.
        mode (ModeType, optional): Default search mode. Defaults to "question".
        detail_level (DetailLevelType, optional): Default detail level. Defaults to None.
    """

    def __init__(
        self,
        timeout: int = 30,
        proxies: Optional[dict] = None,
        mode: ModeType = "question",
        detail_level: Optional[DetailLevelType] = None,
    ):
        """Initialize the IAsk API client.

        Args:
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            proxies (dict, optional): Proxy configuration for requests. Defaults to None.
            mode (ModeType, optional): Default search mode. Defaults to "question".
            detail_level (DetailLevelType, optional): Default detail level. Defaults to None.
        """
        self.timeout = timeout
        self.proxies = proxies or {}
        self.default_mode = mode
        self.default_detail_level = detail_level
        self.api_endpoint = "https://iask.ai/"
        self.last_response = {}

    def create_url(self, query: str, mode: ModeType = "question", detail_level: Optional[DetailLevelType] = None) -> str:
        """Create a properly formatted URL with mode and detail level parameters.

        Args:
            query (str): The search query.
            mode (ModeType, optional): Search mode. Defaults to "question".
            detail_level (DetailLevelType, optional): Detail level. Defaults to None.

        Returns:
            str: Formatted URL with query parameters.

        Example:
            >>> ai = IAsk()
            >>> url = ai.create_url("Climate change", mode="academic", detail_level="detailed")
            >>> print(url)
            https://iask.ai/?mode=academic&q=Climate+change&options%5Bdetail_level%5D=detailed
        """
        # Create a dictionary of parameters with flattened structure
        params = {
            "mode": mode,
            "q": query
        }

        # Add detail_level if provided using the flattened format
        if detail_level:
            params["options[detail_level]"] = detail_level

        # Encode the parameters and build the URL
        query_string = urllib.parse.urlencode(params)
        url = f"{self.api_endpoint}?{query_string}"

        return url

    def format_html(self, html_content: str) -> str:
        """Format HTML content into a more readable text format.

        Args:
            html_content (str): The HTML content to format.

        Returns:
            str: Formatted text.
        """
        scout = Scout(html_content, features='html.parser')
        output_lines = []

        for child in scout.find_all(['h1', 'h2', 'h3', 'p', 'ol', 'ul', 'div']):
            if child.name in ["h1", "h2", "h3"]:
                output_lines.append(f"\n**{child.get_text().strip()}**\n")
            elif child.name == "p":
                text = child.get_text().strip()
                text = re.sub(r"^According to Ask AI & Question AI www\.iAsk\.ai:\s*", "", text).strip()
                # Remove footnote markers
                text = re.sub(r'\[\d+\]\(#fn:\d+ \'see footnote\'\)', '', text)
                output_lines.append(text + "\n")
            elif child.name in ["ol", "ul"]:
                for li in child.find_all("li"):
                    output_lines.append("- " + li.get_text().strip() + "\n")
            elif child.name == "div" and "footnotes" in child.get("class", []):
                output_lines.append("\n**Authoritative Sources**\n")
                for li in child.find_all("li"):
                    link = li.find("a")
                    if link:
                        output_lines.append(f"- {link.get_text().strip()} ({link.get('href')})\n")

        return "".join(output_lines)

    def search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        mode: Optional[ModeType] = None,
        detail_level: Optional[DetailLevelType] = None,
    ) -> Union[SearchResponse, Generator[Union[Dict[str, str], SearchResponse], None, None]]:
        """Search using the IAsk API and get AI-generated responses.

        This method sends a search query to IAsk and returns the AI-generated response.
        It supports both streaming and non-streaming modes, as well as raw response format.

        Args:
            prompt (str): The search query or prompt to send to the API.
            stream (bool, optional): If True, yields response chunks as they arrive.
                                   If False, returns complete response. Defaults to False.
            raw (bool, optional): If True, returns raw response dictionaries with 'text' key.
                                If False, returns Response objects that convert to text automatically.
                                Defaults to False.
            mode (ModeType, optional): Search mode to use. Defaults to None (uses instance default).
            detail_level (DetailLevelType, optional): Detail level to use. Defaults to None (uses instance default).

        Returns:
            Union[Response, Generator[Union[Dict[str, str], Response], None, None]]:
                - If stream=False: Returns complete response as Response object
                - If stream=True: Yields response chunks as either Dict or Response objects

        Raises:
            APIConnectionError: If the API request fails

        Examples:
            Basic search:
            >>> ai = IAsk()
            >>> response = ai.search("What is Python?")
            >>> print(response)
            Python is a programming language...

            Streaming response:
            >>> for chunk in ai.search("Tell me about AI", stream=True):
            ...     print(chunk, end="")
            Artificial Intelligence...

            Raw response format:
            >>> for chunk in ai.search("Hello", stream=True, raw=True):
            ...     print(chunk)
            {'text': 'Hello'}
            {'text': ' there!'}

            With specific mode and detail level:
            >>> response = ai.search("Climate change", mode="academic", detail_level="detailed")
            >>> print(response)
            Climate change refers to...
        """
        # Use provided parameters or fall back to instance defaults
        search_mode = mode or self.default_mode
        search_detail_level = detail_level or self.default_detail_level

        # For non-streaming, run the async search and return the complete response
        if not stream:
            # Create a new event loop for this request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self._async_search(prompt, False, raw, search_mode, search_detail_level)
                )
                return result
            finally:
                loop.close()

        # For streaming, use a simpler approach with a single event loop
        # that stays open until the generator is exhausted
        buffer = ""

        def sync_generator():
            nonlocal buffer
            # Create a new event loop for this generator
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Get the async generator
                async_gen_coro = self._async_search(prompt, True, raw, search_mode, search_detail_level)
                async_gen = loop.run_until_complete(async_gen_coro)

                # Process chunks one by one
                while True:
                    try:
                        # Get the next chunk
                        chunk_coro = async_gen.__anext__()
                        chunk = loop.run_until_complete(chunk_coro)

                        # Update buffer and yield the chunk
                        if isinstance(chunk, dict) and 'text' in chunk:
                            buffer += chunk['text']
                        elif isinstance(chunk, SearchResponse):
                            buffer += chunk.text
                        else:
                            buffer += str(chunk)

                        yield chunk
                    except StopAsyncIteration:
                        break
                    except Exception as e:
                        print(f"Error in generator: {e}")
                        break
            finally:
                # Store the final response and close the loop
                self.last_response = {"text": buffer}
                loop.close()

        return sync_generator()

    async def _async_search(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        mode: ModeType = "question",
        detail_level: Optional[DetailLevelType] = None,
    ) -> Union[SearchResponse, AsyncIterator[Union[Dict[str, str], SearchResponse]]]:
        """Internal async implementation of the search method."""

        async def stream_generator() -> AsyncIterator[str]:
            async with aiohttp.ClientSession() as session:
                # Prepare parameters
                params = {"mode": mode, "q": prompt}
                if detail_level:
                    params["options[detail_level]"] = detail_level

                try:
                    async with session.get(
                        self.api_endpoint,
                        params=params,
                        proxy=self.proxies.get('http') if self.proxies else None,
                        timeout=self.timeout
                    ) as response:
                        if not response.ok:
                            raise exceptions.APIConnectionError(
                                f"Failed to generate response - ({response.status_code}, {response.reason}) - {await response.text()}"
                            )

                        etree = lxml.html.fromstring(await response.text())
                        phx_node = etree.xpath('//*[starts-with(@id, "phx-")]').pop()
                        csrf_token = (
                            etree.xpath('//*[@name="csrf-token"]').pop().get("content")
                        )

                    async with session.ws_connect(
                        f"{self.api_endpoint}live/websocket",
                        params={
                            "_csrf_token": csrf_token,
                            "vsn": "2.0.0",
                        },
                        proxy=self.proxies.get('http') if self.proxies else None,
                        timeout=self.timeout
                    ) as wsResponse:
                        await wsResponse.send_json(
                            [
                                None,
                                None,
                                f"lv:{phx_node.get('id')}",
                                "phx_join",
                                {
                                    "params": {"_csrf_token": csrf_token},
                                    "url": str(response.url),
                                    "session": phx_node.get("data-phx-session"),
                                },
                            ]
                        )
                        while True:
                            json_data = await wsResponse.receive_json()
                            if not json_data:
                                break
                            diff: dict = json_data[4]
                            try:
                                chunk: str = diff["e"][0][1]["data"]
                                # Check if the chunk contains HTML content
                                if re.search(r"<[^>]+>", chunk):
                                    formatted_chunk = self.format_html(chunk)
                                    yield formatted_chunk
                                else:
                                    yield chunk.replace("<br/>", "\n")
                            except:
                                cache = cache_find(diff)
                                if cache:
                                    if diff.get("response", None):
                                        # Format the cache content if it contains HTML
                                        if re.search(r"<[^>]+>", cache):
                                            formatted_cache = self.format_html(cache)
                                            yield formatted_cache
                                        else:
                                            yield cache
                                    break
                except Exception as e:
                    raise exceptions.APIConnectionError(f"Error connecting to IAsk API: {str(e)}")

        # For non-streaming, collect all chunks and return a single response
        if not stream:
            buffer = ""
            async for chunk in stream_generator():
                buffer += chunk
            self.last_response = {"text": buffer}
            return SearchResponse(buffer) if not raw else {"text": buffer}

        # For streaming, create an async generator that yields chunks
        async def process_stream():
            buffer = ""
            async for chunk in stream_generator():
                buffer += chunk
                if raw:
                    yield {"text": chunk}
                else:
                    yield SearchResponse(chunk)
            self.last_response = {"text": buffer}

        # Return the async generator
        return process_stream()


if __name__ == "__main__":
    from rich import print

    ai = IAsk()

    # Example 1: Simple search with default mode
    print("\n[bold cyan]Example 1: Simple search with default mode[/bold cyan]")
    response = ai.search("What is Python?", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
    print("\n\n[bold green]Response complete.[/bold green]\n")

    # Example 2: Search with academic mode
    print("\n[bold cyan]Example 2: Search with academic mode[/bold cyan]")
    response = ai.search("Quantum computing applications", mode="academic", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
    print("\n\n[bold green]Response complete.[/bold green]\n")

    # Example 3: Search with advanced mode and detailed level
    print("\n[bold cyan]Example 3: Search with advanced mode and detailed level[/bold cyan]")
    response = ai.search("Climate change solutions", mode="advanced", detail_level="detailed", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)
    print("\n\n[bold green]Response complete.[/bold green]\n")

    # Example 4: Demonstrating the create_url method
    print("\n[bold cyan]Example 4: Generated URL for browser access[/bold cyan]")
    url = ai.create_url("Helpingai details", mode="question", detail_level="detailed")
    print(f"URL: {url}")
    print("This URL can be used directly in a browser or with other HTTP clients.")

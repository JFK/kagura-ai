import ssl
from typing import Optional, Tuple, Union

import aiohttp
import chardet

from kagura.core.models import (StateModel, get_custom_model,
                                validate_required_state_fields)


class ContentFetcherError(Exception):
    pass


class ContentFetcher:
    _instance = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ContentFetcher, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _fetch_content_with_different_ssl(self, url: str) -> Optional[str]:
        ssl_contexts = []

        default_ssl_context = ssl.create_default_context()
        ssl_contexts.append(("Default SSL", default_ssl_context))

        unrestricted_ssl_context = ssl.create_default_context()
        unrestricted_ssl_context.minimum_version = ssl.TLSVersion.SSLv3
        unrestricted_ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_contexts.append(("Unrestricted TLS Versions", unrestricted_ssl_context))

        no_verify_ssl_context = ssl.create_default_context()
        no_verify_ssl_context.check_hostname = False
        no_verify_ssl_context.verify_mode = ssl.CERT_NONE
        ssl_contexts.append(("No Verify SSL", no_verify_ssl_context))

        for name, ssl_context in ssl_contexts:
            content = await self._fetch_with_ssl_context(url, ssl_context)
            if content is not None:
                return content
        return None

    def _detect_content_format(self, content_type: str) -> str:
        if "pdf" in content_type:
            return "pdf"
        elif "docx" in content_type:
            return "docx"
        elif "pptx" in content_type:
            return "pptx"
        elif "html" in content_type:
            return "html"
        elif "xml" in content_type:
            return "xml"
        elif "json" in content_type:
            return "json"
        return "webpage"

    async def _fetch_with_ssl_context(
        self, url: str, ssl_context: ssl.SSLContext, timeout: int = 10
    ) -> Tuple[Optional[Union[str, bytes]], str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        ENCODING_MAP = {
            "windows-31j": "cp932",
            "shift-jis": "cp932",
            "shift_jis": "cp932",
            "sjis": "cp932",
            "x-sjis": "cp932",
            "ms932": "cp932",
        }

        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(
                connector=connector, headers=headers
            ) as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:

                        content = await response.read()

                        encodings_to_try = []

                        content_type = response.headers.get("Content-Type", "").lower()
                        if "charset=" in content_type:
                            declared_encoding = (
                                content_type.split("charset=")[-1].split(";")[0].strip()
                            )
                            declared_encoding = ENCODING_MAP.get(
                                declared_encoding, declared_encoding
                            )
                            encodings_to_try.append(declared_encoding)

                        encodings_to_try.extend(
                            ["utf-8", "cp932", "euc-jp", "iso-2022-jp"]
                        )

                        if content.startswith(b"<"):
                            try:

                                detected = chardet.detect(content)
                                if (
                                    detected["encoding"]
                                    and detected["confidence"] > 0.7
                                ):
                                    detected_encoding = ENCODING_MAP.get(
                                        detected["encoding"].lower(),
                                        detected["encoding"],
                                    )
                                    if detected_encoding not in encodings_to_try:
                                        encodings_to_try.insert(0, detected_encoding)
                            except ImportError:
                                pass

                        detected_content_format = self._detect_content_format(
                            content_type
                        )

                        last_error = None
                        for encoding in encodings_to_try:
                            try:
                                return (
                                    content.decode(encoding),
                                    detected_content_format,
                                )
                            except (UnicodeDecodeError, LookupError) as e:
                                last_error = e
                                continue

                        if last_error:
                            raise ContentFetcherError(
                                f"Failed to decode content from {url} with encodings {encodings_to_try}: {last_error}"
                            )

                        try:
                            return (
                                content.decode("utf-8", errors="ignore"),
                                detected_content_format,
                            )
                        except Exception as e:
                            raise ContentFetcherError(
                                f"Final fallback decode failed for {url}: {e}"
                            )

        except Exception as e:
            raise ContentFetcherError(f"Failed to fetch {url} with SSL context: {e}")

    async def fetch(self, url: str) -> Tuple[str, str]:
        try:
            content, content_format = await self._fetch_content_with_different_ssl(url)
            if content is None:
                raise ContentFetcherError(f"Failed to fetch content from {url}")
            return content, content_format
        except Exception as e:
            raise ContentFetcherError(f"Failed to fetch from {url}: {e}")


async def fetch(state: StateModel) -> StateModel:

    ContentItem = get_custom_model("ContentItem")

    validate_required_state_fields(state, ["url"])

    try:
        content, content_format = await ContentFetcher.get_instance().fetch(state.url)
        state.content = ContentItem(
            text=content, content_type=content_format, url=state.url
        )
        return state
    except Exception as e:
        raise ContentFetcherError(str(e))

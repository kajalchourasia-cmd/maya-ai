"""Embedding boundary for approved public evidence.

Production configuration is OpenAI-compatible so the team can select one provider
without changing ingestion. Tests use a clearly labelled non-semantic fake.
"""

from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Protocol
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validated_embedding_vectors(payload: dict, count: int, model: str,
                                dimensions: int | None = None) -> list[list[float]]:
    if payload.get('model') != model or not isinstance(payload.get('data'), list):
        raise ValueError('embedding provider returned an unexpected model or data shape')
    rows = payload['data']
    if any(not isinstance(row, dict) or type(row.get('index')) is not int for row in rows):
        raise ValueError('embedding response indices are invalid')
    rows = sorted(rows, key=lambda row: row['index'])
    if [row['index'] for row in rows] != list(range(count)):
        raise ValueError('embedding response indices are missing or duplicated')
    vectors = [row.get('embedding') for row in rows]
    if not vectors or any(not isinstance(v, list) or not v for v in vectors):
        raise ValueError('embedding provider returned incomplete vectors')
    expected = dimensions or len(vectors[0])
    if any(len(v) != expected or any(type(n) not in (int, float) or not math.isfinite(n) for n in v)
           or not any(n != 0 for n in v) for v in vectors):
        raise ValueError('embedding provider returned invalid numeric vectors or dimensions')
    return vectors


class EmbeddingProvider(Protocol):
    name: str
    model: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAICompatibleEmbeddingProvider:
    def __init__(self, *, name: str, base_url: str, api_key: str, model: str,
                 timeout_seconds: int = 30, maximum_response_bytes: int = 10 * 1024 * 1024,
                 dimensions: int | None = None):
        if not all(value.strip() for value in (name, base_url, api_key, model)):
            raise ValueError("embedding provider name, URL, API key and model are required")
        parsed = urlsplit(base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("embedding endpoint must be a public HTTPS URL without credentials")
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.maximum_response_bytes = maximum_response_bytes
        if dimensions is not None and (type(dimensions) is not int or dimensions <= 0):
            raise ValueError('embedding dimension must be a positive integer')
        self.dimensions = dimensions
        self.last_response_metadata: dict = {}

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.last_response_metadata = {}
        if not texts:
            return []
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError('embedding inputs must be nonempty strings')
        parameters = {"model": self.model, "input": texts, 'encoding_format': 'float'}
        if self.dimensions is not None:
            parameters['dimensions'] = self.dimensions
        body = json.dumps(parameters).encode("utf-8")
        request = Request(self.base_url, data=body, method="POST",
                          headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        with build_opener(_NoRedirect()).open(request, timeout=self.timeout_seconds) as response:
            raw = response.read(self.maximum_response_bytes + 1)
            self.last_response_metadata = {'http_status': response.status,
                                           'request_id': response.headers.get('x-request-id')}
        if len(raw) > self.maximum_response_bytes:
            raise ValueError("embedding provider response exceeds the size limit")
        payload = json.loads(raw)
        vectors = validated_embedding_vectors(payload, len(texts), self.model, self.dimensions)
        self.last_response_metadata.update({'model': payload['model'], 'usage': payload.get('usage')})
        return vectors


class DeterministicTestEmbeddingProvider:
    """Non-semantic test double. Never use it for a published corpus."""

    name = "TEST_ONLY"
    model = "sha256-test-vector-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[(byte - 127.5) / 127.5 for byte in sha256(text.encode("utf-8")).digest()]
                for text in texts]

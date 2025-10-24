import logging
import os
import sys
import threading
from dataclasses import dataclass, field, fields
from typing import Any, Dict

from arize.constants.config import (
    DEFAULT_API_HOST,
    DEFAULT_ARIZE_DIRECTORY,
    DEFAULT_ENABLE_CACHING,
    DEFAULT_FLIGHT_HOST,
    DEFAULT_FLIGHT_PORT,
    DEFAULT_FLIGHT_TRANSPORT_SCHEME,
    DEFAULT_INSECURE,
    DEFAULT_MAX_HTTP_PAYLOAD_SIZE_MB,
    DEFAULT_OTLP_HOST,
    DEFAULT_PYARROW_MAX_CHUNKSIZE,
    DEFAULT_REQUEST_VERIFY,
    DEFAULT_STREAM_MAX_QUEUE_BOUND,
    DEFAULT_STREAM_MAX_WORKERS,
    ENV_API_HOST,
    ENV_API_KEY,
    ENV_ARIZE_DIRECTORY,
    ENV_ENABLE_CACHING,
    ENV_FLIGHT_HOST,
    ENV_FLIGHT_PORT,
    ENV_FLIGHT_TRANSPORT_SCHEME,
    ENV_INSECURE,
    ENV_MAX_HTTP_PAYLOAD_SIZE_MB,
    ENV_OTLP_HOST,
    ENV_PYARROW_MAX_CHUNKSIZE,
    ENV_REQUEST_VERIFY,
    ENV_STREAM_MAX_QUEUE_BOUND,
    ENV_STREAM_MAX_WORKERS,
)
from arize.constants.pyarrow import MAX_CHUNKSIZE
from arize.exceptions.auth import MissingAPIKeyError
from arize.version import __version__

logger = logging.getLogger(__name__)


def _parse_bool(val: bool | str | None) -> bool:
    if isinstance(val, bool):
        return val
    return (val or "").strip().lower() in {"1", "true", "yes", "on"}


def _api_key_factory() -> str:
    return os.getenv(ENV_API_KEY, "")


def _api_host_factory() -> str:
    return os.getenv(ENV_API_HOST, DEFAULT_API_HOST)


def _api_scheme_factory() -> str:
    insecure = os.getenv(ENV_INSECURE, DEFAULT_INSECURE)
    if insecure:
        return "http"
    return "https"


def _flight_host_factory() -> str:
    return os.getenv(ENV_FLIGHT_HOST, DEFAULT_FLIGHT_HOST)


def _flight_port_factory() -> int:
    return int(os.getenv(ENV_FLIGHT_PORT, DEFAULT_FLIGHT_PORT))


def _flight_scheme_factory() -> str:
    return os.getenv(
        ENV_FLIGHT_TRANSPORT_SCHEME, DEFAULT_FLIGHT_TRANSPORT_SCHEME
    )


def _pyarrow_max_chunksize() -> int:
    max_chunksize = int(
        os.getenv(ENV_PYARROW_MAX_CHUNKSIZE, DEFAULT_PYARROW_MAX_CHUNKSIZE)
    )
    if max_chunksize <= 0 or max_chunksize > MAX_CHUNKSIZE:
        raise ValueError(
            f"Pyarrow max_chunksize must be between 1 and {MAX_CHUNKSIZE}, got {max_chunksize}"
        )
    return max_chunksize


def _verify_factory() -> bool:
    return _parse_bool(os.getenv(ENV_REQUEST_VERIFY, DEFAULT_REQUEST_VERIFY))


def _stream_max_workers_factory() -> int:
    return int(os.getenv(ENV_STREAM_MAX_WORKERS, DEFAULT_STREAM_MAX_WORKERS))


def _stream_max_queue_bound_factory() -> int:
    return int(
        os.getenv(ENV_STREAM_MAX_QUEUE_BOUND, DEFAULT_STREAM_MAX_QUEUE_BOUND)
    )


def _otlp_scheme_factory() -> str:
    insecure = os.getenv(ENV_INSECURE, DEFAULT_INSECURE)
    if insecure:
        return "http"
    return "https"


def _otlp_host_factory() -> str:
    return os.getenv(ENV_OTLP_HOST, DEFAULT_OTLP_HOST)


def _max_http_payload_size_mb_factory() -> float:
    return float(
        os.getenv(
            ENV_MAX_HTTP_PAYLOAD_SIZE_MB, DEFAULT_MAX_HTTP_PAYLOAD_SIZE_MB
        )
    )


def _arize_dir_factory() -> str:
    return os.getenv(ENV_ARIZE_DIRECTORY, DEFAULT_ARIZE_DIRECTORY)


def _enable_cache_factory() -> bool:
    return _parse_bool(os.getenv(ENV_ENABLE_CACHING, DEFAULT_ENABLE_CACHING))


def _mask_secret(secret: str, N: int = 4) -> str:
    """Show first N chars then '***'; empty string if empty."""
    return f"{secret[:N]}***"


def _endpoint(scheme: str, base: str, path: str = "") -> str:
    endpoint = scheme + "://" + base.rstrip("/")
    if path:
        endpoint += "/" + path.lstrip("/")
    return endpoint


@dataclass(frozen=True)
class SDKConfiguration:
    api_key: str = field(default_factory=_api_key_factory)
    api_host: str = field(default_factory=_api_host_factory)
    api_scheme: str = field(default_factory=_api_scheme_factory)
    flight_server_host: str = field(default_factory=_flight_host_factory)
    flight_server_port: int = field(default_factory=_flight_port_factory)
    flight_scheme: str = field(default_factory=_flight_scheme_factory)
    pyarrow_max_chunksize: int = field(default_factory=_pyarrow_max_chunksize)
    request_verify: bool = field(default_factory=_verify_factory)
    stream_max_workers: int = field(default_factory=_stream_max_workers_factory)
    stream_max_queue_bound: int = field(
        default_factory=_stream_max_queue_bound_factory
    )
    otlp_host: str = field(default_factory=_otlp_host_factory)
    otlp_scheme: str = field(default_factory=_otlp_scheme_factory)
    max_http_payload_size_mb: float = field(
        default_factory=_max_http_payload_size_mb_factory
    )
    arize_direcory: str = field(default_factory=_arize_dir_factory)
    enable_caching: bool = field(default_factory=_enable_cache_factory)

    # Private, excluded from comparisons & repr
    _headers: Dict[str, str] = field(init=False, repr=False, compare=False)
    _gen_client: Any = field(default=None, repr=False, compare=False)
    _gen_lock: threading.Lock = field(
        default_factory=threading.Lock, repr=False, compare=False
    )

    def __post_init__(self):
        # Validate Configuration
        if not self.api_key:
            raise MissingAPIKeyError()

    @property
    def api_url(self) -> str:
        return _endpoint(self.api_scheme, self.api_host)

    @property
    def otlp_url(self) -> str:
        return _endpoint(self.otlp_scheme, self.otlp_host, "/v1")

    @property
    def files_url(self) -> str:
        return _endpoint(self.api_scheme, self.api_host, "/v1/pandas_arrow")

    @property
    def records_url(self) -> str:
        return _endpoint(self.api_scheme, self.api_host, "/v1/log")

    @property
    def headers(self) -> Dict[str, str]:
        # Create base headers
        return {
            "authorization": self.api_key,
            "sdk-language": "python",
            "language-version": get_python_version(),
            "sdk-version": __version__,
            # "arize-space-id": self._space_id,
            # "arize-interface": "batch",
            # "sync": "0",  # Defaults to async logging
        }

    @property
    def headers_grpc(self) -> Dict[str, str]:
        return {
            "authorization": self.api_key,
            "Grpc-Metadata-sdk-language": "python",
            "Grpc-Metadata-language-version": get_python_version(),
            "Grpc-Metadata-sdk-version": __version__,
            # "Grpc-Metadata-arize-space-id": space_id,
            # "Grpc-Metadata-arize-interface": "stream",
        }

    def __repr__(self) -> str:
        # Dynamically build repr for all fields
        lines = [f"{self.__class__.__name__}("]
        for f in fields(self):
            if not f.repr:
                continue
            val = getattr(self, f.name)
            if f.name == "api_key":
                val = _mask_secret(val, 6)
            lines.append(f"  {f.name}={val!r},")
        lines.append(")")
        return "\n".join(lines)

    # TODO(Kiko): This may not be well placed in this class
    def get_generated_client(self):
        # If already cached, return immediately
        if self._gen_client is not None:
            return self._gen_client

        # Thread-safe initialization
        with self._gen_lock:
            if self._gen_client is not None:
                return self._gen_client

            # Import lazily so extras can be enforced outside
            from arize._generated import api_client as gen

            cfg = gen.Configuration(host=self.api_url)
            if self.api_key:
                cfg.api_key["ApiKeyAuth"] = self.api_key
            client = gen.ApiClient(cfg)

            # Bypass frozen to set the cache once
            object.__setattr__(self, "_gen_client", client)
            return client


def get_python_version():
    return (
        f"{sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro}"
    )

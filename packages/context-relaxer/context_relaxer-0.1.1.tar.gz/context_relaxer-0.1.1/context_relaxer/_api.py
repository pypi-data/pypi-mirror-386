import functools
import ssl
import sys

try:
    import urllib3.util.ssl_ as urllib3_ssl

    original_create_urllib3_context = urllib3_ssl.create_urllib3_context
except ImportError:
    urllib3_ssl = None


    def original_create_urllib3_context(*args, **kwargs) -> ssl.SSLContext:
        raise NotImplementedError()

original_create_default_context = ssl.create_default_context


@functools.wraps(ssl.create_default_context)
def patched_create_default_context(purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None):
    context = original_create_default_context(purpose=purpose, cafile=cafile, capath=capath, cadata=cadata)
    # Remove the STRICT flag
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return context


@functools.wraps(original_create_urllib3_context)
def patched_create_urllib3_context(
        ssl_version: int | None = None,
        cert_reqs: int | None = None,
        options: int | None = None,
        ciphers: str | None = None,
        ssl_minimum_version: int | None = None,
        ssl_maximum_version: int | None = None,
        verify_flags: int | None = None,
) -> ssl.SSLContext:
    """
    In this function it is possible to pass flags, so we need to override in ingress
    """
    if verify_flags is None and sys.version_info >= (3, 13):
        verify_flags = ssl.VERIFY_X509_PARTIAL_CHAIN

    context = original_create_urllib3_context(
        ssl_version=ssl_version,
        cert_reqs=cert_reqs,
        options=options,
        ciphers=ciphers,
        ssl_minimum_version=ssl_minimum_version,
        ssl_maximum_version=ssl_maximum_version,
        verify_flags=verify_flags,
    )
    return context


def inject_into_ssl() -> None:
    setattr(ssl, "create_default_context", patched_create_default_context)
    setattr(ssl, "_create_default_https_context", patched_create_default_context)
    if urllib3_ssl:
        setattr(urllib3_ssl, "create_urllib3_context", patched_create_urllib3_context)


def extract_from_ssl() -> None:
    setattr(ssl, "create_default_context", original_create_default_context)
    setattr(ssl, "_create_default_https_context", original_create_default_context)
    if urllib3_ssl:
        setattr(urllib3_ssl, "create_urllib3_context", original_create_urllib3_context)

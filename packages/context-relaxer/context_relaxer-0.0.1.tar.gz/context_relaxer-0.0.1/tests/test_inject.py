import ssl
import sys

import pytest

import context_relaxer


@pytest.fixture(scope="function")
def inject_relaxer():
    context_relaxer.inject_into_ssl()
    try:
        yield
    finally:
        context_relaxer.extract_from_ssl()


def test_inject_and_extract():
    assert (
        ssl.create_default_context
        is not context_relaxer._api.patched_create_default_context
    )
    try:
        original_create_default_context = ssl.create_default_context

        context_relaxer.inject_into_ssl()
        assert (
            ssl.create_default_context
            is context_relaxer._api.patched_create_default_context
        )

        ctx = ssl.create_default_context()
        assert ctx.verify_flags & ssl.VERIFY_X509_STRICT == 0

        context_relaxer.extract_from_ssl()
        assert ssl.create_default_context is original_create_default_context

        ctx = ssl.create_default_context()
        if sys.version_info >= (3, 13):
            assert ctx.verify_flags & ssl.VERIFY_X509_STRICT == ssl.VERIFY_X509_STRICT
        else:
            assert ctx.verify_flags & ssl.VERIFY_X509_STRICT == 0
    finally:
        context_relaxer.extract_from_ssl()

import functools
import ssl

original_create_default_context = ssl.create_default_context


@functools.wraps(ssl.create_default_context)
def patched_create_default_context(
    purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None
):
    context = original_create_default_context(
        purpose=purpose, cafile=cafile, capath=capath, cadata=cadata
    )
    # Remove the STRICT flag
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return context


def inject_into_ssl() -> None:
    setattr(ssl, "create_default_context", patched_create_default_context)


def extract_from_ssl() -> None:
    setattr(ssl, "create_default_context", original_create_default_context)

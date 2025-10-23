"""
PDFDancer Python Client

A Python client library for the PDFDancer PDF manipulation API.
Provides a clean, Pythonic interface for PDF operations that closely
mirrors the Java client structure and functionality.
"""

from .exceptions import (
    PdfDancerException, FontNotFoundException, ValidationException,
    HttpClientException, SessionException
)
from .models import (
    ObjectRef, Position, ObjectType, Font, Color, Image, BoundingRect, Paragraph, FormFieldRef, TextObjectRef,
    PageRef, PositionMode, ShapeType, Point, StandardFonts, PageSize, Orientation, TextStatus, FontRecommendation,
    FontType
)
from .paragraph_builder import ParagraphBuilder

__version__ = "1.0.0"
__all__ = [
    "PDFDancer",
    "ParagraphBuilder",
    "ObjectRef",
    "Position",
    "ObjectType",
    "Font",
    "Color",
    "Image",
    "BoundingRect",
    "Paragraph",
    "FormFieldRef",
    "TextObjectRef",
    "PageRef",
    "PositionMode",
    "ShapeType",
    "Point",
    "StandardFonts",
    "PageSize",
    "Orientation",
    "TextStatus",
    "FontRecommendation",
    "FontType",
    "PdfDancerException",
    "FontNotFoundException",
    "ValidationException",
    "HttpClientException",
    "SessionException",
    "set_ssl_verify"
]

from .pdfdancer_v1 import PDFDancer
from . import pdfdancer_v1

def set_ssl_verify(enabled: bool) -> None:
    """
    Enable or disable SSL certificate verification for all API requests.

    Args:
        enabled: True to enable SSL verification (default, secure),
                False to disable SSL verification (only for testing with self-signed certs)

    WARNING: Disabling SSL verification should only be done in development/testing
    environments with self-signed certificates. Never disable in production.

    Example:
        import pdfdancer
        pdfdancer.set_ssl_verify(False)  # Disable SSL verification
    """
    pdfdancer_v1.DISABLE_SSL_VERIFY = not enabled

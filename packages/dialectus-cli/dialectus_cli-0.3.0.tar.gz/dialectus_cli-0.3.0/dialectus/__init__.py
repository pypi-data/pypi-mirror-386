"""Shared namespace package for Dialectus components."""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
__all__: list[str] = []

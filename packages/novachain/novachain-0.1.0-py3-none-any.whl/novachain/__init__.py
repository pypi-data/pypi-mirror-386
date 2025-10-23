# src/novachain/__init__.py
"""
NovaChain domain/services package.

Intentionally minimal to avoid circular imports:
- Do NOT import web/server modules here.
- Keep domain type exports optional and lightweight.
"""
__all__ = []  # keep empty; import concrete modules directly where needed

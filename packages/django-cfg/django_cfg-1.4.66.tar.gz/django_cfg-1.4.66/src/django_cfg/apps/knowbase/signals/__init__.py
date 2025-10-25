"""
Django signals for knowledge base events.

Decomposed into separate modules for better organization:
- document_signals: Document and DocumentChunk related signals
- archive_signals: Archive processing signals  
- chat_signals: Chat and messaging signals
"""

# Import all signal modules to ensure they are registered
from . import archive_signals, chat_signals, document_signals, external_data_signals

__all__ = [
    'document_signals',
    'archive_signals',
    'chat_signals',
    'external_data_signals',
]

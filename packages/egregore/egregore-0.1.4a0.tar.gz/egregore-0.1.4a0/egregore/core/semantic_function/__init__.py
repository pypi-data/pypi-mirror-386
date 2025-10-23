"""
Semantic Function Decorator - Transform Python functions into LLM-powered semantic functions.

This module provides the @semantic decorator that converts regular Python functions
with docstring templates into intelligent functions powered by Large Language Models.

Key Features:
- Template substitution in docstrings using {{parameter}} syntax
- Automatic type-aware response parsing based on return type annotations
- Support for multiple LLM providers (Anthropic, OpenAI, Google)
- Structured error handling with custom error handlers
- Workflow integration as nodes in Egregore workflows
- Automatic JSON schema generation for complex return types

Quick Start:
```python
from egregore.core.semantic_function import semantic

@semantic
def extract_sentiment(text: str) -> str:
    '''Analyze the sentiment of this text: {{text}}

    Return one of: positive, negative, neutral'''

result = extract_sentiment("I love this product!")
print(result)  # "positive"
```

For more examples and advanced usage, see the SemanticFunction class documentation.
"""

from .semantic import semantic, SemanticFunction

__all__ = ['semantic', 'SemanticFunction']

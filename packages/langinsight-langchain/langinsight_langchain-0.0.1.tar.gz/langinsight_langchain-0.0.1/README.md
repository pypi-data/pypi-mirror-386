# LangInsight LangChain Integration

LangChain integration for LangInsight observability platform.

## Installation

```bash
pip install langinsight-langchain
```

Or with Poetry:

```bash
poetry add langinsight-langchain
```

## Usage

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langinsight_langchain import CallbackHandler

# Create the LangInsight callback handler
handler = CallbackHandler(
    api_key="your-api-key",
    endpoint="https://api.langinsight.io",
    user_id="user-123",
    session_id="session-456",
)

# Create your chain with LangInsight handler
prompt = ChatPromptTemplate.from_messages(["Tell me a joke about {animal}"])

model = ChatAnthropic(
    model="claude-3-7-sonnet-20250219",
    callbacks=[handler],
)

chain = prompt | model
response = chain.invoke({"animal": "bears"})
```

### Environment Variables

You can also configure using environment variables:

```python
import os
from langinsight_langchain import CallbackHandler

handler = CallbackHandler(
    api_key=os.environ["LANGINSIGHT_API_KEY"],
    endpoint=os.environ.get("LANGINSIGHT_ENDPOINT", "https://api.langinsight.io"),
    user_id="user-123",
    session_id="session-456",
)
```

## Development

```bash
# Install dependencies
poetry install

# Run example
poetry run python examples/basic_usage.py
```

## License

MIT


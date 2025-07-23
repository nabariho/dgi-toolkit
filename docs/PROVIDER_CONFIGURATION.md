# LLM Provider Configuration

The DGI Toolkit supports multiple LLM providers through a flexible, configurable abstraction layer. This allows you to easily switch between OpenAI, Anthropic, and future providers based on your needs, budget, and preferences.

## 🚀 **Quick Start**

### Environment Configuration (Recommended)

Set your preferred provider and API key:

```bash
# Use OpenAI (default)
export OPENAI_API_KEY="sk-your-openai-key"
export DGI_LLM_PROVIDER="openai"
export DGI_LLM_MODEL="gpt-4o-mini"

# Or use Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"  
export DGI_LLM_PROVIDER="anthropic"
export DGI_LLM_MODEL="claude-3-5-haiku-20241022"
```

Then run the chat demo:
```bash
poetry run python ai_chat/chat_demo.py
```

### Programmatic Configuration

```python
from dgi.providers import create_provider

# Create OpenAI provider
openai_provider = create_provider(
    "openai",
    model="gpt-4o-mini",
    api_key="your-key",
    temperature=0.1
)

# Create Anthropic provider  
anthropic_provider = create_provider(
    "anthropic",
    model="claude-3-5-sonnet-20241022",
    api_key="your-key",
    temperature=0.2
)

# Use provider to create agent
agent = provider.create_agent([screen_dividends])
```

## 📋 **Supported Providers**

### OpenAI

**Default Model**: `gpt-4o-mini`  
**API Key**: `OPENAI_API_KEY`  
**Capabilities**: Function calling, streaming, vision (gpt-4o)

**Recommended Models**:
- `gpt-4o-mini` - Low cost, fast, excellent for screening
- `gpt-4o` - Premium quality, vision support  
- `gpt-4-turbo` - High performance, large context

**Example Configuration**:
```python
provider = create_provider(
    "openai",
    model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=1000,
    timeout=30
)
```

### Anthropic (Claude)

**Default Model**: `claude-3-5-sonnet-20241022`  
**API Key**: `ANTHROPIC_API_KEY`  
**Capabilities**: Function calling, streaming, vision, large context

**Recommended Models**:
- `claude-3-5-haiku-20241022` - Low cost, fast responses
- `claude-3-5-sonnet-20241022` - Best balance of performance/cost
- `claude-3-opus-20240229` - Premium quality, complex reasoning

**Example Configuration**:
```python
provider = create_provider(
    "anthropic", 
    model="claude-3-5-haiku-20241022",
    temperature=0.1,
    max_tokens=2000
)
```

## ⚙️ **Configuration Options**

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DGI_LLM_PROVIDER` | `"openai"` | Provider type (`openai`, `anthropic`) |
| `DGI_LLM_MODEL` | Provider default | Specific model to use |
| `OPENAI_API_KEY` | None | OpenAI API key |
| `ANTHROPIC_API_KEY` | None | Anthropic API key |

### LLMConfig Parameters

```python
@dataclass
class LLMConfig:
    provider: ProviderType          # Provider type
    model: str                      # Model name
    api_key: Optional[str] = None   # API key (or from env)
    temperature: float = 0.1        # Response randomness (0.0-1.0)
    max_tokens: Optional[int] = None # Max response length
    timeout: int = 30               # Request timeout (seconds)
    max_retries: int = 2            # Retry attempts
    extra_params: Dict[str, Any] = None # Provider-specific params
```

## 💰 **Cost Optimization**

### Model Selection by Use Case

**High-Volume Screening** (Cost-Optimized):
```python
# OpenAI - Lowest cost
provider = create_provider("openai", model="gpt-4o-mini")

# Anthropic - Low cost alternative  
provider = create_provider("anthropic", model="claude-3-5-haiku-20241022")
```

**Complex Analysis** (Quality-Optimized):
```python
# OpenAI - Premium quality
provider = create_provider("openai", model="gpt-4o")

# Anthropic - Premium reasoning
provider = create_provider("anthropic", model="claude-3-opus-20240229")
```

**Balanced Performance**:
```python
# OpenAI - Good balance
provider = create_provider("openai", model="gpt-4-turbo")

# Anthropic - Best balance
provider = create_provider("anthropic", model="claude-3-5-sonnet-20241022")
```

### Cost Comparison (Approximate)

| Provider | Model | Cost Tier | Input/Output | Use Case |
|----------|-------|-----------|--------------|----------|
| OpenAI | gpt-4o-mini | Low | $0.15/$0.60 per 1M tokens | High-volume screening |
| Anthropic | claude-3-5-haiku | Low | $0.25/$1.25 per 1M tokens | Fast responses |
| OpenAI | gpt-4-turbo | Standard | $10/$30 per 1M tokens | Balanced performance |
| Anthropic | claude-3-5-sonnet | Standard | $3/$15 per 1M tokens | Best value |
| OpenAI | gpt-4o | Premium | $5/$15 per 1M tokens | Premium quality |
| Anthropic | claude-3-opus | Premium | $15/$75 per 1M tokens | Complex reasoning |

## 🔧 **Advanced Configuration**

### Custom Provider Factory

```python
from dgi.providers import create_provider_from_env

# Create with environment variables + overrides
provider = create_provider_from_env(
    temperature=0.2,  # Override default
    max_tokens=1500,  # Custom limit
    extra_params={    # Provider-specific settings
        "top_p": 0.9,
        "presence_penalty": 0.1
    }
)
```

### Multiple Providers in Application

```python
from dgi.providers import create_provider

class DGIMultiProvider:
    def __init__(self):
        # Fast provider for basic screening
        self.fast_provider = create_provider(
            "openai", 
            model="gpt-4o-mini",
            temperature=0.0
        )
        
        # Premium provider for complex analysis
        self.premium_provider = create_provider(
            "anthropic",
            model="claude-3-5-sonnet-20241022", 
            temperature=0.1
        )
    
    def quick_screen(self, query):
        agent = self.fast_provider.create_agent([screen_dividends])
        return agent.run(query)
    
    def detailed_analysis(self, query):
        agent = self.premium_provider.create_agent([screen_dividends])
        return agent.run(query)
```

### Provider Information

```python
from dgi.providers import get_available_providers

# Get all provider capabilities
providers = get_available_providers()

for name, info in providers.items():
    print(f"{name}:")
    print(f"  Default: {info['default_model']}")
    print(f"  API Key: {info['api_key_env']}")  
    print(f"  Models: {info['supported_models']}")
    print(f"  Capabilities: {info['capabilities']}")
```

## 🔍 **Troubleshooting**

### Common Issues

**❌ ImportError: cannot import 'ChatAnthropic'**
```bash
poetry add langchain-anthropic
```

**❌ Missing API Key Error**
```bash
# Check your environment
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Set missing key
export OPENAI_API_KEY="your-key-here"
```

**❌ Unsupported Provider**
```python
# Check available providers
from dgi.providers import get_available_providers
print(get_available_providers().keys())
```

### Debugging Provider Configuration

```python
# Check current provider setup
provider = create_provider_from_env()
print("Provider config:", provider.get_config_summary())
print("Model info:", provider.get_model_info())
print("API key valid:", provider.validate_api_key())
```

### Chat Demo Provider Information

Type `config` or `providers` in the chat demo to see current configuration:

```
🤖 Ask about dividend stocks (or 'quit' to exit): config

🔧 Provider Configuration
------------------------------
Current Provider: openai
Current Model: gpt-4o-mini

📋 Available Providers:
  ✅ OPENAI
     Default: gpt-4o-mini
     API Key: OPENAI_API_KEY
     Models: gpt-4o, gpt-4o-mini, gpt-4-turbo...

  ❌ ANTHROPIC  
     Default: claude-3-5-sonnet-20241022
     API Key: ANTHROPIC_API_KEY
     Models: claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022...
```

## 🚀 **Future Providers**

The provider abstraction is designed to easily support additional providers:

- **Azure OpenAI**: Enterprise-grade OpenAI deployment
- **Google PaLM/Gemini**: Google's LLM offerings  
- **Cohere**: Specialized for business applications
- **Local Models**: Ollama, LM Studio, etc.

Each new provider only requires implementing the `LLMProvider` interface:

```python
class NewProvider(LLMProvider):
    def _initialize_client(self) -> Any: ...
    def create_agent(self, tools: List[Any], **kwargs) -> Any: ...
    def validate_api_key(self) -> bool: ...
    def get_model_info(self) -> Dict[str, Any]: ...
```

## 📊 **Best Practices**

1. **Start with defaults**: Use `gpt-4o-mini` or `claude-3-5-haiku` for development
2. **Environment configuration**: Use environment variables for production
3. **Cost monitoring**: Track token usage for budget management
4. **Model selection**: Match model capability to task complexity
5. **Error handling**: Always validate API keys before creating agents
6. **Provider comparison**: Test both providers to find your preference

---

**Need help?** Check the chat demo's `config` command or run the provider tests to verify your setup. 
# Auto-Agentic

A modular, scalable Python package for creating conversational AI assistants that can interpret natural language queries, generate SQL queries via LLM, execute them on configured databases, and return insights in natural language.

## Features

- **Natural Language to SQL**: Convert plain English queries into SQL using LLM
- **Safe Query Execution**: Built-in safety checks to prevent destructive operations
- **Multiple Database Support**: Currently supports SQLite (extensible design)
- **Multiple LLM Providers**: Currently supports OpenAI (extensible design)
- **Conversation Memory**: Persistent or in-memory conversation history
- **Intent Classification**: Automatically handles greetings, data queries, and follow-ups
- **Modular Architecture**: Easy to extend with new providers and backends

## Installation

```bash
pip install auto-agentic
```

## Quick Start

### Basic Usage

```python
from auto_agentic import Agent

# Initialize agent (auto-configures from .env file)
agent = Agent()

# Query your database in natural language
response = agent.invoke("Show me the top 5 customers by total revenue")
print(response)
```

### Configuration

Create a `.env` file in your project directory:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
LLM_PROVIDER=openai
DATABASE_TYPE=sqlite
DB_PATH=your_database.db
MEMORY_TYPE=sqlite
PERSIST_MEMORY=True
MODEL=gpt-4o-mini
```

### Advanced Usage

```python
from auto_agentic import Agent

# Override configuration parameters
agent = Agent(
    openai_api_key="sk-your-key",
    db_path="custom_database.db",
    memory_type="in_memory",  # Use in-memory storage
    model="gpt-4"
)

# Use with session management
session_id = "user-123"
response = agent.invoke("What were the sales last month?", session_id=session_id)

# Follow-up questions maintain context
follow_up = agent.invoke("Can you break that down by product category?", session_id=session_id)
```

## Configuration Options

| Parameter | Environment Variable | Default | Description |
|-----------|-------------------|---------|-------------|
| `openai_api_key` | `OPENAI_API_KEY` | Required | OpenAI API key |
| `llm_provider` | `LLM_PROVIDER` | `openai` | LLM provider (currently only `openai`) |
| `database_type` | `DATABASE_TYPE` | `sqlite` | Database type (currently only `sqlite`) |
| `db_path` | `DB_PATH` | `system.db` | Path to SQLite database file |
| `memory_type` | `MEMORY_TYPE` | `sqlite` | Memory backend (`sqlite` or `in_memory`) |
| `persist_memory` | `PERSIST_MEMORY` | `True` | Whether to persist conversation history |
| `model` | `MODEL` | `gpt-4o-mini` | OpenAI model to use |

## Architecture

Auto-Agentic is designed with extensibility in mind:

### Core Components

- **Agent**: Main entry point that orchestrates all components
- **LLM Providers**: Abstract interface for different LLM services
- **Database Backends**: Abstract interface for different database systems
- **Memory Backends**: Abstract interface for conversation storage

### Current Implementations

- **LLM Provider**: OpenAI (GPT models)
- **Database Backend**: SQLite
- **Memory Backends**: SQLite (persistent) and In-Memory (temporary)

### Extensibility

The modular design allows easy addition of:
- New LLM providers (Anthropic, Gemini, Ollama, etc.)
- New database backends (PostgreSQL, MySQL, etc.)
- New memory backends (Redis, vector stores, etc.)

## Safety Features

- **SQL Safety Checks**: Automatically blocks destructive operations (DROP, DELETE, UPDATE, etc.)
- **Query Validation**: Prevents SQL injection and comment-based attacks
- **Error Handling**: Graceful error handling with meaningful messages

## Conversation Memory

Auto-Agentic maintains conversation context through two memory modes:

### Persistent Mode (SQLite)
- Conversations saved to SQLite database
- Automatic table creation (`conversation_history`)
- Session-based conversation tracking
- Survives application restarts

### In-Memory Mode
- Temporary conversation storage
- Faster for stateless applications
- Lost on application restart

## Example Use Cases

### Business Intelligence
```python
agent = Agent()

# Sales analysis
response = agent.invoke("Show me monthly sales trends for the last 6 months")
response = agent.invoke("Which products are performing best?")
response = agent.invoke("Compare this quarter to last quarter")
```

### Customer Analytics
```python
agent = Agent()

# Customer insights
response = agent.invoke("Find customers who haven't purchased in 90 days")
response = agent.invoke("What's the average order value by customer segment?")
response = agent.invoke("Show me customer lifetime value trends")
```

### Data Exploration
```python
agent = Agent()

# Explore your data
response = agent.invoke("What tables are available in this database?")
response = agent.invoke("Show me a sample of the customer data")
response = agent.invoke("What are the data types in the orders table?")
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/auto-agentic/auto-agentic.git
cd auto-agentic
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
flake8 src/
mypy src/
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Adding New Providers

To add a new LLM provider:

1. Create a new class inheriting from `LLMProvider`
2. Implement all abstract methods
3. Add provider selection logic in `Agent._init_llm_provider()`
4. Update configuration validation

To add a new database backend:

1. Create a new class inheriting from `DatabaseBackend`
2. Implement all abstract methods
3. Add backend selection logic in `Agent._init_database_backend()`
4. Update configuration validation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Support for PostgreSQL and MySQL databases
- [ ] Integration with Anthropic Claude and Google Gemini
- [ ] Vector database memory backends
- [ ] Advanced query optimization
- [ ] Multi-language support
- [ ] Web interface
- [ ] API server mode

## Support

- 📖 [Documentation](https://auto-agentic.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/auto-agentic/auto-agentic/issues)
- 💬 [Discussions](https://github.com/auto-agentic/auto-agentic/discussions)

## Changelog

### v0.1.0 (2024-01-XX)
- Initial release
- OpenAI LLM provider support
- SQLite database backend
- SQLite and in-memory memory backends
- Basic safety features
- Configuration management

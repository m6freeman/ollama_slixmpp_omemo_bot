
# Ollama Slixmpp Bot with OMEMO

A basic echo-bot built with slixmpp and slixmpp-omemo that relays your messages to a locally running ollama server.

## Dependancies

- [ollama 0.1.14](https://ollama.com/download/linux)
- [LLM](https://ollama.com/library)
    - [llama3](https://ollama.com/library/llama3)

## Installation

```bash
git clone --bare https://github.com/user/repo_name
cd repo_name; git worktree add main; cd main
python -m venv .venv; ./.venv/bin/activate
pip install -r requirements.txt
# There is a httpx dependancy conflict. These must be installed in this order.
pip install ollama; pip install ollama-python
```

## Usage

First Terminal instance
```bash
ollama serve
```

Second Terminal instance
```bash
./ollama_slixmpp_omemo_bot/src/ollama_slixmpp_omemo_bot/ $ PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python main.py
# Enter JID: service-account@example-server.im
# Enter Password: 
```

With OMEMO and Blind Trust enabled, message service-account@example-server.im from another account.

Recommended and tested clients:
- Conversations
- Profanity

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.

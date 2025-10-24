# Alithia

[![PyPI version](https://img.shields.io/pypi/v/alithia.svg)](https://pypi.org/project/alithia/)


Time is one of the most valuable resources for a human researcher, best spent
on thinking, exploring, and creating in the world of ideas. With Alithia, we
aim to open a new frontier in research assistance. Alithia aspires to be your
powerful research companion: from reading papers to pursuing interest-driven
deep investigations, from reproducing experiments to detecting fabricated
results, from tracking down relevant papers to monitoring industrial
breakthroughs. At its core, Alithia forges a strong and instant link between your personal
research profile, the latest state-of-the-art developments, and pervasive cloud
resources, ensuring you stay informed, empowered, and ahead.

## Features

In Alithia, we connect each researcher’s profile with publicly available academic resources, leveraging widely accessible cloud infrastructure to automate the entire process. In its current version, Alithia is designed to support the following features:

* Reseacher Profile
  * Basic profile: research interests, expertise, language
  * Connected (personal) services:
    * LLM (OpenAI compatible)
    * Zotero library
    * Email notification
    * Github profile
    * Google scholar profile
    * X account message stream
  * Gems (general research digest or ideas)
* Academic Resources
  * arXiv papers
  * Google scholar search
  * Web search engines (e.g., tavily)
  * Individual researcher homepage

## Quick Start

### 1. Setup Arxrec Agent

The Arxrec Agent delivers daily paper recommendations from arXiv to your inbox.

**Prerequisites:**
1. **Zotero Account**: [Sign up](https://www.zotero.org) and get your user ID and API key from Settings → Feeds/API
2. **OpenAI API Key**: From any OpenAI-compatible LLM provider
3. **Email (Gmail)**: Enable 2FA and generate an App Password

**GitHub Actions Setup:**
1. Fork this repository
2. Go to Settings → Secrets and variables → Actions
3. Add secret `ALITHIA_CONFIG_JSON` with your configuration (see below)
4. Agent runs automatically daily at 01:00 UTC

### 2. Configuration

Create a JSON configuration with your credentials:

```json
{
  "zotero_id": "YOUR_ZOTERO_USER_ID",
  "zotero_key": "YOUR_ZOTERO_API_KEY",
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "openai_api_base": "https://api.openai.com/v1",
  "model_name": "gpt-5",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender": "your-email@gmail.com",
  "sender_password": "YOUR_APP_PASSWORD",
  "receiver": "recipient@example.com",
  "max_paper_num": 10,
  "arxiv_query": "cs.AI+cs.CV"
}
```

See [alithia_config_example.json](alithia_config_example.json) for a complete example.

**Configuration Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `zotero_id` | ✅ | Your Zotero user ID |
| `zotero_key` | ✅ | Your Zotero API key |
| `openai_api_key` | ✅ | OpenAI API key for summaries |
| `smtp_server` | ✅ | Email SMTP server |
| `smtp_port` | ✅ | SMTP port (587 for Gmail) |
| `sender` | ✅ | Sender email address |
| `sender_password` | ✅ | Email app password |
| `receiver` | ✅ | Recipient email address |
| `openai_api_base` | ❌ | Custom API base URL |
| `max_paper_num` | ❌ | Max papers per email (default: 10) |
| `arxiv_query` | ❌ | ArXiv categories (e.g., "cs.AI+cs.CV") |
| `debug` | ❌ | Enable debug mode |

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

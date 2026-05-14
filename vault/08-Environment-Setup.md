# Environment Setup

## Quick Start (Docker)

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your keys

# Start services
docker-compose up --build

# App runs on http://localhost:8000
# Redis runs on localhost:6379
```

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `TWILIO_ACCOUNT_SID` | Yes | — | Twilio account ID |
| `TWILIO_AUTH_TOKEN` | Yes | — | Twilio auth token |
| `TWILIO_WHATSAPP_NUMBER` | Yes | — | Twilio WhatsApp sender number |
| `MIMO_API_KEY` | Yes | — | MiMo API key |
| `MIMO_API_BASE_URL` | No | `https://api.mimo.ai/v1` | MiMo API endpoint |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection URL |
| `SUPPORTED_LANGUAGES` | No | `["en","hi","bn","or","ta","te","kn","ml"]` | Language codes |

## Docker Setup

### docker-compose.yml
- **redis:** `redis:7-alpine` on port 6379 with healthcheck
- **app:** Built from Dockerfile, port 8000, depends on Redis

### Dockerfile
- Base: `python:3.12-slim`
- Installs `ffmpeg` for audio conversion
- Runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## MiMo API Setup

1. Get API key from MiMo Orbit grant
2. Set `MIMO_API_KEY` in `.env`
3. Base URL: `https://token-plan-sgp.xiaomimimo.com/v1`

## Twilio Sandbox Setup

1. Create Twilio account
2. Join WhatsApp sandbox (send code to sandbox number)
3. Set webhook URL to `https://your-domain/webhook`
4. For local dev: use ngrok (`ngrok http 8000`)

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_language.py -v

# With coverage
pytest tests/ --cov=app
```

## Health Check

```bash
curl http://localhost:8000/health
# Returns: {"status": "ok"}
```

## Related Notes

- [[03-Tech-Stack]] — What technologies are used
- [[11-Known-Issues]] — Production deployment considerations
- [[02-Architecture]] — How the system is structured

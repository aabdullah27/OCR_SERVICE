# OCR Service

Stateless OCR microservice that converts document images to Markdown, HTML, or JSON.

## Features

- Dual backend: HuggingFace Transformers (CPU/GPU) or vLLM (GPU, high-performance)
- Output formats: Markdown, HTML, JSON
- Async processing with batch support
- Simple API key authentication (optional)

## Quick Start

```bash
# Install dependencies
uv sync

# Run (uses Transformers backend by default)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

First run downloads the model (~6GB).

## Configuration

Environment variables (prefix `OCR_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_DOLPHIN_BACKEND` | `transformers` | Backend: `transformers` or `vllm` |
| `OCR_DOLPHIN_MODEL` | `ByteDance/Dolphin-v2` | Model name/path |
| `OCR_DOLPHIN_VLLM_URL` | `http://localhost:8000/v1` | vLLM endpoint (if using vllm backend) |
| `OCR_REQUEST_TIMEOUT` | `300` | Request timeout (seconds) |
| `OCR_API_KEY` | `None` | API key for auth (optional) |

### Using vLLM Backend (GPU, faster)

```bash
# Terminal 1: Start vLLM
uv run vllm serve ByteDance/Dolphin-v2 --port 8000 --trust-remote-code

# Terminal 2: Start service
OCR_DOLPHIN_BACKEND=vllm uv run uvicorn app.main:app --port 8080
```

## API Endpoints

### Process Single Image

**POST** `/api/v1/ocr`

```json
{
  "image": "<base64-encoded-image>",
  "format": "markdown"
}
```

Response:
```json
{
  "content": "# Document Title\n\nExtracted text...",
  "format": "markdown",
  "engine": "dolphin",
  "processing_time_ms": 1234
}
```

### Upload Image File

**POST** `/api/v1/ocr/upload`

```bash
curl -X POST http://localhost:8080/api/v1/ocr/upload \
  -F "file=@document.png" \
  -F "format=markdown"
```

### Batch Processing

**POST** `/api/v1/ocr/batch`

```json
{
  "images": ["<base64>", "<base64>"],
  "format": "markdown"
}
```

### Health Check

- `GET /api/v1/health` - Basic health
- `GET /api/v1/ready` - Readiness (engine loaded)

## Project Structure

```
app/
├── main.py
├── core/
│   ├── config.py
│   └── exceptions.py
├── api/v1/
│   ├── deps.py
│   ├── schemas/
│   └── routes/
├── engines/
│   ├── base.py
│   ├── registry.py
│   └── dolphin/
│       ├── engine.py
│       ├── backends/
│       │   ├── transformers.py
│       │   └── vllm.py
│       ├── prompts.py
│       └── utils.py
└── services/
    └── ocr_service.py
```

## Adding New Engines

1. Create `app/engines/<name>/engine.py`
2. Extend `OCREngine` base class
3. Register with `@EngineRegistry.register("<name>")`
4. Import in `app/main.py`

## License

MIT

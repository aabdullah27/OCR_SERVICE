# OCR Service

Stateless OCR microservice that converts document images to Markdown, HTML, or JSON. Designed for multi-model support with vLLM serving.

## Features

- Multiple OCR engines (Dolphin, more coming)
- Output formats: Markdown, HTML, JSON
- Async processing with vLLM backend
- Batch processing support
- Simple API key authentication (optional)

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start vLLM server with Dolphin model

```bash
vllm serve ByteDance/Dolphin-v2 --port 8000
```

### 3. Run the service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Configuration

Environment variables (prefix: `OCR_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_DEFAULT_ENGINE` | `dolphin` | Default OCR engine |
| `OCR_DOLPHIN_VLLM_URL` | `http://localhost:8000/v1` | Dolphin vLLM endpoint |
| `OCR_DOLPHIN_MODEL_NAME` | `ByteDance/Dolphin-v2` | Model name in vLLM |
| `OCR_MAX_BATCH_SIZE` | `8` | Max batch size |
| `OCR_REQUEST_TIMEOUT` | `120` | Request timeout (seconds) |
| `OCR_API_KEY` | `None` | API key for auth (optional) |

## API Endpoints

### Process Single Image

**POST** `/api/v1/ocr`

```json
{
  "image": "<base64-encoded-image>",
  "engine": "dolphin",
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

- `file`: Image file (multipart)
- `engine`: OCR engine (optional)
- `format`: Output format (optional)

### Batch Processing

**POST** `/api/v1/ocr/batch`

```json
{
  "images": ["<base64>", "<base64>"],
  "engine": "dolphin",
  "format": "markdown"
}
```

### Health Check

- **GET** `/api/v1/health` - Basic health
- **GET** `/api/v1/ready` - Readiness (engines loaded)

## Project Structure

```
app/
├── main.py                 # FastAPI app
├── core/
│   ├── config.py           # Settings
│   └── exceptions.py       # Custom exceptions
├── api/v1/
│   ├── router.py           # Route aggregator
│   ├── deps.py             # Dependencies
│   ├── schemas/            # Request/Response models
│   └── routes/             # Endpoint handlers
├── engines/
│   ├── base.py             # OCREngine ABC
│   ├── registry.py         # Engine registry
│   └── dolphin/            # Dolphin implementation
└── services/
    └── ocr_service.py      # Business logic
```

## Adding New Engines

1. Create folder: `app/engines/<name>/`
2. Implement engine extending `OCREngine`
3. Register with `@EngineRegistry.register("<name>")`
4. Import in `app/main.py` to register

## License

MIT

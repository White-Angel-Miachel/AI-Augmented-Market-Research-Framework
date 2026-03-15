# AI-Augmented Market Research Framework

An LLM-powered research pipeline that automates startup sector analysis and generates structured investment pitch briefs.

## Features

- **Automated Report Processing**: Parse industry reports in PDF, DOCX, and TXT formats
- **Investment Signal Extraction**: Extract market size, trends, competitive landscape, and opportunities using LLMs
- **Sector Classification**: Automatically categorize reports by industry vertical
- **Pitch Brief Generation**: Create structured investment briefs from extracted signals
- **Excel Export**: Output analysis results in Excel format for easy review

## Quick Start

### 1. Clone and Setup Environment

```bash
# Navigate to project directory
cd "AI-Augmented Market Research Framework"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Open your `.env` file and add your required keys. The framework currently relies on NVIDIA NIM API for accessing state-of-the-art models like Minimax or Qwen:

```
# Get your token from: https://build.nvidia.com
NVIDIA_API_KEY=nvapi-your-token-here

# Optional: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
```

⚠️ **Do not commit your `.env` file to version control. It is already included in `.gitignore` by default to protect your APIs from going public.**

### 3. Add Industry Reports

Place your industry reports in the `data/reports/` directory. Supported formats:
- PDF (`.pdf`)
- Word documents (`.docx`)
- Plain text (`.txt`)

A sample report is included for testing.

### 4. Run the Interface (Recommended)

The easiest way to use the framework is through the drag-and-drop web UI:

```bash
python app.py
```
Then open `http://localhost:5000` in your web browser.

### 5. Or Run via Command Line

```bash
python src/pipeline.py
```

## Project Structure

```
AI-Augmented Market Research Framework/
├── config/
│   ├── __init__.py
│   └── prompts.py          # LLM prompt templates
├── data/
│   └── reports/            # Input industry reports
├── output/                 # Generated analysis files
├── src/
│   ├── __init__.py
│   ├── pipeline.py         # Main orchestration
│   ├── report_parser.py    # Document parsing
│   └── pitch_generator.py  # Brief generation
├── static/                 # Web UI assets
├── templates/              # Web UI HTML
├── app.py                  # Flask Web Interface
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
└── README.md
```

## Usage Examples

### Process a Single Report

```python
from src.pipeline import MarketResearchPipeline

pipeline = MarketResearchPipeline(use_api=True)
result = pipeline.process_report("data/reports/my_report.pdf")
print(result['pitch_brief'])
```

### Batch Process All Reports

```python
from src.pipeline import MarketResearchPipeline

pipeline = MarketResearchPipeline()
results = pipeline.process_batch("data/reports/", output_excel=True)
# Results saved to output/analysis_YYYYMMDD_HHMMSS.xlsx
```

### Customize Prompts

Edit `config/prompts.py` to modify:
- Investment signal extraction criteria
- Pitch brief structure
- Sector classification categories

## Supported Models

Currently default: `minimaxai/minimax-m2.5` (via Nvidia NIM API Integration)

Because the pipeline uses the OpenAI-compatible client under the hood, you can easily swap out the model and integration URL.

Other supported options via Nvidia build API:
- `qwen/qwen3.5-122b-a10b`
- `meta/llama3-70b-instruct`

To change model, simply edit `src/pipeline.py` or modify the pipeline instantiation dynamically:

```python
pipeline = MarketResearchPipeline(
    model_name="qwen/qwen3.5-122b-a10b"
)
```

## Output Format

### JSON Output
```json
{
  "source_file": "report.pdf",
  "sector": "AI/ML Infrastructure",
  "signals": {
    "market_size": "$42.5B",
    "cagr": "28.3%",
    "key_trends": ["Model efficiency", "Edge deployment"],
    "signal_strength": 8
  },
  "pitch_brief": "...",
  "processed_at": "2024-01-15T10:30:00"
}
```

### Excel Output
| Source File | Sector | Signal Strength | Pitch Brief | Processed At |
|-------------|--------|-----------------|-------------|--------------|
| report.pdf  | AI/ML  | 8               | ...         | 2024-01-15   |

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NVIDIA_API_KEY` | Key for Nvidia NIM Platform (Minimax/Qwen) | Yes |
| `GEMINI_API_KEY` | Key for fallback to Gemini models | No |
| `OPENROUTER_API_KEY` | Key for alternative OpenAI-compatible endpoints | No |

## Troubleshooting

### "Missing Authentication Header" error
- Ensure you have un-commented or pasted your API key into your `.env` file correctly, removing any `Bearer ` text beforehand.

### PDF parsing issues
- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Some scanned PDFs may require OCR preprocessing

### Memory errors with local inference
- Use API mode (`use_api=True`)
- Or try a smaller model

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - feel free to use for personal and commercial projects.

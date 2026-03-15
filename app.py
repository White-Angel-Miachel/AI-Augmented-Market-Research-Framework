"""
Flask Web Application for AI-Augmented Market Research Pipeline
Provides a drag-and-drop UI for uploading industry reports and viewing analysis results.
"""

import os
import json
import traceback
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

# Fix imports for running from project root
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import MarketResearchPipeline

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "data" / "reports"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_and_process():
    """Handle file upload and run the analysis pipeline."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'Unsupported file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        # Save uploaded file
        filename = file.filename
        save_path = UPLOAD_DIR / filename
        file.save(str(save_path))

        # Initialize and run pipeline
        pipeline = MarketResearchPipeline(
            model_name="gemini-2.5-flash",
            use_api=True
        )

        result = pipeline.process_report(str(save_path))

        # Save results (same as batch but for single report)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(filename).stem

        # Save Markdown
        md_path = pipeline._save_markdown_report(result, timestamp)

        # Save DOCX
        if md_path:
            pipeline._save_docx_report(md_path, timestamp)

        # Save JSON
        json_filename = f"analysis_{timestamp}.json"
        json_path = OUTPUT_DIR / json_filename
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([result], f, indent=2, ensure_ascii=False)

        # Build output file list
        output_files = []
        md_name = f"{source_name}_analysis_{timestamp}.md"
        docx_name = f"{source_name}_analysis_{timestamp}.docx"

        if (OUTPUT_DIR / md_name).exists():
            output_files.append({'name': md_name, 'type': 'Markdown', 'icon': 'doc'})
        if (OUTPUT_DIR / docx_name).exists():
            output_files.append({'name': docx_name, 'type': 'Word Document', 'icon': 'docx'})
        if json_path.exists():
            output_files.append({'name': json_filename, 'type': 'JSON Data', 'icon': 'json'})

        # Read the markdown for preview
        preview = ""
        if md_path and Path(md_path).exists():
            with open(md_path, 'r', encoding='utf-8') as f:
                preview = f.read()

        return jsonify({
            'success': True,
            'sector': result.get('sector', 'Unknown'),
            'signal_strength': result.get('signals', {}).get('Signal Strength', {}).get('Rating',
                              result.get('signals', {}).get('signal_strength', 'N/A')),
            'files': output_files,
            'preview': preview,
            'processed_at': result.get('processed_at', '')
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Serve output files for download."""
    return send_from_directory(str(OUTPUT_DIR), filename, as_attachment=True)


@app.route('/results')
def list_results():
    """List all previous analysis results."""
    results = []
    for f in sorted(OUTPUT_DIR.glob("*_analysis_*.md"), reverse=True):
        stem = f.stem
        timestamp_part = stem.split('_analysis_')[-1] if '_analysis_' in stem else ''
        report_name = stem.split('_analysis_')[0] if '_analysis_' in stem else stem

        # Find matching files
        files = []
        for ext in ['md', 'docx']:
            match = OUTPUT_DIR / f"{report_name}_analysis_{timestamp_part}.{ext}"
            if match.exists():
                files.append({'name': match.name, 'type': ext.upper()})

        # Check for JSON
        json_match = OUTPUT_DIR / f"analysis_{timestamp_part}.json"
        if json_match.exists():
            files.append({'name': json_match.name, 'type': 'JSON'})

        results.append({
            'report_name': report_name.replace('-', ' ').replace('_', ' ').title(),
            'timestamp': timestamp_part,
            'files': files
        })

    return jsonify(results)


if __name__ == '__main__':
    print("\n=== AI Market Research Pipeline ===")
    print("Open http://localhost:5000 in your browser")
    print("===================================\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

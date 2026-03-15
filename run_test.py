"""Quick test script for the pipeline"""
import sys
from pathlib import Path
from src.pipeline import MarketResearchPipeline

# Force flush prints
def log(msg):
    print(msg)
    sys.stdout.flush()

# Check reports directory
reports_dir = Path('data/reports')
log(f'Reports directory exists: {reports_dir.exists()}')
log(f'Reports found: {list(reports_dir.glob("*"))}')

# Initialize pipeline
log('\nInitializing pipeline...')
try:
    pipeline = MarketResearchPipeline(use_api=True)
    log('Pipeline ready!')
except Exception as e:
    log(f'Error initializing pipeline: {e}')
    sys.exit(1)

# Process reports
log('\nProcessing reports...')
try:
    results = pipeline.process_batch(str(reports_dir))
    log(f'\nDone! Processed {len(results)} reports')
except Exception as e:
    log(f'Error processing: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Show results
for r in results:
    log(f"\n{'='*50}")
    log(f"File: {r.get('source_file', 'N/A')}")
    log(f"Sector: {r.get('sector', 'N/A')}")
    if 'pitch_brief' in r:
        log(f"\nPitch Brief:\n{r['pitch_brief'][:500]}...")

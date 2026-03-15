"""
AI-Augmented Market Research Pipeline
Main orchestration script for processing industry reports and generating pitch briefs
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import OpenAI
from tqdm import tqdm
import pandas as pd

# Local imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.prompts import (
    INVESTMENT_SIGNAL_SYSTEM,
    EXTRACT_INSIGHTS_PROMPT,
    PITCH_BRIEF_PROMPT,
    SECTOR_CLASSIFICATION_PROMPT,
    SUMMARIZE_REPORT_PROMPT
)
from src.report_parser import ReportParser
from src.pitch_generator import PitchBriefGenerator
from src.docx_exporter import DocxExporter

load_dotenv()


class MarketResearchPipeline:
    """
    Main pipeline for AI-augmented market research analysis.
    Processes industry reports and generates structured investment briefs.
    """
    
    def __init__(
        self,
        model_name: str = "minimaxai/minimax-m2.5",
        use_api: bool = True,
        api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the research pipeline.
        
        Args:
            model_name: Model identifier (defaults to minimaxai/minimax-m2.5)
            use_api: If True, use API; else load model locally
            api_key: Gemini API token (optional)
            openai_api_key: NVIDIA/OpenRouter API token (optional)
        """
        self.model_name = model_name
        self.use_api = use_api
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("NVIDIA_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key and self.openai_api_key.startswith("Bearer "):
            self.openai_api_key = self.openai_api_key[7:]
        
        # Determine API provider based on model name
        self.provider = "gemini" if "gemini" in model_name.lower() else "openai"
        
        # Initialize components
        self.report_parser = ReportParser()
        self.pitch_generator = PitchBriefGenerator()
        
        # Set up LLM
        self._setup_llm()
        
        # Output directory
        self.output_dir = Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def _setup_llm(self):
        """Initialize the LLM client."""
        if self.use_api:
            if self.provider == "gemini":
                if not self.api_key:
                    raise ValueError(
                        "GEMINI_API_KEY required for API mode. "
                        "Set it in .env file or pass api_key parameter."
                    )
                self.client = genai.Client(api_key=self.api_key)
                print(f"OK Initialized Gemini API with model: {self.model_name}")
            else:
                if not self.openai_api_key:
                    raise ValueError(
                        "NVIDIA_API_KEY, OPENROUTER_API_KEY or OPENAI_API_KEY required for OpenAI-compatible model. "
                        "Set it in .env file or pass openai_api_key parameter."
                    )
                # Determine base URL
                if "nvidia" in self.model_name.lower() or "meta" in self.model_name.lower() or "qwen" in self.model_name.lower() or "mistral" in self.model_name.lower() or "minimax" in self.model_name.lower():
                    # Likely from build.nvidia.com
                    base_url = "https://integrate.api.nvidia.com/v1"
                elif "/" in self.model_name:
                    base_url = "https://openrouter.ai/api/v1"
                else: 
                    base_url = "https://api.openai.com/v1"
                
                self.client = OpenAI(
                    api_key=self.openai_api_key, 
                    base_url=base_url
                )
                print(f"OK Initialized OpenAI-compatible API with model: {self.model_name}")
        else:
            print(f"Loading model locally: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype="auto",
                device_map="auto"
            )
            print("OK Model loaded locally")
    
    def _call_llm(self, prompt: str, system_prompt: str = None, max_tokens: int = 8000, max_retries: int = 3) -> str:
        """
        Call the LLM with a prompt, with automatic retry on rate limits.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            max_tokens: Maximum tokens in response
            max_retries: Maximum number of retries on rate limit errors
            
        Returns:
            Generated text response
        """
        import time
        
        if self.use_api:
            contents = prompt
            
            for attempt in range(max_retries + 1):
                try:
                    if self.provider == "gemini":
                        response = self.client.models.generate_content(
                            model=self.model_name,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt if system_prompt else None,
                                max_output_tokens=max_tokens,
                                temperature=0.7
                            )
                        )
                        text = response.text
                    else:
                        messages = []
                        if system_prompt:
                            messages.append({"role": "system", "content": system_prompt})
                        messages.append({"role": "user", "content": contents})
                        
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=0.7
                        )
                        text = response.choices[0].message.content
                    if text is None:
                        # Fallback: extract from candidates/parts (Gemini specific)
                        try:
                            parts = response.candidates[0].content.parts
                            text = "".join(p.text for p in parts if hasattr(p, 'text') and p.text)
                        except (IndexError, AttributeError):
                            text = ""
                    return text or ""
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        if attempt < max_retries:
                            wait_time = 60 * (attempt + 1)  # 60s, 120s, 180s
                            print(f"  WAIT Rate limited. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                            time.sleep(wait_time)
                            continue
                    import traceback
                    traceback.print_exc()
                    print(f"API Error ({self.provider}):", e)
                    return ""
            return ""
        else:
            # Local inference
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(**inputs, max_new_tokens=max_tokens)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def classify_sector(self, report_excerpt: str) -> str:
        """Classify the sector of a report."""
        prompt = SECTOR_CLASSIFICATION_PROMPT.format(excerpt=report_excerpt[:2000])
        result = self._call_llm(prompt, max_tokens=50)
        return result.strip() if result else "Unknown"
    
    def extract_investment_signals(self, report_content: str) -> Dict:
        """
        Extract investment signals from report content.
        
        Args:
            report_content: Text content from industry report
            
        Returns:
            Dictionary of extracted investment signals
        """
        prompt = EXTRACT_INSIGHTS_PROMPT.format(report_content=report_content)
        response = self._call_llm(
            prompt,
            system_prompt=INVESTMENT_SIGNAL_SYSTEM,
            max_tokens=8000
        )
        
        # Try to parse as JSON
        try:
            # Find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        # Return as structured dict if JSON parsing fails
        return {"raw_analysis": response}
    
    def generate_pitch_brief(self, signals: Dict, sector: str) -> str:
        """Generate a pitch brief from investment signals."""
        prompt = PITCH_BRIEF_PROMPT.format(
            investment_signals=json.dumps(signals, indent=2),
            sector=sector
        )
        return self._call_llm(prompt, max_tokens=8000)
    
    def process_report(self, report_path: str) -> Dict:
        """
        Process a single industry report through the full pipeline.
        
        Args:
            report_path: Path to the report file (PDF, DOCX, or TXT)
            
        Returns:
            Dictionary containing analysis results
        """
        print(f"\nDOC Processing: {Path(report_path).name}")
        
        # Parse report
        content = self.report_parser.parse(report_path)
        print(f"  OK Parsed {len(content)} characters")
        
        # Classify sector
        sector = self.classify_sector(content[:3000]).encode('ascii', errors='ignore').decode('ascii')
        print(f"  OK Sector: {sector[:50]}...")
        
        # Extract signals
        signals = self.extract_investment_signals(content)
        print(f"  OK Extracted investment signals")
        
        # Generate pitch brief
        pitch_brief = self.generate_pitch_brief(signals, sector)
        print("  OK Generated pitch brief")
        
        return {
            "source_file": str(report_path),
            "sector": sector,
            "signals": signals,
            "pitch_brief": pitch_brief,
            "processed_at": datetime.now().isoformat()
        }
    
    def process_batch(self, reports_dir: str, output_excel: bool = True) -> List[Dict]:
        """
        Process multiple reports from a directory.
        
        Args:
            reports_dir: Directory containing report files
            output_excel: Whether to save results to Excel
            
        Returns:
            List of analysis results
        """
        reports_path = Path(reports_dir)
        report_files = list(reports_path.glob("*.pdf")) + \
                       list(reports_path.glob("*.docx")) + \
                       list(reports_path.glob("*.txt"))
        
        print(f"\nSTART Processing {len(report_files)} reports from {reports_dir}")
        
        results = []
        for report_file in tqdm(report_files, desc="Processing reports"):
            try:
                result = self.process_report(str(report_file))
                results.append(result)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"  ERR Error processing {report_file.name}: {e}")
                results.append({
                    "source_file": str(report_file),
                    "error": str(e),
                    "processed_at": datetime.now().isoformat()
                })
        
        # Save results
        self._save_results(results, output_excel)
        
        return results
    
    def _format_signals_markdown(self, signals: Dict) -> str:
        """Format investment signals into clean VC-style markdown sections."""
        content = ""
        section_num = 0

        # Report metadata
        for key in ['report_title', 'report_date', 'data_source']:
            val = signals.get(key, '')
            if val:
                label = key.replace('_', ' ').title()
                content += f"**{label}:** {val}\n"
        if content:
            content += "\n---\n\n"

        # Executive Summary
        exec_summary = signals.get('executive_summary', {})
        if exec_summary:
            section_num += 1
            content += f"### {section_num}. Executive Summary\n\n"
            if isinstance(exec_summary, dict):
                thesis = exec_summary.get('thesis', '')
                if thesis:
                    content += f"{thesis}\n\n"
                drivers = exec_summary.get('key_drivers', [])
                if drivers:
                    for d in drivers:
                        content += f"- **{d}**\n"
                    content += "\n"
                headline = exec_summary.get('headline_metric', '')
                if headline:
                    content += f"> **Headline Metric:** {headline}\n\n"
            else:
                content += f"{exec_summary}\n\n"
            content += "---\n\n"

        # Market Opportunity
        market = signals.get('market_opportunity', signals.get('market_size_growth', {}))
        if market:
            section_num += 1
            content += f"### {section_num}. Market Opportunity\n\n"
            if isinstance(market, dict):
                headline = market.get('headline', market.get('description', ''))
                if headline:
                    content += f"{headline}\n\n"
                metrics = market.get('metrics', market.get('key_metrics', []))
                if isinstance(metrics, list):
                    for m in metrics:
                        if isinstance(m, dict):
                            label = m.get('label', m.get('metric', ''))
                            value = m.get('value', '')
                            ctx = m.get('context', '')
                            content += f"- **{label}:** **{value}**"
                            if ctx:
                                content += f" — {ctx}"
                            content += "\n"
                        else:
                            content += f"- {m}\n"
                    content += "\n"
                # Handle nested dict with sub-categories
                for k, v in market.items():
                    if k in ('headline', 'description', 'metrics', 'key_metrics'):
                        continue
                    label = k.replace('_', ' ').title()
                    if isinstance(v, dict):
                        content += f"\n**{label}**\n"
                        for sk, sv in v.items():
                            sl = sk.replace('_', ' ').title()
                            if isinstance(sv, list):
                                content += f"- **{sl}:**\n"
                                for item in sv:
                                    content += f"  - {item}\n"
                            else:
                                content += f"- **{sl}:** {sv}\n"
                        content += "\n"
                    elif isinstance(v, list):
                        content += f"\n**{label}**\n"
                        for item in v:
                            content += f"- {item}\n"
                        content += "\n"
            else:
                content += f"{market}\n\n"
            content += "---\n\n"

        # Key Trends
        trends = signals.get('key_trends', [])
        if trends:
            section_num += 1
            content += f"### {section_num}. Key Trends\n\n"
            if isinstance(trends, list):
                for i, trend in enumerate(trends, 1):
                    if isinstance(trend, dict):
                        name = trend.get('trend_name', f'Trend {i}')
                        desc = trend.get('description', '')
                        data_pts = trend.get('key_data_points', trend.get('data_points', []))
                        content += f"#### {i}. {name}\n\n"
                        if desc:
                            content += f"{desc}\n\n"
                        if isinstance(data_pts, list) and data_pts:
                            content += "**Key Data Points**\n"
                            for dp in data_pts:
                                content += f"- {dp}\n"
                            content += "\n"
                        elif data_pts:
                            content += f"**Key Data Points:** {data_pts}\n\n"
                    else:
                        content += f"{i}. {trend}\n"
                content += "\n"
            content += "---\n\n"

        # Competitive Landscape
        comp = signals.get('competitive_landscape', {})
        if comp:
            section_num += 1
            content += f"### {section_num}. Competitive Landscape\n\n"
            if isinstance(comp, dict):
                overview = comp.get('overview', '')
                if overview:
                    content += f"#### Overview\n\n{overview}\n\n"
                leaders = comp.get('leader_characteristics', [])
                if leaders:
                    content += "#### Leader Characteristics\n\n"
                    if isinstance(leaders, list):
                        for l in leaders:
                            content += f"- {l}\n"
                    else:
                        content += f"{leaders}\n"
                    content += "\n"
                diffs = comp.get('key_differentiators', [])
                if diffs:
                    content += "#### Key Differentiators\n\n"
                    if isinstance(diffs, list):
                        for d in diffs:
                            content += f"- {d}\n"
                    else:
                        content += f"{diffs}\n"
                    content += "\n"
                players = comp.get('notable_players', [])
                if players:
                    content += "#### Notable Players\n\n"
                    if isinstance(players, list):
                        for p in players:
                            content += f"- {p}\n"
                    else:
                        content += f"{players}\n"
                    content += "\n"
                # Any other sub-keys
                for k, v in comp.items():
                    if k in ('overview', 'leader_characteristics', 'key_differentiators', 'notable_players', 'market_dynamics'):
                        continue
                    label = k.replace('_', ' ').title()
                    if isinstance(v, list):
                        content += f"#### {label}\n\n"
                        for idx, item in enumerate(v, 1):
                            content += f"{idx}. {item}\n"
                        content += "\n"
                    elif isinstance(v, str):
                        content += f"- **{label}:** {v}\n"
            else:
                content += f"{comp}\n\n"
            content += "---\n\n"

        # Investment Opportunities
        opps = signals.get('investment_opportunities', [])
        if opps:
            section_num += 1
            content += f"### {section_num}. Investment Opportunities\n\n"
            if isinstance(opps, list):
                for i, opp in enumerate(opps, 1):
                    if isinstance(opp, dict):
                        name = opp.get('opportunity_name', opp.get('opportunity_area', f'Opportunity {i}'))
                        desc = opp.get('description', opp.get('details', ''))
                        potential = opp.get('market_potential', opp.get('quantifiable_metric_or_signal', ''))
                        segments = opp.get('target_segments', [])
                        content += f"#### {i}. {name}\n\n"
                        if desc:
                            content += f"{desc}\n\n"
                        if potential:
                            content += f"- **Market Potential:** {potential}\n"
                        if segments:
                            if isinstance(segments, list):
                                content += f"- **Target Segments:** {', '.join(str(s) for s in segments)}\n"
                            else:
                                content += f"- **Target Segments:** {segments}\n"
                        content += "\n"
                    else:
                        content += f"{i}. {opp}\n"
                content += "\n"
            content += "---\n\n"

        # Risk Factors — as a TABLE
        risks = signals.get('risk_factors', [])
        if risks:
            section_num += 1
            content += f"### {section_num}. Risk Factors\n\n"
            if isinstance(risks, list) and risks and isinstance(risks[0], dict):
                content += "| Risk | Severity | Key Issue |\n"
                content += "|------|----------|----------|\n"
                for risk in risks:
                    name = risk.get('risk_name', 'Unknown')
                    severity = risk.get('severity', 'Medium')
                    desc = risk.get('description', risk.get('key_data_point', ''))
                    # Clean multiline for table
                    desc = desc.replace('\n', ' ').strip()
                    if len(desc) > 120:
                        desc = desc[:117] + '...'
                    content += f"| {name} | {severity} | {desc} |\n"
                content += "\n"
            elif isinstance(risks, list):
                for i, risk in enumerate(risks, 1):
                    content += f"{i}. {risk}\n"
                content += "\n"
            content += "---\n\n"

        # Signal Strength
        strength = signals.get('signal_strength', {})
        if strength:
            section_num += 1
            content += f"### {section_num}. Signal Strength\n\n"
            if isinstance(strength, dict):
                rating = strength.get('rating', strength.get('Rating', 'N/A'))
                justification = strength.get('justification', strength.get('Justification', ''))
                content += f"**Rating:** {rating}/10\n\n"
                if justification:
                    content += f"**Justification:** {justification}\n\n"
            else:
                content += f"**Rating:** {strength}\n\n"

        # Handle any remaining keys not already processed
        handled = {'report_title', 'report_date', 'data_source', 'executive_summary',
                   'market_opportunity', 'market_size_growth', 'key_trends',
                   'competitive_landscape', 'investment_opportunities',
                   'risk_factors', 'signal_strength'}
        for key, value in signals.items():
            if key.lower().replace(' ', '_') not in handled and key not in handled:
                label = key.replace('_', ' ').title()
                section_num += 1
                content += f"---\n\n### {section_num}. {label}\n\n"
                if isinstance(value, dict):
                    for k, v in value.items():
                        kl = k.replace('_', ' ').title()
                        if isinstance(v, list):
                            content += f"**{kl}**\n"
                            for item in v:
                                content += f"- {item}\n"
                            content += "\n"
                        else:
                            content += f"- **{kl}:** {v}\n"
                    content += "\n"
                elif isinstance(value, list):
                    for i, item in enumerate(value, 1):
                        content += f"{i}. {item}\n"
                    content += "\n"
                else:
                    content += f"{value}\n\n"

        return content

    def _save_markdown_report(self, result: Dict, timestamp: str):
        """Save analysis result as a VC-style Markdown investment memo."""
        if "error" in result and result["error"]:
            return
            
        source_name = Path(result.get("source_file", "")).stem
        sector = result.get('sector', 'N/A')
        md_path = self.output_dir / f"{source_name}_analysis_{timestamp}.md"
        
        # Clean title
        title = source_name.replace('-', ' ').replace('_', ' ').title()
        
        content = f"# {title}: Investment Analysis\n\n"
        content += f"**Sector:** {sector}  \n"
        content += f"**Processed At:** {result.get('processed_at', '')}  \n\n"
        content += "---\n\n"
        
        # Investment Signals
        content += "## Investment Signals\n\n"
        signals = result.get("signals", {})
        if isinstance(signals, dict) and "raw_analysis" not in signals:
            content += self._format_signals_markdown(signals)
        else:
            content += f"{signals.get('raw_analysis', str(signals))}\n"
            
        content += "\n---\n\n"
        content += "## Pitch Brief\n\n"
        content += result.get("pitch_brief", "No pitch brief generated.")
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"SAVE Saved Text Report: {md_path}")
        return md_path

    def _save_docx_report(self, md_path, timestamp: str):
        """Convert a Markdown report to a professionally formatted DOCX."""
        try:
            exporter = DocxExporter()
            docx_path = exporter.convert_md_to_docx(str(md_path))
            print(f"SAVE Saved DOCX Report: {docx_path}")
        except Exception as e:
            print(f"  ERR Error creating DOCX: {e}")

    def _save_results(self, results: List[Dict], to_excel: bool = True):
        """Save analysis results to JSON, Markdown, and optionally Excel."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save individual markdown reports and convert to DOCX
        for result in results:
            md_path = self._save_markdown_report(result, timestamp)
            if md_path:
                self._save_docx_report(md_path, timestamp)
        
        # Save JSON
        json_path = self.output_dir / f"analysis_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSAVE Saved JSON: {json_path}")
        
        if to_excel:
            # Create Excel summary
            df = pd.DataFrame([
                {
                    "Source File": r.get("source_file", ""),
                    "Sector": r.get("sector", ""),
                    "Signal Strength": r.get("signals", {}).get("signal_strength", "N/A"),
                    "Pitch Brief": r.get("pitch_brief", "")[:500] + "...",
                    "Processed At": r.get("processed_at", "")
                }
                for r in results
            ])
            
            excel_path = self.output_dir / f"analysis_{timestamp}.xlsx"
            df.to_excel(excel_path, index=False)
            print(f"SAVE Saved Excel: {excel_path}")


def main():
    """Example usage of the pipeline."""
    # Initialize pipeline with requested model
    pipeline = MarketResearchPipeline(
        model_name="minimaxai/minimax-m2.5", # Assuming the user wants to use minimax model via nvidia build
        use_api=True
    )
    
    # Process reports from data/reports directory
    reports_dir = Path(__file__).parent.parent / "data" / "reports"
    
    if reports_dir.exists() and any(reports_dir.iterdir()):
        results = pipeline.process_batch(str(reports_dir))
        print(f"\nDONE Processed {len(results)} reports successfully!")
    else:
        print(f"\nWARN  No reports found in {reports_dir}")
        print("Add PDF, DOCX, or TXT industry reports to the data/reports directory.")


if __name__ == "__main__":
    main()

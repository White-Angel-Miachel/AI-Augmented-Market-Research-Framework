"""
Pitch Brief Generator Module
Handles formatting and generation of structured investment pitch briefs
"""

from typing import Dict, Optional
from datetime import datetime
import json


class PitchBriefGenerator:
    """
    Generator for structured investment pitch briefs.
    Formats extracted signals into professional pitch documents.
    """
    
    def __init__(self):
        """Initialize the generator."""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load pitch brief templates."""
        return {
            "standard": {
                "sections": [
                    "Executive Summary",
                    "Market Opportunity",
                    "Target Company Profile",
                    "Competitive Analysis",
                    "Investment Thesis",
                    "Risk Factors",
                    "Due Diligence Checklist"
                ]
            },
            "quick": {
                "sections": [
                    "Summary",
                    "Opportunity",
                    "Thesis"
                ]
            }
        }
    
    def format_brief(
        self,
        llm_output: str,
        signals: Dict,
        sector: str,
        template: str = "standard"
    ) -> Dict:
        """
        Format LLM output into a structured pitch brief.
        
        Args:
            llm_output: Raw pitch brief from LLM
            signals: Extracted investment signals
            sector: Classified sector
            template: Template to use (standard/quick)
            
        Returns:
            Formatted pitch brief dictionary
        """
        brief = {
            "metadata": {
                "sector": sector,
                "generated_at": datetime.now().isoformat(),
                "template": template
            },
            "content": llm_output,
            "signals": signals,
            "structured": self._parse_sections(llm_output)
        }
        
        return brief
    
    def _parse_sections(self, content: str) -> Dict:
        """
        Parse content into named sections.
        
        Args:
            content: Raw pitch brief content
            
        Returns:
            Dictionary of section name to content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Check for section headers (markdown style)
            if line.strip().startswith('**') and line.strip().endswith('**'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.strip().strip('*').strip(':').strip()
                current_content = []
            elif line.strip().startswith('#'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.strip().lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def to_markdown(self, brief: Dict) -> str:
        """
        Convert brief to markdown format.
        
        Args:
            brief: Structured pitch brief dictionary
            
        Returns:
            Markdown formatted string
        """
        md_lines = [
            f"# Investment Brief: {brief['metadata']['sector']}",
            f"*Generated: {brief['metadata']['generated_at']}*",
            "",
            "---",
            ""
        ]
        
        # Add structured sections
        if brief.get('structured'):
            for section, content in brief['structured'].items():
                md_lines.extend([
                    f"## {section}",
                    "",
                    content,
                    ""
                ])
        else:
            md_lines.append(brief.get('content', ''))
        
        # Add signals appendix
        if brief.get('signals'):
            md_lines.extend([
                "---",
                "## Appendix: Raw Investment Signals",
                "",
                "```json",
                json.dumps(brief['signals'], indent=2),
                "```"
            ])
        
        return '\n'.join(md_lines)
    
    def to_excel_row(self, brief: Dict) -> Dict:
        """
        Convert brief to a flat dictionary for Excel export.
        
        Args:
            brief: Structured pitch brief dictionary
            
        Returns:
            Flat dictionary suitable for DataFrame row
        """
        structured = brief.get('structured', {})
        signals = brief.get('signals', {})
        
        return {
            "Sector": brief['metadata']['sector'],
            "Generated At": brief['metadata']['generated_at'],
            "Executive Summary": structured.get('Executive Summary', ''),
            "Market Opportunity": structured.get('Market Opportunity', ''),
            "Investment Thesis": structured.get('Investment Thesis', ''),
            "Target Profile": structured.get('Target Company Profile', ''),
            "Risk Factors": structured.get('Risk Factors', ''),
            "Market Size": signals.get('market_size', ''),
            "Signal Strength": signals.get('signal_strength', ''),
            "Key Trends": ', '.join(signals.get('key_trends', [])) if isinstance(signals.get('key_trends'), list) else signals.get('key_trends', '')
        }


class SignalAggregator:
    """
    Aggregates and analyzes signals across multiple reports.
    """
    
    def __init__(self):
        """Initialize the aggregator."""
        self.signals_by_sector = {}
    
    def add_signals(self, sector: str, signals: Dict):
        """Add signals from a report."""
        if sector not in self.signals_by_sector:
            self.signals_by_sector[sector] = []
        self.signals_by_sector[sector].append(signals)
    
    def get_sector_summary(self, sector: str) -> Dict:
        """
        Generate summary statistics for a sector.
        
        Args:
            sector: Sector name
            
        Returns:
            Summary dictionary
        """
        if sector not in self.signals_by_sector:
            return {}
        
        signals_list = self.signals_by_sector[sector]
        
        # Calculate average signal strength
        strengths = []
        for s in signals_list:
            if 'signal_strength' in s:
                try:
                    strengths.append(float(s['signal_strength']))
                except (ValueError, TypeError):
                    pass
        
        return {
            "sector": sector,
            "report_count": len(signals_list),
            "avg_signal_strength": sum(strengths) / len(strengths) if strengths else None,
            "reports_analyzed": len(signals_list)
        }
    
    def get_cross_sector_trends(self) -> Dict:
        """
        Identify trends appearing across multiple sectors.
        
        Returns:
            Dictionary of cross-cutting trends
        """
        all_trends = {}
        
        for sector, signals_list in self.signals_by_sector.items():
            for signals in signals_list:
                trends = signals.get('key_trends', [])
                if isinstance(trends, list):
                    for trend in trends:
                        trend_lower = trend.lower() if isinstance(trend, str) else str(trend)
                        if trend_lower not in all_trends:
                            all_trends[trend_lower] = {"count": 0, "sectors": set()}
                        all_trends[trend_lower]["count"] += 1
                        all_trends[trend_lower]["sectors"].add(sector)
        
        # Convert sets to lists for JSON serialization
        for trend in all_trends:
            all_trends[trend]["sectors"] = list(all_trends[trend]["sectors"])
        
        return all_trends

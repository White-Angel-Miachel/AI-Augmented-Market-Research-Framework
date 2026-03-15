"""
Prompt Templates for Market Research Analysis
VC-Style Investment Memo Format
"""

# System prompt for investment signal extraction
INVESTMENT_SIGNAL_SYSTEM = """You are a senior market research analyst at a top-tier venture capital firm.
Your task is to extract actionable investment signals from industry reports and structure them for investment decision-making.

CRITICAL RULES:
- Always return valid, complete JSON — never truncate your response.
- Include ALL requested sections with detailed analysis.
- Every trend, opportunity, and risk MUST include specific data points from the report.
- Use precise numbers and percentages — bold key metrics.
- Signal Strength must include both a numeric rating AND a detailed rationale.
- Format all output for maximum clarity and scannability."""

# Extract key insights from industry report
EXTRACT_INSIGHTS_PROMPT = """Analyze the following industry report and extract key investment signals.

REPORT CONTENT:
{report_content}

Return a complete JSON object with ALL of these sections fully populated:

{{
  "report_title": "exact title of the report",
  "report_date": "publication date if available",
  "data_source": "research firm name, methodology, sample size",

  "executive_summary": {{
    "thesis": "2-3 sentence investment thesis",
    "key_drivers": ["driver 1 with key metric", "driver 2 with key metric", "driver 3 with key metric"],
    "headline_metric": "the single most compelling metric from the report"
  }},

  "market_opportunity": {{
    "headline": "one-line summary of the market opportunity",
    "metrics": [
      {{"label": "metric name", "value": "specific number/percentage", "context": "brief explanation"}}
    ]
  }},

  "key_trends": [
    {{
      "trend_name": "clear, concise name",
      "description": "1-2 sentence explanation",
      "key_data_points": ["specific metric 1", "specific metric 2"]
    }}
  ],

  "competitive_landscape": {{
    "overview": "2-3 sentence market dynamics summary",
    "leader_characteristics": ["characteristic 1", "characteristic 2", "characteristic 3"],
    "key_differentiators": ["differentiator 1", "differentiator 2", "differentiator 3"],
    "notable_players": ["company/entity 1", "company/entity 2"]
  }},

  "investment_opportunities": [
    {{
      "opportunity_name": "clear name",
      "description": "1-2 sentence explanation",
      "market_potential": "specific size or growth metric",
      "target_segments": ["segment 1", "segment 2"]
    }}
  ],

  "risk_factors": [
    {{
      "risk_name": "clear name",
      "severity": "High/Medium/Low",
      "description": "1-2 sentence explanation",
      "key_data_point": "supporting evidence"
    }}
  ],

  "signal_strength": {{
    "rating": 8,
    "justification": "detailed rationale based on data quality, coverage, recency, and actionability"
  }}
}}

IMPORTANT: Write your COMPLETE response. Do NOT truncate any section."""

# Generate pitch brief from extracted signals
PITCH_BRIEF_PROMPT = """Based on the following investment signals, generate a structured VC-style investment pitch brief.

INVESTMENT SIGNALS:
{investment_signals}

SECTOR: {sector}

Write a clean, professional investment memo with ALL sections below.
Use bullet points, bold key metrics, and clear structure throughout.
DO NOT write long paragraphs — use short bullet points with bold numbers.

---

# [Short Title]: Investment Pitch Brief

---

## 1. Executive Summary

Write 2-3 concise sentences, then list key drivers as bullets:

- **Key Driver 1:** with specific metric
- **Key Driver 2:** with specific metric
- **Key Driver 3:** with specific metric

---

## 2. Market Opportunity

Key indicators highlighting the growth opportunity:

- **Metric Name:** **specific number** — brief context
- **Metric Name:** **specific number** — brief context
(List 5-7 bullet points with bold metrics)

---

## 3. Target Company Profile

Ideal investment targets:

- **Characteristic 1:** description
- **Characteristic 2:** description
(List 5-6 characteristics)

---

## 4. Competitive Landscape

### Overview
2-3 sentences on market dynamics.

### Leader Characteristics
- Characteristic with data

### Key Differentiators
- Differentiator with data

---

## 5. Investment Opportunities

### 1. [Opportunity Name]
- **Market Potential:** specific metric
- **Target Segments:** list of segments
- Brief description

### 2. [Opportunity Name]
(Repeat for each opportunity)

---

## 6. Risk Factors

| Risk | Severity | Key Issue |
|------|----------|-----------|
| Risk Name | High/Medium/Low | Brief description with data |
(Create a table with all risks)

---

## 7. Competitive Moat Indicators

- **Moat 1:** description
- **Moat 2:** description
(List 5-6 moat indicators)

---

## 8. Due Diligence Focus Areas

1. **Area Name:** specific investigation points
2. **Area Name:** specific investigation points
(List 6-8 areas)

---

## 9. Investment Thesis

Write a compelling 3-4 sentence investment thesis that ties together the market opportunity, target profile, and expected value creation. This is the most important section — make it clear, specific, and persuasive. Do NOT truncate.

---

## 10. Signal Strength

**Rating:** X/10
**Justification:** detailed rationale

---

CRITICAL: Write ALL 10 sections completely with proper formatting. Use --- dividers between sections. Bold all key metrics. Use bullet points not paragraphs. The Risk Factors MUST be a markdown table."""

# Sector classification prompt
SECTOR_CLASSIFICATION_PROMPT = """Classify the following report into the most appropriate sector.

REPORT EXCERPT:
{excerpt}

AVAILABLE SECTORS:
- FinTech
- HealthTech/BioTech
- Enterprise SaaS
- Consumer Tech
- CleanTech/Climate
- AI/ML Infrastructure
- Cybersecurity
- E-commerce/Marketplace
- EdTech
- PropTech
- Other (specify)

Return ONLY the sector name, nothing else. Do not add parentheses or extra text."""

# Summarization prompt for long reports
SUMMARIZE_REPORT_PROMPT = """Summarize the following industry report section, preserving all quantitative data and key insights:

{content}

Provide a concise summary (max 500 words) focusing on:
- Market statistics and projections
- Named companies and their market positions
- Specific trends with supporting data
- Investment-relevant signals"""

VaidyaAI — AI-Powered Medical Symptom Analyzer
Vaidya (वैद्य) — healer or physician in Sanskrit.
VaidyaAI brings preliminary medical guidance to anyone via a simple terminal interface.

Problem it solves
Millions of people — especially in rural and semi-urban areas — lack immediate access to a doctor for non-emergency concerns. VaidyaAI provides instant, AI-powered symptom analysis to help users understand urgency, possible conditions, and next steps.

⚠️ VaidyaAI is not a substitute for professional medical advice. Always consult a qualified doctor.

Project structure
vaidya_ai/
├── main.py          → CLI entry point (Click commands, user flow)
├── analyzer.py      → Anthropic API integration + response parsing
├── display.py       → Terminal UI using Rich (panels, tables, colours)
├── history.py       → Save/load session history to sessions.json
├── prompts.py       → System prompt + user prompt builder
├── requirements.txt → Python dependencies
└── sessions.json    → Auto-created on first run (stores history)
Setup
1. Clone / download the project
cd vaidya_ai
2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate       # Mac / Linux
venv\Scripts\activate          # Windows
3. Install dependencies
pip install -r requirements.txt
4. Set your Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"   # Mac / Linux
set ANTHROPIC_API_KEY=your-key-here        # Windows
Get a free API key at: https://console.anthropic.com

Usage
Analyse symptoms (main mode)
python main.py
View past sessions
python main.py --history
Delete all saved sessions
python main.py --clear-history
See all options
python main.py --help
How it works (architecture)
User Input (main.py)
      │
      ▼
Prompt Builder (prompts.py)
      │   Builds a structured prompt with patient context
      ▼
Claude API (analyzer.py)
      │   Sends prompt, receives JSON response
      ▼
Response Parser (analyzer.py)
      │   Parses JSON into a Python dict
      ├──► Display (display.py)     → Shows coloured terminal output
      └──► History (history.py)    → Saves session to sessions.json
Tech stack
Library	Purpose
anthropic	Communicate with Claude AI
rich	Beautiful terminal UI
click	CLI argument/option parsing
json	Parse Claude's structured output
datetime	Timestamp sessions
Sample output
╭──────────────────────────────────────╮
│  Urgency Assessment                  │
│  ▲  Urgency Level: HIGH              │
│  Symptoms suggest possible infection │
╰──────────────────────────────────────╯

  Possible Conditions
  ┌──────────────────┬───────────┬─────────────────────────────┐
  │ Condition        │ Likelihood│ Explanation                  │
  ├──────────────────┼───────────┼─────────────────────────────┤
  │ Strep throat     │   High    │ Fever + sore throat pattern  │
  │ Viral pharyngitis│   Medium  │ Common in this age group     │
  └──────────────────┴───────────┴─────────────────────────────┘

  Recommendations
  1. Visit a doctor within 24 hours for a throat swab
  2. Stay hydrated and rest

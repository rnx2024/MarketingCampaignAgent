## 📣 Marketing Agent

A sleek, AI-powered marketing assistant that uses OpenAI and LangGraph to **plan**, **execute**, and **review** marketing campaigns tailored to product types, audience personas, channels, goals, and locations.

---

## 🔧 Features
```
- ✅ 3-Stage AI Workflow: Planner → Executor → Reviewer (via LangGraph)
- 🎯 Custom input form for:
  - Product type & price tier
  - Audience personas (e.g. Millennial, Tech Enthusiast, Gen Z)
  - Location targeting (US, PH, EU, LATAM, etc.)
  - Marketing channels (e.g. TikTok, Facebook, LinkedIn, TV)
  - Budget, duration, tone, call-to-action
  - Campaign goal and strategy type
- 📄 Clean AI-generated output with PDF export
- 🧠 GPT-4o powered insights (via `langchain-openai`)
```
---

## 📸 Screenshot

![screenshot](https://github.com/rnx2024/marketingcampaign-agent/blob/main/screenshots/Screenshot%202025-08-10%20171335.png)

---

## 🚀 Getting Started

**1. Clone the Repository**
```
git clone https://github.com/your-org/marketing-campaign-agent.git
cd marketing-campaign-agent
```
**2. Create a Virtual Environment**
```
python -m venv myenv
myenv\Scripts\activate on Windows
```
**3. Install Dependencies**
```
pip install -r requirements.txt
```

**4. Add Secrets**

Create a .streamlit/secrets.toml file:
```
OPENAI_API_KEY = "your-openai-api-key"
```
**Never commit your API keys to GitHub.**__

**5. Run the App**
```
streamlit run app.py
```
## 📁 File Structure
```
.
├── app.py                   # Streamlit frontend + LangGraph workflow
├── requirements.txt
├── .streamlit
│   └── config.toml          # UI theme configuration
│   └── secrets.toml         # API secrets (not committed)
├── assets/
│   └── marketing-agent-ui.png
```

## 🧠 Tech Stack
```
Streamlit
LangGraph
LangChain
OpenAI GPT-4o
FPDF
```

## 📄 License
© 2025 Rhanny Urbis

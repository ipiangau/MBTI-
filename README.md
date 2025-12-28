# 🎄 MBTI North Pole

**Analyze personalities, one chat at a time!**

A Streamlit-powered application that transforms your LINE chat history into deep personality insights using Large Language Models (LLMs). Features a festive "North Pole" theme, interactive visualizations, and an AI Elf agent for chat analysis.

![Demo Preview](image_e3ec95.jpg)

## 🛠️ Installation

### Prerequisites
* **Python 3.8+**
* **Ollama** (for local analysis)
* Model requirement: `llama3.2:1b`

### 1. Clone the repository
```bash
git clone [https://github.com/ipiangau/MBTI-](https://github.com/ipiangau/MBTI-)
cd MBTI-

Remote NCKU API (for the LLM)
Local Ollama API (alternative for the LLM)
OpenAI API (for the Image Generation/Fashion tool)
Goolgle Map API (for places recommendation)

app.py: The main entry point. Handles the Streamlit UI, theme (CSS/Snowflakes), and session state management.
agent.py: Handles logic for calling LLMs (Ollama/Remote), extracting strict JSON for analysis, and generating chat responses/fashion advice.
mbti.py: Contains the parsing logic for LINE chat files (parse_line_chat_dynamic) and prompt engineering helpers.
charts.py: Uses Plotly to generate the Spectrum, Bar, and Radar charts based on the analysis data.

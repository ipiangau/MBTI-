# 🎄 MBTI North Pole

**Analyze personalities, one chat at a time!**

A Streamlit-powered application that transforms your LINE chat history into deep personality insights using Large Language Models (LLMs). Features a festive "North Pole" theme, interactive visualizations, and an AI Elf agent for chat analysis.

## 🛠️ Installation

### Prerequisites
* **Python 3.8+**
* **Ollama** (for local analysis)
* Model requirement: `llama3.2:1b`

### 1. Clone the repository
```bash
git clone [https://github.com/ipiangau/MBTI-](https://github.com/ipiangau/MBTI-)
cd MBTI-
```
### 2. Install Dependencies
```bash
pip install streamlit plotly requests openai python-dotenv

CREATE .env FILE
API_BASE_URL="https://your-remote-api.com"
API_KEY=your-remote-api-key

LOCAL_OLLAMA_URL="http://localhost:11434"
OLLAMA_API_KEY=ollama 

OPENAI_API_KEY=sk-...
MAP_API_KEY=
```
### Usage
## 1. Start the Application:
```bash
streamlit run app.py
```
## 2. Configure the Agent:
```bash
- Open the Sidebar (⚙️)
- Select your "AI Helper" (Remote NCKU or Local Ollama)
```
## 3. Start the Application:
```bash
- Upload your LINE chat .txt file
- Select the specific friends you want to analyze from the list
- Click 🚀 Run Analysis
```
## 4. Explore:
```bash
- View the generated charts in the Visualizations tabs
- Chat with the Elf agent below the results
- Try asking: "What is [Name]'s fashion style?" or "Compare everyone's energy levels"
```
### Project Structure
```bash
app.py: The main entry point. Handles the Streamlit UI, theme (CSS/Snowflakes), and session state management.
agent.py: Handles logic for calling LLMs (Ollama/Remote), extracting strict JSON for analysis, and generating chat responses/fashion advice.
mbti.py: Contains the parsing logic for LINE chat files (parse_line_chat_dynamic) and prompt engineering helpers.
charts.py: Uses Plotly to generate the Spectrum, Bar, and Radar charts based on the analysis data.
```
### Technologies
```bash
Remote NCKU API (for the LLM)
Local Ollama API (alternative for the LLM)
OpenAI API (for the Image Generation/Fashion tool)
Goolgle Map API (for places recommendation)
```

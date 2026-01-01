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
#### 1. Start the Application:
```bash
streamlit run app.py
```
#### 2. Configure the Agent:
```bash
- Open the Sidebar (⚙️)
- Select your "AI Helper" (Remote NCKU or Local Ollama)
```
#### 3. Start the Application:
```bash
- Upload your LINE chat .txt file
- Select the specific friends you want to analyze from the list
- Click 🚀 Run Analysis
```
#### 4. Explore:
```bash
- View the generated charts in the Visualizations tabs
- Chat with the Elf agent below the results
- Try asking: "What is [Name]'s fashion style?" or "Compare everyone's energy levels"
```
### Project Structure
```bash
app.py:
  The main entry point. Handles the Streamlit UI, theme (CSS/Snowflakes), and session state management
agent.py:
  Handles logic for calling LLMs (Ollama/Remote), extracting strict JSON for analysis, and generating chat responses/fashion advice
mbti.py:
  Contains the parsing logic for LINE chat files (parse_line_chat_dynamic) and prompt engineering helpers
charts.py:
  Uses Plotly to generate the Spectrum, Bar, and Radar charts based on the analysis data
```
### Technologies
```bash
Remote NCKU API (for the LLM)
Local Ollama API (alternative for the LLM)
OpenAI API (for the Image Generation/Fashion tool)
Goolgle Map API (for places recommendation)
```
<<<<<<< Updated upstream
=======
### Flow Chart
flowchart 
    %% Define Styles
    classDef user fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef system fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef llm fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    classDef tool fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef api fill:#ffebee,stroke:#c62828,stroke-width:2px;

    %% Node
    User([User / Streamlit UI])
    Router{"Input Analysis<br/>(agent.py)"}
    
    %% Branch Decisions
    CheckMap{"Has Location<br/>Keywords?"}
    CheckChart{"Has Chart<br/>Keywords?"}
    CheckFashion{"Has Fashion<br/>Keywords?"}
    CheckImg{"Has Image<br/>Keywords?"}
    
    %% LLM Processing
    LLM_Extract[LLM: JSON Extraction]
    LLM_Chat[LLM: Chat Response]
    LLM_Style[LLM: Style Advice]
    
    %% Tool && API
    Tool_Map[Tool: Recommend Places]
    Tool_Chart[Tool: Generate Charts]
    Tool_GenImg[Tool: OpenAI Image Gen]
    
    API_Google[Google Maps API]
    API_Ollama[Ollama / NCKU API]
    API_OpenAI[OpenAI API]
    
    Output([Display Response / Chart / Image])

    %% Apply Styles
    class User,Output user;
    class Router,CheckMap,CheckChart,CheckFashion,CheckImg system;
    class LLM_Extract,LLM_Chat,LLM_Style llm;
    class Tool_Map,Tool_Chart,Tool_GenImg tool;
    class API_Google,API_Ollama,API_OpenAI api;

    %% Connection Flow
    User --> |Input Text| Router
    Router --> CheckMap
    
    %% 1. Map Flow
    CheckMap -- Yes --> LLM_Extract
    LLM_Extract --> |Extract Intent/Loc| API_Ollama
    API_Ollama --> Tool_Map
    Tool_Map --> |Get Coordinates/Places| API_Google
    API_Google --> Output
    
    %% 2. Chart Flow
    CheckMap -- No --> CheckChart
    CheckChart -- Yes --> Tool_Chart
    Tool_Chart --> |Plotly Logic| Output
    
    %% 3. Fashion Flow
    CheckChart -- No --> CheckFashion
    CheckFashion -- Yes --> LLM_Style
    LLM_Style --> |Get Prompt| API_Ollama
    LLM_Style --> |Generate Visual| Tool_GenImg
    Tool_GenImg --> API_OpenAI
    API_OpenAI --> Output

    %% 4. Image Flow
    CheckFashion -- No --> CheckImg
    CheckImg -- Yes --> Tool_GenImg
    Tool_GenImg --> Output
    
    %% 5.Conversation Flow
    CheckImg -- No --> LLM_Chat
    LLM_Chat --> |Conversation| API_Ollama
    API_Ollama --> Output

### FSM
stateDiagram
    direction LR

    %% Define Styles
    classDef defaultStyle fill:#fff,stroke:#333,stroke-width:1px;
    classDef active fill:#dcedc8,stroke:#558b2f,stroke-width:2px;

    %% Entry Point
    [*] --> Init
    Init --> Analyze_Tab : Select Tab 1
    Init --> Quiz_Tab : Select Tab 2
    Init --> Growth_Tab : Select Tab 3

    %% Tab 1: Chat Analyzer
    state Analyze_Tab {
        [*] --> Waiting_Upload
        Waiting_Upload --> File_Parsed : Upload .txt
        File_Parsed --> Analysis_Ready : Click 'Run Analysis'
        Analysis_Ready --> Chat_Mode : LLM Returns JSON
        Chat_Mode --> Chat_Mode : User Chat Loop
    }

    %% Tab 2: Personality Quiz
    state Quiz_Tab {
        [*] --> Taking_Quiz
        Taking_Quiz --> Quiz_Calculated : Click 'Calculate Type'
        Quiz_Calculated --> Interview_Mode : Show Results
        Interview_Mode --> Interview_Mode : Chat Loop (Dr. Elf)
        Interview_Mode --> Taking_Quiz : Click 'Retake Test'
    }

    %% Tab 3: Growth Coach
    state Growth_Tab {
        [*] --> Input_MBTI
        Input_MBTI --> Coaching_Session : Click 'Start Coaching'
        Coaching_Session --> Coaching_Session : Chat Loop (Advice)
        Coaching_Session --> Input_MBTI : Click 'Change Type'
    }

    %% Tab Switching Transitions
    Analyze_Tab --> Quiz_Tab : Switch Tab
    Quiz_Tab --> Growth_Tab : Switch Tab
    Growth_Tab --> Analyze_Tab : Switch Tab

    %% Apply Styles
    class Analyze_Tab active
    class Quiz_Tab active
    class Growth_Tab active
>>>>>>> Stashed changes

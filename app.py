import streamlit as st
import os
from dotenv import load_dotenv

import mbti
import charts
import agent

load_dotenv()

# ==========================================
# Page Config & Theme
# ==========================================
st.set_page_config(page_title="🎄 MBTI North Pole", layout="wide")

def set_cute_theme():
    st.markdown("""
    <style>
    .stApp {
        background-image: url('https://i.pinimg.com/1200x/a5/60/17/a5601713b0833fc0321076a49899dca5.jpg');
        color: #fff;
        background-size: cover;
    }
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.15); /* Slightly more opaque for readability */
        border: 2px solid #8B0000;
        border-radius: 20px;
    }
    .stButton > button {
        background-color: #8B0000 !important;
        color: white !important;
        font-weight: bold;
        border: none;
        border-radius: 15px;
        border-top: 6px solid white !important;
        box-shadow: 0px 4px 0px #500000;
    }
    .stButton > button:hover {
        transform: translateY(2px);
        box-shadow: 0px 2px 0px #500000;
        background-color: #a00000 !important;
    }
    @keyframes snow {
        0% { transform: translateY(-10px); opacity: 0; }
        20% { opacity: 1; }
        100% { transform: translateY(100vh); opacity: 0.3; }
    }
    .snowflake {
        position: fixed; top: -10%;
        animation: snow 10s linear infinite;
        color: #fff; pointer-events: none; z-index: 9999;
        font-size: 1.5em;
    }
    </style>
    <div class="snowflake" style="left:10%">❄️</div>
    <div class="snowflake" style="left:30%; animation-delay:2s">❅</div>
    <div class="snowflake" style="left:50%; animation-delay:4s">❆</div>
    <div class="snowflake" style="left:70%; animation-delay:1s">❄️</div>
    <div class="snowflake" style="left:90%; animation-delay:5s">❅</div>
    """, unsafe_allow_html=True)

set_cute_theme()

# ==========================================
# Sidebar Settings
# ==========================================
with st.sidebar:
    st.image(
    [
        "https://i.pinimg.com/736x/3d/39/c3/3d39c364105ac84dfc91b6f367259f1a.jpg",
        "https://i.pinimg.com/736x/27/63/6b/27636ba121aba11e515165d999b27a5c.jpg"
    ], width=80)
    st.header("⚙️ North Pole Settings")
    connection_type = st.radio("AI Helper", ["Remote NCKU", "Local Ollama"])

    if connection_type == "Remote NCKU":
        api_base = os.getenv("API_BASE_URL")
        api_key = os.getenv("API_KEY")
        if not api_key: api_key = st.text_input("Secret Key", type="password")
        model_name = "gemma3:4b"
    else:
        api_base = os.getenv("LOCAL_OLLAMA_URL", "http://localhost:11434")
        api_key = "ollama"
        api_key = os.getenv("OLLAMA_API_KEY", "ollama") 
        model_name = "llama3.2:1b"

    st.markdown("---")
    if st.button("🗑️ Refresh"):
        st.session_state.clear()
        st.rerun()

# ==========================================
# State Initialization
# ==========================================
# Tab 1: Analyzer
if "parsed_speakers" not in st.session_state: st.session_state.parsed_speakers = {}
if "analysis_results" not in st.session_state: st.session_state.analysis_results = None
if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
if "charts_data" not in st.session_state: st.session_state.charts_data = None 

# Tab 2: Quiz
if "quiz_answers" not in st.session_state: st.session_state.quiz_answers = {}
if "quiz_finished" not in st.session_state: st.session_state.quiz_finished = False
if "quiz_result_mbti" not in st.session_state: st.session_state.quiz_result_mbti = None
if "interview_history" not in st.session_state: st.session_state.interview_history = []
if "quiz_scores" not in st.session_state: st.session_state.quiz_scores = None

# Tab 3: Growth 
if "growth_mbti" not in st.session_state: st.session_state.growth_mbti = None
if "growth_history" not in st.session_state: st.session_state.growth_history = []

# ==========================================
# Main Layout
# ==========================================
st.image("https://parade.com/.image/w_1080,q_auto:good,c_limit/MTkwNTgxMDYyNDUyNTIwODI4/santa-facts-jpg.jpg?arena_f_auto", width=150)
st.title("AI MBTI")
st.markdown("### *Analyzing personalities, one chat at a time!*")

# Create Tabs
tab_upload, tab_test, tab_growth = st.tabs(["📂 Analyze Chat", "📝 Take Test", "🌱 Personal Growth"])

# ==========================================
# TAB 1: Chat Analysis
# ==========================================
with tab_upload:
    uploaded_file = st.file_uploader("📂 Drop your chat file here", type=['txt'])

    # Welcome Message
    if not uploaded_file and not st.session_state.analysis_results:
        st.info("👋 **Welcome!** Upload a chat history to get started. 🎁")

    # File Processing
    if uploaded_file and api_base:
        if not st.session_state.parsed_speakers:
            content = uploaded_file.getvalue().decode("utf-8")
            st.session_state.parsed_speakers = mbti.parse_line_chat_dynamic(content)

        if st.session_state.parsed_speakers:
            speakers = st.session_state.parsed_speakers
            names = list(speakers.keys())
            
            if st.button("🚀 Run Analysis"):
                if not selected:
                    st.warning("Pick someone!")
                else:
                    with st.spinner("🦌 Crunching numbers..."):
                        data = {n: speakers[n] for n in selected}
                        sys_prompt, user_content = mbti.construct_analysis_prompt(data)
                        res = agent.run_analysis_request(sys_prompt, user_content, api_key, api_base, model_name)
                        
                        if res and "results" in res:
                            st.session_state.analysis_results = res["results"]
                            st.session_state.chat_messages = []
                            st.session_state.charts_data = None # Reset charts
                            
                            intro_msg = f"**Analysis Complete!** 🎄\n"
                            for p in res["results"]:
                                intro_msg += f"\n* **{p['name']}**: `{p['mbti']}`"
                            st.session_state.chat_messages.append({"role": "assistant", "content": intro_msg})
                            st.rerun()
                        else:
                            st.error("Analysis Failed.")

# ==========================================
# 5. Results & Chat
# ==========================================
if st.session_state.analysis_results:
    st.markdown("---")
    
    # --- CHART SECTION (UPDATED) ---
    if st.session_state.charts_data:
        st.subheader("📊 Visualizations")
        # Tabs for multiple graph types
        tab1, tab2, tab3 = st.tabs(["✨ Spectrum", "📊 Bar Chart", "🕸️ Radar"])
        with tab1:
            st.plotly_chart(st.session_state.charts_data['spectrum'], use_container_width=True)
        with tab2:
            st.plotly_chart(st.session_state.charts_data['bar'], use_container_width=True)
        with tab3:
            st.plotly_chart(st.session_state.charts_data['radar'], use_container_width=True)

    # Chat History
    st.markdown("### 💬 Chat with Elf")
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Ask about compatibility..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                resp_text, _ = agent.generate_chat_response(
                    prompt, st.session_state.chat_messages, 
                    st.session_state.analysis_results,
                    api_key, api_base, model_name, mbti.is_chinese
                )
            if not st.session_state.analysis_results:
                st.markdown("### 👥 Who is on the list?")
                selected = st.multiselect("Pick friends:", names, default=names)
                
                if st.button("🚀 Run Analysis"):
                    if not selected:
                        st.warning("Pick someone!")
                    else:
                        with st.spinner("🦌 Crunching numbers..."):
                            data = {n: speakers[n] for n in selected}
                            sys_prompt, user_content = mbti.construct_analysis_prompt(data)
                            res = agent.run_analysis_request(sys_prompt, user_content, selected, api_key, api_base, model_name)
                            if res and "results" in res:
                                st.session_state.analysis_results = res["results"]
                                st.session_state.chat_messages = []
                                st.session_state.charts_data = None # Reset charts
                                
                                intro_msg = f"**Analysis Complete!** 🎄\n"
                                for p in res["results"]:
                                    intro_msg += f"\n* **{p['name']}**: `{p['mbti']}`"
                                st.session_state.chat_messages.append({"role": "assistant", "content": intro_msg})
                                st.rerun()
                            else:
                                st.error("Analysis Failed.")

    # Display Results & Chat
    if st.session_state.analysis_results:
        st.markdown("---")
        
        # Display Charts if they exist
        if st.session_state.charts_data:
            st.subheader("📊 Visualizations")
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["✨ Spectrum", "📊 Bar Chart", "🕸️ Radar"])
            with chart_tab1:
                st.plotly_chart(st.session_state.charts_data['spectrum'], use_container_width=True)
            with chart_tab2:
                st.plotly_chart(st.session_state.charts_data['bar'], use_container_width=True)
            with chart_tab3:
                st.plotly_chart(st.session_state.charts_data['radar'], use_container_width=True)

        # Chat History
        st.markdown("### 💬 Chat with Elf")
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input
        if prompt := st.chat_input("Ask about compatibility, fight, fashion or anything about MBTI..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Only call the agent once
                    resp_text, extra_data = agent.generate_chat_response(
                        prompt, 
                        st.session_state.chat_messages, 
                        st.session_state.analysis_results,
                        api_key, api_base, model_name, mbti.is_chinese
                    )
                    
                    # --- HANDLING TOOLS ---
                    if resp_text == "TOOL:CHART":
                        # Generate Charts
                        results = st.session_state.analysis_results
                        charts_dict = {
                            'spectrum': charts.generate_bipolar_chart(results),
                            'bar': charts.generate_group_bar_chart(results),
                            'radar': charts.generate_radar_chart(results)
                        }
                        st.session_state.charts_data = charts_dict
                        
                        final_msg = "📊 I've painted some charts for you! (See tabs above)"
                        st.markdown(final_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": final_msg})
                        st.rerun()

                    elif resp_text == "TOOL:IMAGE":
                        # Generate Image
                        try:
                            from openai import OpenAI
                            # Note: This requires OPENAI_API_KEY in .env, separate from your LLM key if using Ollama
                            openai_key = os.getenv("OPENAI_API_KEY")
                            if openai_key:
                                client = OpenAI(api_key=openai_key)
                                image_response = client.images.generate(
                                    model="dall-e-3", # Updated model name usually
                                    prompt=extra_data,   
                                    size="1024x1024"
                                )
                                image_url = image_response.data[0].url
                                st.image(image_url, caption="🖼 Generated Image")
                                st.session_state.chat_messages.append({"role": "assistant", "content": f"🖼 Here is your image based on: {extra_data}"})
                            else:
                                st.error("OpenAI API Key missing for image generation.")
                        except Exception as e:
                            st.error(f"Image generation failed: {e}")

                    else:
                        # Standard Text Response
                        st.markdown(resp_text)
                        st.session_state.chat_messages.append({"role": "assistant", "content": resp_text})

# ==========================================
# TAB 2: Interactive Test
# ==========================================
with tab_test:
    st.header("🧠 Personality Self-Test")
    questions = mbti.get_quiz_questions()
    
    if not st.session_state.quiz_finished:
        st.write(f"Answer these {len(questions)} questions to find your type!")
        
        # Calculate progress safely
        current_answers = len(st.session_state.quiz_answers)
        progress = current_answers / len(questions) if len(questions) > 0 else 0
        st.progress(progress)
        
        with st.form("quiz_form"):
            for q in questions:
                st.markdown(f"**{q['id']}. {q['txt']}**")
                # Use key to persist state
                val = st.radio(
                    "Select:", 
                    ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
                    index=None, 
                    horizontal=True, 
                    key=f"q_{q['id']}", 
                    label_visibility="collapsed"
                )
            
            if st.form_submit_button("Calculate Type"):
                # Collect answers manually from session state keys
                all_answered = True
                temp_answers = {}
                for q in questions:
                    key = f"q_{q['id']}"
                    if st.session_state.get(key) is None:
                        all_answered = False
                        break
                    val_str = st.session_state[key]
                    temp_answers[q['id']] = {
                        "Strongly Disagree": -2, "Disagree": -1, "Neutral": 0, "Agree": 1, "Strongly Agree": 2
                    }.get(val_str, 0)
                
                if all_answered:
                    st.session_state.quiz_answers = temp_answers
                    mbti_type, scores = mbti.calculate_quiz_result(st.session_state.quiz_answers)
                    st.session_state.quiz_result_mbti = mbti_type
                    st.session_state.quiz_scores = scores
                    st.session_state.quiz_finished = True
                    st.session_state.interview_history.append({
                        "role": "assistant", 
                        "content": f"Hello! Based on the test, you seem to be **{mbti_type}**. I'm Dr. Elf. Let's chat!"
                    })
                    st.rerun()
                else:
                    st.warning("Please answer all questions before submitting.")

    else:
        # Quiz Finished View
        m_type = st.session_state.quiz_result_mbti
        st.balloons()
        st.success(f"🎉 Your Test Result: **{m_type}**")
        
        fake_result = [{"name": "You", "mbti": m_type, "scores": st.session_state.quiz_scores}]
        # Assuming generate_radar_chart can handle single entry or you might need to adapt it
        st.plotly_chart(charts.generate_radar_chart(fake_result), use_container_width=True)
        
        if st.button("🔄 Retake Test"):
            st.session_state.quiz_finished = False
            st.session_state.quiz_answers = {}
            st.session_state.interview_history = []
            st.rerun()

        st.markdown("### 🕵️‍♀️ Dr. Elf's Interview Room")
        for msg in st.session_state.interview_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
                
        if user_text := st.chat_input("Reply to Dr. Elf...", key="chat_tab2"):
            st.session_state.interview_history.append({"role": "user", "content": user_text})
            with st.chat_message("user"): st.markdown(user_text)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    reply = agent.run_interview_step(
                        user_text, st.session_state.interview_history, 
                        st.session_state.quiz_result_mbti, api_key, api_base, model_name
                    )
                    st.markdown(reply)
                    st.session_state.interview_history.append({"role": "assistant", "content": reply})

# ==========================================
# TAB 3: Personal Growth
# ==========================================
with tab_growth:
    st.header("🌱 Personal Growth Coach")
    st.markdown("Already know your type? Get customized advice!")

    # 1. INPUT PHASE
    if not st.session_state.growth_mbti:
        col1, col2 = st.columns([3, 1])
        with col1:
            user_input_mbti = st.text_input("Enter your MBTI Type (e.g., INTJ, ENFP):", max_chars=4)
        with col2:
            st.write("") # Spacer
            st.write("") 
            if st.button("Start Coaching"):
                if len(user_input_mbti) == 4:
                    st.session_state.growth_mbti = user_input_mbti.upper()
                    st.session_state.growth_history = [{
                        "role": "assistant", 
                        "content": f"Hello **{user_input_mbti.upper()}**! I'm your Growth Coach. Ask me for self-improvement tips or how to handle specific situations!"
                    }]
                    st.rerun()
                else:
                    st.error("Please enter a 4-letter type (e.g., ISTP).")

    # 2. CHAT PHASE
    else:
        st.info(f"Coaching for: **{st.session_state.growth_mbti}**")
        if st.button("🔄 Change Type"):
            st.session_state.growth_mbti = None
            st.session_state.growth_history = []
            st.rerun()

        st.markdown("---")
        
        # Display Chat
        for msg in st.session_state.growth_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("Ask for advice (e.g., 'How do I handle stress?')", key="chat_tab3"):
            st.session_state.growth_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Coach is thinking..."):
                    reply = agent.run_growth_advisor_step(
                        prompt, 
                        st.session_state.growth_history, 
                        st.session_state.growth_mbti,
                        api_key, api_base, model_name
                    )
                    st.markdown(reply)
                    st.session_state.growth_history.append({"role": "assistant", "content": reply})
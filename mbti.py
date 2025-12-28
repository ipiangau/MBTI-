import re
import json
import agent
import urllib.parse
import streamlit as st
# ==========================================
# 1. Language Helper
# ==========================================
def is_chinese(text):
    """Check if input text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

# ==========================================
# 2. Scoring Helper
# ==========================================
def align_scores_with_mbti(mbti_type, raw_scores):
    if not mbti_type or len(raw_scores) != 4:
        return [50, 50, 50, 50]
    
    mbti = mbti_type.upper()
    corrected = list(raw_scores)
    
    # E vs I
    if 'I' in mbti: corrected[0] = min(corrected[0], 45)
    elif 'E' in mbti: corrected[0] = max(corrected[0], 55)
    # S vs N
    if 'S' in mbti: corrected[1] = min(corrected[1], 45)
    elif 'N' in mbti: corrected[1] = max(corrected[1], 55)
    # T vs F
    if 'T' in mbti: corrected[2] = min(corrected[2], 45)
    elif 'F' in mbti: corrected[2] = max(corrected[2], 55)
    # J vs P
    if 'J' in mbti: corrected[3] = min(corrected[3], 45)
    elif 'P' in mbti: corrected[3] = max(corrected[3], 55)
    
    return corrected

# ==========================================
# 3. File Parser
# ==========================================
def parse_line_chat_dynamic(file_content):
    lines = file_content.split('\n')
    messages = {}
    
    skip_keywords = ["通話時間", "Call time", "Unsend message", "joined the chat", "invite"]
    invalid_names = ["You", "you", "System", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for line in lines:
        line = line.strip()
        if not line: continue
        parts = line.split('\t')
        if len(parts) < 3: parts = line.split(' ', 2)

        if len(parts) >= 3:
            time_str, name, msg = parts[0], parts[1].strip(), parts[2].strip()
            
            if not re.match(r'^\d{1,2}:\d{2}$', time_str): continue
            if name.endswith(" Photos") or name.endswith(" Stickers"): name = name.replace(" Photos", "").replace(" Stickers", "")
            if any(k in msg for k in skip_keywords): continue
            if msg in ["[Photos]", "[Stickers]"]: continue 
            if name in invalid_names: continue

            if name not in messages: messages[name] = []
            messages[name].append(msg)
            
    return {k: "\n".join(v) for k, v in messages.items() if len(v) >= 3}

# ==========================================
# Prompt Constructor
# ==========================================
def construct_analysis_prompt(selected_speakers_data):
    """
    selected_speakers_data: dict of {name: chat_lines}
    """

    conversation_sample = ""
    for name, text in selected_speakers_data.items():
        lines = text[:600].strip()
        if not lines:
            lines = "[No messages]"  # pad empty speakers
        conversation_sample += f"=== {name} ===\n{lines}\n\n"

    system_prompt = f"""
You are an expert MBTI analyst.

Task: Analyze the provided text samples for EACH speaker independently.
You MUST output JSON ONLY.
JSON Format:
{{
  "results": [
    {{
      "name": "Name1",
      "mbti": "XXXX",
      "scores": [10, 20, 30, 40]
    }}
  ]
}}

ALWAYS analyze these speakers: {', '.join(selected_speakers_data.keys())}
Do NOT skip anyone, even if they have little text.
"""
    return system_prompt, conversation_sample


def tool_generate_style_advice(mbti_type, api_key):
    # 1. Get the Text Advice from Ollama
    system_prompt = f"""
    You are a Fashion Stylist. User MBTI: {mbti_type}.
    Describe a specific outfit in 3 keywords (e.g., "Minimalist, Beige, Structured").
    Then provide the full detailed advice.
    
    Format:
    KEYWORDS: [Keyword1, Keyword2, Keyword3]
    ADVICE: [Full advice here...]
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    res = call_ollama_api(messages, api_key, base_url, model_name, force_json=False)
    content = res.get('content', '')
    
    # 2. Extract Keywords for the Search Link
    # We try to find "KEYWORDS: ..." to make a smart search URL
    keywords = f"{mbti_type} fashion aesthetic" # Default
    if "KEYWORDS:" in content:
        try:
            # simple parsing logic
            parts = content.split("KEYWORDS:")[1].split("ADVICE:")[0]
            keywords = f"{mbti_type} fashion {parts.strip()}"
        except:
            pass
            
    # 3. Create a Clickable Image Search Link
    search_query = urllib.parse.quote(keywords)
    pinterest_url = f"https://www.pinterest.com/search/pins/?q={search_query}"
    google_url = f"https://www.google.com/search?tbm=isch&q={search_query}"
    
    # 4. Append the buttons to the text
    advice_part = content.split("ADVICE:")[-1].strip() if "ADVICE:" in content else content
    
    final_output = f"""
    {advice_part}
    
    ---
    ### 👗 See Examples
    * [Search on Pinterest]({pinterest_url})
    * [Search on Google Images]({google_url})
    """
    return final_output
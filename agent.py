import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. API Caller (Robust)
# ==========================================
def call_ollama_api(messages, api_key, base_url, model_name):
    # Ensure URL is clean
    base_url = base_url.rstrip('/')
    url = f"{base_url}/api/chat"
    
    headers = {"Content-Type": "application/json"}
    if api_key and api_key != "ollama":
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Payload setup
    payload = {
        "model": model_name, 
        "messages": messages, 
        "stream": False, 
        "options": {"temperature": 0.5} # Lower temp = more stable JSON
    }
    
    # Only add format: json for Llama3/Ollama local, sometimes NCKU doesn't support it
    if "ncku" not in base_url:
        payload["format"] = "json"

    try:
        print(f"📡 Sending request to {url} with model {model_name}...")
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200: 
            return response.json().get('message', {})
        else: 
            error_msg = f"Error {response.status_code}: {response.text}"
            print(f"❌ API Error: {error_msg}")
            return {"content": json.dumps({"error": error_msg})}
            
    except Exception as e: 
        print(f"❌ Connection Failed: {str(e)}")
        return {"content": json.dumps({"error": str(e)})}

# ==========================================
# 2. THE FIX: Powerful JSON Extractor
# ==========================================
def extract_json_from_text(text):
    """
    Cleans up the AI's messy response to find valid JSON.
    """
    try:
        # 1. Try simple parse first
        return json.loads(text)
    except:
        pass

    try:
        # 2. Remove Markdown code blocks (```json ... ```)
        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```', '', text)
        
        # 3. Find the first '{' and the last '}'
        # This ignores any "Here is your data:" text at the start
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            clean_text = match.group(1)
            return json.loads(clean_text)
            
        raise Exception("No JSON brackets found in response")
    except Exception as e:
        print(f"⚠️ JSON Parsing Failed. Raw text was:\n{text}\nError: {e}")
        return None

# ==========================================
# 3. Analysis Function
# ==========================================
def run_analysis_request(system_prompt, user_content, api_key, base_url, model_name):
    messages = [
        {"role": "system", "content": system_prompt}, 
        {"role": "user", "content": user_content}
    ]
    
    ai_msg = call_ollama_api(messages, api_key, base_url, model_name)
    content = ai_msg.get('content', '')
    
    # Check if API returned a hard error
    if 'error' in content and len(content) < 200:
        return {"error": content}

    # Attempt to extract
    result = extract_json_from_text(content)
    
    if result:
        return result
    else:
        # Return a dummy error structure so the UI shows something useful
        return {"error": "Could not parse JSON", "raw_output": content}

# ==========================================
# 4. Chat Function
# ==========================================
# ==========================================
# 4. Chat Function (Fixed for Compatibility Charts)
# ==========================================
# ==========================================
# 4. Chat Function (Smart Logic)
# ==========================================
# ==========================================
# 4. Chat Function (Strict Python Control)
# ==========================================
def generate_chat_response(user_input, chat_history, context_results, api_key, base_url, model_name, is_chinese_func):
    # --- 1. PYTHON DECISION LAYER (Instant & Accurate) ---
    # Check if the USER wants a chart. If so, don't even bother the AI.
    user_lower = user_input.lower()
    chart_keywords = ["chart", "graph", "plot", "visual", "drawing", "picture", "matrix", "diagram"]
    
    # If user explicitly asks for visual, trigger immediately
    if any(keyword in user_lower for keyword in chart_keywords):
        return "TOOL:CHART", None

    # --- 2. AI TEXT GENERATION LAYER ---
    # If we get here, the user wants TEXT. We will strictly ask for text.
    
    names = [r['name'] for r in context_results]
    
    # Notice: I REMOVED the instructions about "TOOL:CHART". 
    # The AI now doesn't even know charts exist, so it MUST write text.
    system_prompt = f"""
    You are an MBTI Consultant. 
    Users: {", ".join(names)}
    Data: {json.dumps(context_results)}
    
    INSTRUCTIONS:
    1. Answer the user's question based on the personality data.
    2. Keep your answer concise (under 3 sentences if possible).
    3. Use direct, plain text. Do NOT output JSON.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history (Limit to last 3 to make it FASTER)
    for msg in chat_history[-3:]:
        if msg["role"] in ["user", "assistant"]:
            # Filter out previous chart triggers from history so AI doesn't copy them
            if "📊" not in msg["content"] and "TOOL:CHART" not in msg["content"]: 
                messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": user_input})
    
    # Call API
    ai_msg = call_ollama_api(messages, api_key, base_url, model_name)
    content = ai_msg.get('content', '')
    
    # --- 3. FINAL CLEANUP ---
    # Just in case the AI tries to be smart and outputs code, we strip it.
    clean_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    clean_content = clean_content.strip()
    
    if not clean_content:
        return "I'm pondering that... could you ask in a different way?", None
        
    return clean_content, None
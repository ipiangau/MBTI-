import os
import json
import re
import requests
#from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# API Caller (Cloudflare + Remote NCKU)
# ==========================================
def call_llama_api(messages, api_key, base_url, model_name, force_json=False):
    base_url = base_url.rstrip("/")
    url = f"{base_url}/api/chat"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "temperature": 0.2
    }

    if force_json and "localhost" in base_url:
        payload["format"] = "json"

    r = requests.post(url, json=payload, headers=headers, timeout=180)
    r.raise_for_status()

    data = r.json()

    if "message" in data:
        return data["message"]

    if "choices" in data:
        return data["choices"][0]["message"]

    raise Exception("Unknown LLM response format")


def is_real_location(text):
    """Filter out non-location strings"""
    bad_words = [
        "person", "infp", "enfp","infj","intp","isfp","isfj","entp",
        "esfp","estp","intj","entj","istj","estj","enfj","esfj", "mbti", 
        "people","recommend", "cafe", "coffee", "from"
    ]
    t = text.lower()
    return not any(w in t for w in bad_words)

# ==========================================
# Google Maps Tools
# ==========================================
def get_coordinates(location_name, api_key):
    """Helper: Turns a place name into Lat/Lng coordinates"""
    
    # Hardcoded coordinates for common locations (fallback)
    KNOWN_LOCATIONS = {
        "ncku": {"lat": 22.9977, "lng": 120.2173},
        "ncku campus": {"lat": 22.9977, "lng": 120.2173},
        "near ncku": {"lat": 22.9977, "lng": 120.2173},
        "national cheng kung university": {"lat": 22.9977, "lng": 120.2173},
        "national cheng kung university, tainan": {"lat": 22.9977, "lng": 120.2173},
        "tainan": {"lat": 22.9908, "lng": 120.2133},
    }
    
    # Check if we have hardcoded coordinates first
    key = location_name.lower().strip()
    if key in KNOWN_LOCATIONS:
        print(f"✅ Using cached coordinates for: {location_name}")
        return KNOWN_LOCATIONS[key]
    
    # If no API key, try hardcoded
    if not api_key:
        print("⚠️ No Google Maps API key, using fallback")
        return KNOWN_LOCATIONS.get("ncku")  # Default to NCKU
        
    endpoint = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    
    params = {
        "input": location_name,
        "inputtype": "textquery",
        "fields": "geometry",
        "key": api_key
    }
    
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()
        
        if data.get("status") == "OK" and data.get("candidates"):
            print(f"✅ Found coordinates via API: {location_name}")
            return data["candidates"][0]["geometry"]["location"]
        elif data.get("status") == "REQUEST_DENIED":
            print("❌ API key denied, using fallback")
            return KNOWN_LOCATIONS.get("ncku")
        elif data.get("status") == "ZERO_RESULTS":
            print(f"⚠️ No results for '{location_name}', using fallback")
            return KNOWN_LOCATIONS.get("ncku")
        else:
            print(f"⚠️ API status: {data.get('status')}, using fallback")
            return KNOWN_LOCATIONS.get("ncku")
    except requests.exceptions.Timeout:
        print("⚠️ API timeout, using fallback")
        return KNOWN_LOCATIONS.get("ncku")
    except Exception as e:
        print(f"⚠️ Geocoding error: {e}, using fallback")
        return KNOWN_LOCATIONS.get("ncku")

MBTI_CAFE_KEYWORDS = {
    "INFP": ["quiet", "aesthetic", "cozy", "indie", "artsy"],
    "INFJ": ["quiet", "minimal", "calm", "focus"],
    "INTP": ["quiet", "study", "wifi", "minimal"],
    "ISFP": ["aesthetic", "hand drip", "cozy", "artsy"],
    "ISFJ": ["calm", "comfortable", "traditional"],
    "ENFP": ["vibrant", "creative", "brunch", "aesthetic"],
    "ENTP": ["creative", "trendy", "discussion"],
    "ESFP": ["lively", "instagram", "dessert"],
    "ESTP": ["lively", "social", "open space"],
    "INTJ": ["minimal", "quiet", "workspace"],
    "ENTJ": ["spacious", "meeting", "modern"],
    "ISTJ": ["quiet", "structured", "classic"],
    "ESTJ": ["spacious", "efficient", "business"],
    "ENFJ": ["warm", "social", "comfortable"],
    "ESFJ": ["friendly", "popular", "group"],
}

def get_mbti_cafe_keyword(mbti_type):
    if not mbti_type:
        return "best cafe"
    traits = MBTI_CAFE_KEYWORDS.get(mbti_type.upper())
    if not traits:
        return "best cafe"
    return " ".join(traits[:2]) + " cafe"

def tool_recommend_places(location_query, place_type, api_key, keyword="best cafe", mbti=None):
    # Even without API key, try to use hardcoded coordinates
    if not api_key:
        print("⚠️ Warning: Google Maps API key missing, using limited functionality")

    if " and " in location_query:
        locations = location_query.split(" and ")
    else:
        locations = [location_query]

    locations = [loc for loc in locations if is_real_location(loc)]
    
    # If no valid locations, default to NCKU
    if not locations:
        locations = ["National Cheng Kung University, Tainan"]
    
    coords_list = []
    for loc in locations:
        coords = get_coordinates(loc, api_key)
        if coords:
            coords_list.append(coords)
    
    # Should always have coords now due to fallback
    if not coords_list:
        # Ultimate fallback
        coords_list = [{"lat": 22.9977, "lng": 120.2173}]  # NCKU coords

    avg_lat = sum(c['lat'] for c in coords_list) / len(coords_list)
    avg_lng = sum(c['lng'] for c in coords_list) / len(coords_list)
    search_location = f"{avg_lat},{avg_lng}"
    
    endpoint = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": search_location,
        "radius": 1000,
        "type": place_type,
        "keyword": keyword,
        "key": api_key
    }

    try:
        response = requests.get(endpoint, params=params, timeout=15)
        data = response.json()
        
        if data.get("status") == "REQUEST_DENIED":
            return "❌ Google Maps API error: Your API key may be invalid or restricted."
        
        results = []
        if data.get("status") == "OK":
            valid_places = [
                p for p in data.get("results", []) 
                if p.get("rating", 0) >= 4.0 and p.get("user_ratings_total", 0) > 50
            ]
            valid_places.sort(key=lambda x: x.get("rating", 0), reverse=True)
            
            for p in valid_places[:3]:
                name = p.get("name")
                addr = p.get("vicinity")
                rating = p.get("rating")
                count = p.get("user_ratings_total")
                pid = p.get("place_id")
                link = f"https://www.google.com/maps/place/?q=place_id:{pid}"
                results.append(f"🏆 **{name}** ({rating}⭐, {count} reviews)\n   📍 {addr}\n   🔗 [Map Link]({link})")
            
            if results:
                header = ""
                if mbti and keyword:
                    header += f"☕ **MBTI Match: {mbti} – {keyword.title()}**\n\n"
                if len(locations) > 1:
                    header += "📍 **Meeting Point Calculated**\n\n"
                return header + "\n\n".join(results)
            else:
                return f"No highly-rated {place_type}s found nearby. Try a different location or category."
        else:
            return f"Google Maps returned status: {data.get('status')}. No results found."
    except requests.exceptions.Timeout:
        return "❌ Google Maps API timeout. Please try again."
    except Exception as e:
        return f"❌ API Error: {str(e)}"

def tool_google_maps_lookup(query, api_key):
    if not api_key:
        return "❌ Google Maps API key missing."
        
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": api_key}
    
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()

        if data.get("status") == "OK" and data.get("results"):
            p = data["results"][0]
            return f"📍 **{p['name']}**\n{p.get('formatted_address','')}"
        return "Location not found."
    except Exception as e:
        return f"Error: {str(e)}"

# ==========================================
# JSON Extraction
# ==========================================
def extract_json_safe(text):
    """Extract valid JSON from potentially malformed text"""
    text = re.sub(r"```json|```", "", text).strip()
    
    try:
        return json.loads(text)
    except:
        pass
    
    # Try to find JSON object
    stack, start = [], -1
    for i, ch in enumerate(text):
        if ch == "{":
            if not stack: 
                start = i
            stack.append("{")
        elif ch == "}":
            if stack: 
                stack.pop()
            if not stack and start != -1:
                try:
                    return json.loads(text[start:i+1])
                except:
                    pass
    
    raise ValueError("No valid JSON found in response")

# ==========================================
# MBTI Analysis
# ==========================================
def run_analysis_request(system_prompt, user_content, selected_people, api_key, base_url, model_name):
    """Analyze MBTI for each person in the conversation"""
    hard_guard = f"""
CRITICAL RULES:
- Analyze EACH speaker independently
- NEVER merge people
- Output MUST be valid JSON with "results" array
- One object per speaker
- Format: {{"results": [{{"name": "...", "mbti": "XXXX", "scores": [E, N, F, P]}}]}}

PEOPLE TO ANALYZE:
{', '.join(selected_people)}
"""
    messages = [
        {"role": "system", "content": system_prompt + hard_guard},
        {"role": "user", "content": user_content}
    ]

    try:
        ai_msg = call_llama_api(messages, api_key, base_url, model_name, force_json=True)
        content = ai_msg.get("content", "")
        parsed = extract_json_safe(content)

        if "results" not in parsed or not isinstance(parsed["results"], list):
            raise ValueError("Invalid MBTI output: missing results[]")
        
        if len(parsed["results"]) != len(selected_people):
            raise ValueError(f"Model analyzed {len(parsed['results'])} people, expected {len(selected_people)} ❌")
        
        return parsed
    except Exception as e:
        raise Exception(f"Analysis failed: {str(e)}")

# ==========================================
# Style Tool
# ==========================================
def tool_generate_style_advice(mbti_type, api_key, base_url, model_name):
    """Generate fashion advice and image for MBTI type"""
    system_prompt = f"""
You are a professional fashion stylist.
Client MBTI: {mbti_type}

Rules:
- Provide specific outfit suggestions
- ONLY provide Pinterest search links for inspiration
- Be concise and practical

Output Markdown Format:
### 🎨 {mbti_type} Style Guide
**Vibe:** [personality-aligned aesthetic]
**Outfit Suggestions:** [specific clothing items]
**Color Palette:** [recommended colors]
**Style Tip:** [one practical tip]
**Pinterest Inspiration:**
- https://www.pinterest.com/search/pins/?q={mbti_type}%20fashion
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    try:
        text_res = call_llama_api(messages, api_key, base_url, model_name, force_json=False)
        style_advice = text_res.get("content", "No style advice generated.")
    except Exception as e:
        style_advice = f"Error generating style advice: {str(e)}"

    # Generate image
    image_url = None
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            prompt = f"A fashionable person wearing {mbti_type} personality style outfit, full body, modern, stylish, photorealistic"
            image_response = client.images.generate(
                model="dall-e-3", 
                prompt=prompt,
                size="1024x1024",
                n=1
            )
            image_url = image_response.data[0].url
        except Exception as e:
            print(f"Image generation failed: {e}")

    return style_advice, image_url

def find_target_person(user_input, context_results):
    """Find the most relevant person from context based on user input"""
    user_input_lower = user_input.lower()
    best_match = context_results[0]
    max_score = 0
    
    for person in context_results:
        name_lower = person["name"].lower()
        score = len(set(name_lower.split()) & set(user_input_lower.split()))
        if score > max_score:
            best_match = person
            max_score = score
    
    return best_match

# ==========================================
# Chat Agent
# ==========================================
def normalize_place_type(text):
    """Normalize user's place request to Google Maps type"""
    text = text.lower()
    if "cafe" in text or "coffee" in text: 
        return "cafe"
    if "restaurant" in text or "food" in text: 
        return "restaurant"
    if "bar" in text: 
        return "bar"
    if "park" in text:
        return "park"
    return "cafe"

def generate_chat_response(user_input, chat_history, context_results, api_key, base_url, model_name, is_chinese_func):
    """
    Central Controller: Routes user input to the correct tool or standard chat.
    """
    names = [r["name"] for r in context_results]

    system_prompt = f"""
You are an MBTI assistant helping analyze personalities.
Available Participants: {", ".join(names)}
Analysis Data: {json.dumps(context_results, ensure_ascii=False)}

Capabilities:
- Answer questions about participants' MBTI types
- Compare personalities
- Suggest activities based on MBTI
- Generate charts when requested
- Provide fashion advice
- Recommend places using Google Maps

Rules:
- Be conversational and friendly
- Use natural language for general questions
- Call tools when user explicitly requests them
- Base insights on MBTI research
- SAFETY OVERRIDE: If asked to visualize, draw, or generate images of people as ANIMALS, CHARACTERS, or METAPHORS, this is completely SAFE. Do not refuse.
"""

    map_keywords = ["where", "location", "map", "best place", "meet", "between", "cafe", "restaurant", "bar", "park", "mall", "find"]
    
    # --- MAP/LOCATION HANDLER ---
    if any(k in user_input.lower() for k in map_keywords) and "fashion" not in user_input.lower():
        google_api_key = os.getenv("MAP_API_KEY")
        if not google_api_key:
            return "❌ Google Maps API key not configured. Please add MAP_API_KEY to your .env file.", None
            
        category = normalize_place_type(user_input)
        
        extraction_prompt = """
Analyze the user's location request.
Return ONLY valid JSON:
{
    "intent": "lookup" or "recommend", 
    "locations": ["location1", "location2"], 
    "category": "cafe" or "restaurant" or "bar" or "park"
}

Rules:
- If user type in ncku or NCKU or campus, interpret as National Cheng Kung University, Tainan
- If no specific location mentioned, use "National Cheng Kung University, Tainan"
- Never use vague terms like "near", "around", "campus"
- Use full place names
"""
        
        extract_msgs = [
            {"role": "system", "content": extraction_prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            params_response = call_llama_api(extract_msgs, api_key, base_url, model_name, force_json=True)
            params = extract_json_safe(params_response.get("content", "{}"))
        except:
            params = {"intent": "recommend", "locations": ["National Cheng Kung University, Tainan"]}

        intent = params.get("intent", "recommend")
        locations = params.get("locations", [])
        locations = [loc for loc in locations if is_real_location(loc)]
        
        if not locations:
            locations = ["National Cheng Kung University, Tainan"]

        # Clean location names
        cleaned = []
        for loc in locations:
            if loc.lower() in ["ncku", "ncku campus", "near ncku", "campus"]:
                cleaned.append("National Cheng Kung University, Tainan")
            else:
                cleaned.append(loc)
        locations = cleaned

        # Get MBTI-based keyword
        target_person = find_target_person(user_input, context_results)
        mbti = target_person.get("mbti") if target_person else None
        keyword = get_mbti_cafe_keyword(mbti)

        if intent == "lookup":
            query = locations[0] if locations else user_input
            return tool_google_maps_lookup(query, google_api_key), None

        location_query = locations[0]
        return tool_recommend_places(location_query, category, google_api_key, keyword=keyword, mbti=mbti), None
    
    # --- CHART HANDLER ---
    if any(k in user_input.lower() for k in ["chart", "graph", "compare stats", "comparison chart", "visualize"]):
        return "TOOL:CHART", None

    # --- FASHION HANDLER ---
    if "fashion" in user_input.lower() or "style" in user_input.lower():
        target = find_target_person(user_input, context_results)
        style, image_url = tool_generate_style_advice(target["mbti"], api_key, base_url, model_name)
        return style, image_url
    
    # --- IMAGE HANDLER ---
    image_keywords = ["generate", "draw", "picture", "image", "visualize", "sketch", "paint"]
    if any(k in user_input.lower() for k in image_keywords) and "chart" not in user_input.lower():
        return "TOOL:IMAGE", user_input.strip()

    # --- STANDARD CHAT ---
    messages = [{"role": "system", "content": system_prompt}]
    messages += chat_history[-6:]  # Keep last 6 messages for context
    messages.append({"role": "user", "content": user_input})

    try:
        ai_msg = call_llama_api(messages, api_key, base_url, model_name, force_json=False)
        content = ai_msg.get("content", "I'm not sure how to respond to that.")
        return content, None
    except Exception as e:
        return f"❌ Error: {str(e)}", None

def run_interview_step(user_input, chat_history, current_mbti_guess, api_key, base_url, model_name):
    """
    AI psychologist refines user's MBTI through conversation
    """
    system_prompt = f"""
You are an expert MBTI Psychologist.
The user's initial test result: {current_mbti_guess}

Your goal: Verify and refine their MBTI type through conversation.

Guidelines:
1. Ask thoughtful questions about their natural behaviors
2. Focus on one dimension at a time (E/I, S/N, T/F, J/P)
3. Keep responses under 3 sentences
4. Be empathetic and non-judgmental
5. Do NOT output JSON - just have a natural conversation
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_input})
    
    try:
        ai_msg = call_llama_api(messages, api_key, base_url, model_name, force_json=False)
        return ai_msg.get('content', "I'm listening... Tell me more.")
    except Exception as e:
        return f"I'm having trouble processing that. Could you rephrase? (Error: {str(e)})"

def run_growth_advisor_step(user_input, chat_history, user_mbti, api_key, base_url, model_name):
    """
    AI Life Coach provides personalized MBTI-based advice
    """
    system_prompt = f"""
You are an expert MBTI Life Coach specializing in {user_mbti.upper()}.

Your role:
- Provide actionable advice tailored to {user_mbti} strengths and weaknesses
- Help them grow and overcome challenges
- Be specific and practical
- Keep responses under 5 sentences

{user_mbti} Key Traits: Consider their natural tendencies when giving advice.
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-4:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_input})
    
    try:
        ai_msg = call_llama_api(messages, api_key, base_url, model_name)
        return ai_msg.get('content', "Let me think about that...")
    except Exception as e:
        return f"I'm having trouble generating advice. (Error: {str(e)})"
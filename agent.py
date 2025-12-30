import os
import json
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# API Caller (Remote NCKU + Local Ollama)
# ==========================================
def call_ollama_api(messages, api_key, base_url, model_name,force_json=False):
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
    bad_words = [
        "person", "infp", "enfp","infj","intp","isfp","isfj","entp",
        "esfp","estp","intj","entj","istj","estj","enfj","esfj", "mbti", 
        "people","recommend", "cafe", "coffee", "from"
    ]
    t = text.lower()
    return not any(w in t for w in bad_words)

# ==========================================
# Google Maps Tools (Upgraded)
# ==========================================
def get_coordinates(location_name, api_key):
    """Helper: Turns a place name into Lat/Lng coordinates"""
    endpoint = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": location_name,
        "inputtype": "textquery",
        "fields": "geometry",
        "key": api_key
    }
    aliases = {
        "ncku": "National Cheng Kung University, Tainan",
        "ncku campus": "National Cheng Kung University, Tainan",
        "near ncku": "National Cheng Kung University, Tainan"
    }
    key = location_name.lower().strip()
    if key in aliases:
        location_name = aliases[key]
    try:
        r = requests.get(endpoint, params=params)
        data = r.json()
        if data.get("status") == "OK" and data.get("candidates"):
            return data["candidates"][0]["geometry"]["location"] # Returns {'lat': ..., 'lng': ...}
    except:
        pass
    return None

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

    # Google prefers short phrases
    return " ".join(traits[:2]) + " cafe"

def tool_recommend_places(location_query, place_type, api_key,keyword="best cafe",mbti=None):
    """
    Finds highly-rated places near a specific location or multiple locations (midpoint).
    location_query: Can be a single string "Central Park" or a list ["Central Park", "Empire State"]
    """
    if not api_key:
        return "Error: Google Maps API key is missing."

    # 1. HANDLE MEETING IN THE MIDDLE
    # If the user provided multiple locations (split by ' and ' or just passed a list)
    if " and " in location_query:
        locations = location_query.split(" and ")
    else:
        locations = [location_query]

    #ignore fake locations
    locations = [loc for loc in locations if is_real_location(loc)]

    # Get coords for all points
    coords_list = []
    for loc in locations:
        coords = get_coordinates(loc, api_key)
        if coords:
            coords_list.append(coords)
    
    if not coords_list:
        return "Could not find coordinates for the provided locations."

    # Calculate Midpoint (Average Lat/Lng)
    avg_lat = sum(c['lat'] for c in coords_list) / len(coords_list)
    avg_lng = sum(c['lng'] for c in coords_list) / len(coords_list)
    search_location = f"{avg_lat},{avg_lng}"
    
    # 2. SEARCH NEARBY (Places API)
    endpoint = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": search_location,
        "radius": 1000,
        "type": place_type,
        "keyword": keyword,
        "key": api_key
    }

    try:
        response = requests.get(endpoint, params=params)
        data = response.json()
        
        results = []
        if data.get("status") == "OK":
            # Filter: Rating > 4.0 and at least 50 reviews
            valid_places = [
                p for p in data.get("results", []) 
                if p.get("rating", 0) >= 4.0 and p.get("user_ratings_total", 0) > 50
            ]
            
            # Sort by rating
            valid_places.sort(key=lambda x: x.get("rating", 0), reverse=True)
            
            # Get top 3
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

                # MBTI header
                if mbti and keyword:
                    header += f"☕ **MBTI Match: {mbti} – {keyword.title()}**\n\n"

                # Midpoint header
                if len(locations) > 1:
                    header += "📍 **Meeting Point Calculated**\n\n"

                return header + "\n\n".join(results)

            else:
                return "No highly-rated places found nearby."
    except Exception as e:
        return f"API Error: {str(e)}"
        
    return "No results."

def tool_google_maps_lookup(query, api_key):
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": api_key}
    r = requests.get(endpoint, params=params)
    data = r.json()

    if data.get("status") == "OK" and data.get("results"):
        p = data["results"][0]
        return f"{p['name']} – {p.get('formatted_address','')}"
    return "Location not found."

# ==========================================
# STRICT JSON Extraction
# ==========================================
def extract_json_safe(text):
    text = re.sub(r"```json|```", "", text).strip()

    try:
        obj = json.loads(text)
        return obj
    except:
        pass

    # fallback bracket matching
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
                return json.loads(text[start:i+1])


    raise ValueError("No valid JSON found")

# ==========================================
# MBTI Analysis (GROUP SAFE)
# ==========================================
def run_analysis_request(system_prompt, user_content, selected_people, api_key, base_url, model_name):
    # Force LLM to analyze only selected people
    hard_guard = f"""
CRITICAL RULES:
- Analyze EACH speaker independently
- NEVER merge people
- NEVER output a single person only
- Output MUST be valid JSON
- JSON MUST contain "results" array
- One object per speaker

ALWAYS ANALYZE THESE PEOPLE:
{', '.join(selected_people)}
"""

    messages = [
        {"role": "system", "content": system_prompt + hard_guard},
        {"role": "user", "content": user_content}
    ]

    ai_msg = call_ollama_api(messages, api_key, base_url, model_name,force_json=True)
    content = ai_msg.get("content", "")
    parsed = extract_json_safe(content)

    # HARD VALIDATION
    if "results" not in parsed or not isinstance(parsed["results"], list):
        raise ValueError("Invalid MBTI output: missing results[]")

    if len(parsed["results"]) != len(selected_people):
        raise ValueError(f"Model analyzed {len(parsed['results'])} people, expected {len(selected_people)} ❌")

    return parsed

# ==========================================
# Style Tool (TEXT ONLY – Pinterest Ref)
# ==========================================
def tool_generate_style_advice(mbti_type, api_key, base_url, model_name):
    system_prompt = f"""
You are a professional fashion stylist.
Client MBTI: {mbti_type}

Rules:
- Pinterest is ONLY a reference
- ONLY provide Pinterest search links

Output Markdown:
### 🎨 {mbti_type} Style
**Vibe:** ...
**Outfit:** ...
**Colors:** ...
**Tip:** ...
**Pinterest References:**
- https://www.pinterest.com/search/pins/?q={mbti_type}%20fashion
"""
    messages = [{"role": "system", "content": system_prompt}]
    text_res = call_ollama_api(messages, api_key, base_url, model_name,force_json=False)
    style_advice = text_res.get("content", "")

    # --- OpenAI image generation ---
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"A full body of person with an outfit of {mbti_type} style, stylish, colorful, realistic"

    image_response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )
    image_url = image_response.data[0].url

    # Return both style advice and image URL
    return style_advice, image_url

def find_target_person(user_input, context_results):
    user_input_lower = user_input.lower()
    best_match = context_results[0]  # fallback

    max_score = 0
    for person in context_results:
        name_lower = person["name"].lower()
        # simple substring match score
        score = len(set(name_lower.split()) & set(user_input_lower.split()))
        if score > max_score:
            best_match = person
            max_score = score

    return best_match
# ==========================================
# Chat Agent
# ==========================================
def normalize_place_type(text):
    text = text.lower()
    if "cafe" in text or "coffee" in text:
        return "cafe"
    if "restaurant" in text or "food" in text:
        return "restaurant"
    if "bar" in text:
        return "bar"
    return "cafe"   # default

def generate_chat_response(user_input, chat_history, context_results,api_key, base_url, model_name, is_chinese_func):
    """
    Central Controller: Routes user input to the correct tool or standard chat.
    """
    DEFAULT_LOCATION = "National Cheng Kung University, Tainan"
    names = [r["name"] for r in context_results]

    # --- 1. SYSTEM PROMPT FOR REGULAR CHAT ---
    system_prompt = f"""
You are an MBTI assistant.
Participants: {", ".join(names)}
Data: {json.dumps(context_results)}

Rules:
- If the question is hypothetical, playful, or conversational (e.g. "who would win in a fight"),
  answer in natural language
- Charts ONLY when user asks for chart/graph/statistics
- If user asks for generating images → respond TOOL:IMAGE
- If user asks for fashion → call tool_generate_style_advice()
- If user asks for charts → respond TOOL:CHART
- if user asks for map/location → call Google Maps tools
- If user asks about a specific person → answer based on their data
- If user asks for places recommenation for a person → use their MBTI to suggest places
"""

    map_keywords = ["where", "location", "map", "best place", "meet", "between", "cafe", "restaurant", "bar", "park", "mall"]
    
    if any(k in user_input.lower() for k in map_keywords)and "fashion" not in user_input.lower():
        google_api_key = os.getenv("MAP_API_KEY")
        category = normalize_place_type(user_input)
        
        #results_text = tool_recommend_places(location_query, category, google_api_key)
        
        extraction_prompt = """
        Analyze the user's request for location services.
        Return ONLY valid JSON with this structure:
        {
            "intent": "lookup" or "recommend", 
            "locations": ["location1", "location2"], 
            "category": "restaurant" (default) or "cafe" or "bar" or "park" or "mall"
        }
        If the user does not specify a clear place name, 
        use exactly: "National Cheng Kung University, Tainan".
        Never output vague locations like "near", "campus", or "around".
        Example: "Meet halfway between Tokyo and Osaka for coffee" -> {"intent": "recommend", "locations": ["Tokyo", "Osaka"], "category": "cafe"}
        Example: "Where is Central Park?" -> {"intent": "lookup", "locations": ["Central Park"], "category": "general"}
        """
        
        extract_msgs = [
            {"role": "system", "content": extraction_prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            params = call_ollama_api(extract_msgs, api_key, base_url, model_name, force_json=True)
            if isinstance(params, str):
                params = extract_json_safe(params)
        except:
            params = {"locations": [user_input]}

        intent = params.get("intent", "recommend")
        locations = params.get("locations", [])

        # filter fake locations
        locations = [loc for loc in locations if is_real_location(loc)]
        
        if not locations:
            locations = ["National Cheng Kung University, Tainan"]

        cleaned = []
        for loc in locations:
            if loc.lower() in ["ncku", "ncku campus", "near ncku", "campus"]:
                cleaned.append("National Cheng Kung University, Tainan")
            else:
                cleaned.append(loc)

        locations = cleaned
        target_person = find_target_person(user_input, context_results)
        mbti = target_person.get("mbti") if target_person else None
        keyword = get_mbti_cafe_keyword(mbti)

        if intent == "lookup":
            query = locations[0] if locations else user_input
            return tool_google_maps_lookup(query, google_api_key), None

        # Single-location recommend
        location_query = locations[0]
        return tool_recommend_places(location_query,category,google_api_key,keyword=keyword,mbti=mbti), None
    # --- 3. CHART HANDLER ---
    chart_keywords = ["chart", "graph", "compare stats", "comparison chart"]
    if any(k in user_input.lower() for k in chart_keywords):
        return "TOOL:CHART", None

    # --- 4. FASHION HANDLER ---
    
    if "fashion" in user_input.lower():
        target = find_target_person(user_input, context_results)
        # Fallback loop to find specific mentioned name
        for p in context_results:
            if p["name"].lower() in user_input.lower():
                target = p
                break

        style, image_url = tool_generate_style_advice(
            target["mbti"], api_key, base_url, model_name
        )
        return style, image_url
    
    # --- 4. IMAGE HANDLER (generic) ---
    image_keywords = [
        "generate image", "generate a picture", "draw", "show me a picture",
        "create an image", "make an image", "picture of", "image of"
    ]

    if any(k in user_input.lower() for k in image_keywords):
        # Return TOOL signal + prompt
        image_prompt = user_input.strip()
        return "TOOL:IMAGE", image_prompt


    # --- 5. STANDARD CHAT HANDLER ---
    messages = [{"role": "system", "content": system_prompt}]
    messages += chat_history
    messages.append({"role": "user", "content": user_input})

    ai_msg = call_ollama_api(messages, api_key, base_url, model_name, force_json=False)
    content = ai_msg.get("content", "")

    return content, None

def run_interview_step(user_input, chat_history, current_mbti_guess, api_key, base_url, model_name):
    """
    The AI acts as a psychologist to refine the user's MBTI.
    """
    system_prompt = f"""
    You are an expert MBTI Psychologist.
    The user just took a quiz and got: {current_mbti_guess}.
    
    GOAL: Have a conversation to verify if this result is accurate.
    1. Ask probing questions about their habits, stress, and energy.
    2. Keep responses short (max 2 sentences).
    3. Be friendly and empathetic.
    4. Do NOT output JSON. Just chat.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add recent history
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": user_input})
    
    ai_msg = call_ollama_api(messages, api_key, base_url, model_name)
    return ai_msg.get('content', "I'm listening...")
# ==========================================
# 6. Growth Coach Function 
# ==========================================
def run_growth_advisor_step(user_input, chat_history, user_mbti, api_key, base_url, model_name):
    """
    AI acts as a Life Coach specific to the user's MBTI type.
    """
    system_prompt = f"""
    You are an expert MBTI Life Coach. 
    The user is: {user_mbti.upper()}.
    
    GOAL: Help them improve based on the strengths/weaknesses of {user_mbti}.
    
    INSTRUCTIONS:
    1. If the user asks for advice, give 3 concrete, actionable tips.
    2. If the user asks about a situation (e.g., "Job Interview", "First Date"), 
       tell them exactly how an {user_mbti} should handle it to succeed.
    3. Keep the tone encouraging but practical.
    4. Keep answers concise (under 4 sentences).
    5. Do NOT output JSON.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add recent history (Limit to 4 to keep it fast)
    for msg in chat_history[-4:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": user_input})
    
    ai_msg = call_ollama_api(messages, api_key, base_url, model_name)
    return ai_msg.get('content', "I'm thinking of some advice...")
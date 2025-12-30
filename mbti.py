import re
import json

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
# 4. Prompt Constructor
# ==========================================
def construct_analysis_prompt(selected_speakers_data):
    conversation_sample = ""
    for name, text in selected_speakers_data.items():
        conversation_sample += f"Speaker [{name}]: {text[:600]}\n\n"

    system_prompt = """
    You are an expert MBTI analyst.
    Task: Analyze the provided text samples for EACH speaker independently.
    Output JSON ONLY:
    { "results": [ { "name": "Name1", "mbti": "XXXX", "scores": [10, 20, 30, 40] } ] }
    """
    return system_prompt, conversation_sample
def get_quiz_questions():
    """Returns a list of 12 quick questions."""
    return [
        {"id": 1, "txt": "I feel energized after being around a lot of people.", "dim": "E", "rev": False},
        {"id": 2, "txt": "I often get lost in my thoughts and ignore my surroundings.", "dim": "N", "rev": False},
        {"id": 3, "txt": "I make decisions based on logic rather than feelings.", "dim": "T", "rev": False},
        {"id": 4, "txt": "I like to have a detailed plan before I start a trip.", "dim": "J", "rev": False},
        {"id": 5, "txt": "I prefer a quiet night in reading over a loud party.", "dim": "E", "rev": True}, # Introvert
        {"id": 6, "txt": "I trust concrete facts more than abstract theories.", "dim": "N", "rev": True}, # Sensing
        {"id": 7, "txt": "I am easily affected by other people's emotions.", "dim": "T", "rev": True}, # Feeling
        {"id": 8, "txt": "I prefer to keep my options open rather than committing.", "dim": "J", "rev": True}, # Perceiving
        {"id": 9, "txt": "I usually start conversations with strangers.", "dim": "E", "rev": False},
        {"id": 10, "txt": "I think about the future more than the present.", "dim": "N", "rev": False},
        {"id": 11, "txt": "Debates and intellectual arguments excite me.", "dim": "T", "rev": False},
        {"id": 12, "txt": "I get stressed when things are disorganized.", "dim": "J", "rev": False},
    ]

def calculate_quiz_result(answers):
    """
    answers: Dictionary {question_id: score (-2 to +2)}
    Returns: MBTI String (e.g., "ENTJ") and raw scores.
    """
    # Scores: E, N, T, J (Positive = Left side, Negative = Right side)
    # E vs I, N vs S, T vs F, J vs P
    dims = {"E": 0, "N": 0, "T": 0, "J": 0}
    
    questions = get_quiz_questions()
    
    for q in questions:
        val = answers.get(q['id'], 0)
        # If question is "Reverse" (e.g. Introvert question for E dim), flip sign
        if q['rev']: val = -val
        dims[q['dim']] += val

    # Determine Letters
    mbti = ""
    mbti += "E" if dims["E"] >= 0 else "I"
    mbti += "N" if dims["N"] >= 0 else "S"
    mbti += "T" if dims["T"] >= 0 else "F"
    mbti += "J" if dims["J"] >= 0 else "P"
    
    # Normalize for charts (0-100 scale)
    # Map range -6 to +6 -> 0 to 100
    def normalize(val):
        # -6 (Strong Right) -> 0
        # +6 (Strong Left) -> 100
        return int(((val + 6) / 12) * 100)

    scores = [
        normalize(dims["E"]), # E score
        normalize(dims["N"]), # N score
        normalize(dims["T"]), # T score
        normalize(dims["J"])  # J score
    ]
    
    return mbti, scores
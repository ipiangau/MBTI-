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
    """
    Adjusts scores to ensure they match the MBTI letter.
    Example: If type is 'INTJ', the 'I' score (index 0) must be < 50.
    """
    if not mbti_type or len(raw_scores) != 4:
        # Default neutral scores if data is missing
        return [50, 50, 50, 50]
    
    mbti = mbti_type.upper()
    corrected = list(raw_scores)
    
    # 0: Energy (I <-> E)
    if 'I' in mbti: corrected[0] = min(corrected[0], 45)  # Force Introvert
    elif 'E' in mbti: corrected[0] = max(corrected[0], 55) # Force Extravert
    
    # 1: Info (S <-> N)
    if 'S' in mbti: corrected[1] = min(corrected[1], 45)  # Force Sensing
    elif 'N' in mbti: corrected[1] = max(corrected[1], 55) # Force Intuition
    
    # 2: Decisions (T <-> F)
    if 'T' in mbti: corrected[2] = min(corrected[2], 45)  # Force Thinking
    elif 'F' in mbti: corrected[2] = max(corrected[2], 55) # Force Feeling
    
    # 3: Lifestyle (J <-> P)
    if 'J' in mbti: corrected[3] = min(corrected[3], 45)  # Force Judging
    elif 'P' in mbti: corrected[3] = max(corrected[3], 55) # Force Perceiving
    
    return corrected

# ==========================================
# 3. File Parser
# ==========================================
def parse_line_chat_dynamic(file_content):
    """
    Parses a Line chat export (.txt) into a dictionary of speakers.
    Returns: {'SpeakerName': 'All their messages combined...'}
    """
    lines = file_content.split('\n')
    messages = {}
    
    # Words to ignore to keep data clean
    skip_keywords = [
        "通話時間", "Call time", "Unsend message", "已收回訊息", 
        "joined the chat", "invite", "加入聊天", "invited", "邀請"
    ]
    invalid_names = ["You", "you", "System", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for line in lines:
        line = line.strip()
        if not line: continue

        # 1. Try Tab Split (Standard Line Export)
        parts = line.split('\t')
       
        # 2. If no tabs, try Space Split (Common copy-paste format)
        if len(parts) < 3:
            parts = line.split(' ', 2)

        if len(parts) >= 3:
            time_str = parts[0]
            name = parts[1].strip()
            msg = parts[2].strip()

            # Verify it starts with a time (e.g., 14:02)
            if not re.match(r'^\d{1,2}:\d{2}$', time_str):
                continue
           
            # Clean up names
            if name.endswith(" Photos"): name = name.replace(" Photos", "")
            if name.endswith(" Stickers"): name = name.replace(" Stickers", "")

            # Filter out junk messages
            if any(k in msg for k in skip_keywords): continue
            if msg == "[Photos]" or msg == "[Stickers]": continue
            if name in invalid_names: continue

            # Append message to that speaker
            if name not in messages: messages[name] = []
            messages[name].append(msg)
           
    # Only keep speakers who have spoken at least 3 times
    valid_speakers = {k: "\n".join(v) for k, v in messages.items() if len(v) >= 3}
    return valid_speakers

# ==========================================
# 4. Prompt Constructor
# ==========================================
def construct_analysis_prompt(selected_speakers_data):
    """
    Builds the prompt that tells the AI what to do.
    """
    conversation_sample = ""
    for name, text in selected_speakers_data.items():
        # Limit text to 600 chars per person to save tokens
        conversation_sample += f"Speaker [{name}]: {text[:600]}\n\n"  

    system_prompt = """
    You are an expert MBTI analyst.
    Task: Analyze the provided text samples for EACH speaker independently.
   
    For EACH speaker, determine:
    1. MBTI Type (e.g., INTJ, ENFP).
    2. Intensity Scores (0-100) for the 4 dimensions:
       - Energy (I <30 ... E >70)
       - Information (S <30 ... N >70)
       - Decisions (T <30 ... F >70)
       - Lifestyle (J <30 ... P >70)

    【Output Format (JSON ONLY)】
    {
        "results": [
            { "name": "Name1", "mbti": "XXXX", "scores": [10, 20, 30, 40] },
            { "name": "Name2", "mbti": "XXXX", "scores": [80, 90, 10, 50] }
        ]
    }
    """
    
    return system_prompt, conversation_sample
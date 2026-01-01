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
    """
    Returns a list of 28 questions with English (txt_en) and Mandarin (txt_cn).
    """
    return [
        # --- E vs I ---
        {"id": 1, "txt_en": "You regularly make new friends.", "txt_cn": "你经常结交新朋友。", "dim": "E", "rev": False},
        {"id": 2, "txt_en": "You feel comfortable starting a conversation with someone interesting.", "txt_cn": "你很容易跟陌生人开启话题。", "dim": "E", "rev": False},
        {"id": 3, "txt_en": "You enjoy participating in group activities.", "txt_cn": "你喜欢参加团体活动。", "dim": "E", "rev": False},
        {"id": 4, "txt_en": "You feel drained after being around a lot of people for a long time.", "txt_cn": "在人群中待久了你会感到精疲力尽。", "dim": "E", "rev": True},
        {"id": 5, "txt_en": "You avoid making phone calls.", "txt_cn": "你尽量避免打电话。", "dim": "E", "rev": True},
        {"id": 6, "txt_en": "You prefer to do your chores alone rather than with others.", "txt_cn": "你宁愿独自做事，也不愿与他人合作。", "dim": "E", "rev": True},
        {"id": 7, "txt_en": "At social events, you rarely try to introduce yourself to new people.", "txt_cn": "在社交场合，你很少主动介绍自己。", "dim": "E", "rev": True},

        # --- N vs S ---
        {"id": 8, "txt_en": "You often get so lost in thoughts that you ignore your surroundings.", "txt_cn": "你经常沉浸在思考中而忽略周围环境。", "dim": "N", "rev": False},
        {"id": 9, "txt_en": "You are intrigued by controversial or theoretical topics.", "txt_cn": "你对有争议或理论性的话题很感兴趣。", "dim": "N", "rev": False},
        {"id": 10, "txt_en": "You enjoy thinking about complex, abstract theories.", "txt_cn": "你喜欢思考复杂抽象的理论。", "dim": "N", "rev": False},
        {"id": 11, "txt_en": "You often think about 'what if' scenarios.", "txt_cn": "你经常思考“如果……会怎样”的情境。", "dim": "N", "rev": False},
        {"id": 12, "txt_en": "You prefer to follow a schedule rather than do things spontaneously.", "txt_cn": "你更喜欢按计划行事，而不是随兴而为。", "dim": "N", "rev": True}, 
        {"id": 13, "txt_en": "You trust concrete facts and data more than intuition.", "txt_cn": "相比直觉，你更相信具体的事实和数据。", "dim": "N", "rev": True}, 
        {"id": 14, "txt_en": "You prefer practical solutions over creative concepts.", "txt_cn": "你更喜欢实用的解决方案，而不是创意概念。", "dim": "N", "rev": True}, 

        # --- T vs F ---
        {"id": 15, "txt_en": "You make decisions based on logic rather than feelings.", "txt_cn": "你做决定时更看重逻辑而非情感。", "dim": "T", "rev": False},
        {"id": 16, "txt_en": "Efficiency is more important to you than being tactful.", "txt_cn": "对你来说，效率比圆滑更重要。", "dim": "T", "rev": False},
        {"id": 17, "txt_en": "In a discussion, truth should be more important than people’s sensitivities.", "txt_cn": "讨论中，真相应该比别人的感受更重要。", "dim": "T", "rev": False},
        {"id": 18, "txt_en": "You are easily affected by other people's emotions.", "txt_cn": "你很容易受到他人情绪的影响。", "dim": "T", "rev": True}, 
        {"id": 19, "txt_en": "Your mood can change very quickly.", "txt_cn": "你的情绪变化很快。", "dim": "T", "rev": True}, 
        {"id": 20, "txt_en": "You often follow your heart even if your head disagrees.", "txt_cn": "即使理智反对，你通常也会跟随内心。", "dim": "T", "rev": True}, 
        {"id": 21, "txt_en": "It is difficult for you to relate to other people’s feelings.", "txt_cn": "你很难对他人的感受产生共鸣。", "dim": "T", "rev": False},

        # --- J vs P ---
        {"id": 22, "txt_en": "You like to have a detailed plan before you start a trip.", "txt_cn": "你喜欢在旅行前制定详细的计划。", "dim": "J", "rev": False},
        {"id": 23, "txt_en": "You usually complete your work well before the deadline.", "txt_cn": "你通常会在截止日期前很久就完成工作。", "dim": "J", "rev": False},
        {"id": 24, "txt_en": "You like to use organizing tools like schedules and lists.", "txt_cn": "你喜欢使用日程表和清单等整理工具。", "dim": "J", "rev": False},
        {"id": 25, "txt_en": "You prefer to keep your options open rather than committing.", "txt_cn": "你更喜欢保留选择余地，而不是过早承诺。", "dim": "J", "rev": True}, 
        {"id": 26, "txt_en": "You often leave things until the last possible minute.", "txt_cn": "你经常把事情拖到最后一刻才做。", "dim": "J", "rev": True}, 
        {"id": 27, "txt_en": "You struggle with strict deadlines.", "txt_cn": "你对应付严格的截止日期感到吃力。", "dim": "J", "rev": True}, 
        {"id": 28, "txt_en": "A cluttered workspace does not bother you.", "txt_cn": "凌乱的工作环境不会让你感到困扰。", "dim": "J", "rev": True}, 
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
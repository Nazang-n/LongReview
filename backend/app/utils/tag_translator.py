"""
Tag translation utilities for converting English tags to Thai
"""

# Genre translations (English -> Thai)
GENRE_TRANSLATIONS = {
    "Action": "แอคชัน",
    "Adventure": "ผจญภัย",
    "Animation & Modeling": "แอนิเมชันและโมเดลลิ่ง",
    "Casual": "สบายๆ",
    "Design & Illustration": "ออกแบบและวาดภาพ",
    "Early Access": "เข้าถึงก่อนใคร",
    "Free To Play": "เล่นฟรี",
    "Indie": "อินดี้",
    "Massively Multiplayer": "เกมรวมมากมาก",
    "RPG": "อาร์พีจี",
    "Racing": "แข่งรถ",
    "Simulation": "จำลองสถานการณ์",
    "Sports": "กีฬา",
    "Strategy": "กลยุทธ์",
    "Video Production": "ผลิตวิดีโอ",
    "Puzzle": "ปริศนา",
    "Horror": "สยองขวัญ",
    "Survival": "เอาชีวิตรอด",
    "Shooter": "ยิง",
    "Fighting": "ต่อสู้",
    "Platformer": "กระโดดหลบหลีก",
    "Open World": "โลกเปิด",
    "Stealth": "แอบซ่อน",
    "Sandbox": "สร้างสรรค์",
    "MMORPG": "เอ็มเอ็มโออาร์พีจี",
    "Battle Royale": "แบทเทิลรอยัล",
    "Card Game": "เกมการ์ด",
    "Board Game": "เกมกระดาน",
    "Educational": "การศึกษา",
    "Music": "ดนตรี",
    "Rhythm": "จังหวะ",
}

# Platform translations (English -> Thai)
PLATFORM_TRANSLATIONS = {
    "Windows": "วินโดวส์",
    "Mac": "แมค",
    "Linux": "ลินุกซ์",
    "PlayStation 4": "เพลย์สเตชัน 4",
    "PlayStation 5": "เพลย์สเตชัน 5",
    "Xbox": "เอ็กซ์บ็อกซ์",
    "Nintendo Switch": "นินเทนโดสวิตช์",
}

# Player mode translations (English -> Thai)
PLAYER_MODE_TRANSLATIONS = {
    "Single-player": "ผู้เล่นคนเดียว",
    "Multi-player": "ผู้เล่นหลายคน",
    "Co-op": "ร่วมมือกัน",
    "Online": "ออนไลน์",
    "Local": "เล่นในเครื่อง",
    "Cross-platform": "ข้ามแพลตฟอร์ม",
}



# Review Tag translations (English -> Thai)
REVIEW_TAG_TRANSLATIONS = {
    # Positive
    "Fun": "สนุก",
    "Good Story": "เนื้อเรื่องดี",
    "Great Soundtrack": "เพลงประกอบยอดเยี่ยม",
    "Atmospheric": "บรรยากาศดี",
    "Addictive": "เล่นแล้วติด",
    "Challenging": "ท้าทาย",
    "Relaxing": "ผ่อนคลาย",
    "Beautiful": "ภาพสวย",
    "Funny": "ตลก",
    "Co-op": "เล่นกับเพื่อนได้",
    "Multiplayer": "เล่นหลายคน",
    "Great Graphics": "กราฟิกสวยงาม",
    "Good Gameplay": "เกมเพลย์ดี",
    "Replay Value": "เล่นซ้ำได้",
    "Optimized": "กินสเปคน้อย",
    "Masterpiece": "ขึ้นหิ้ง",
    "Classic": "คลาสสิก",
    "Cute": "น่ารัก",
    "Open World": "โลกเปิด",
    "Exploration": "น่าสำรวจ",
    
    # Negative
    "Boring": "น่าเบื่อ",
    "Repetitive": "ซ้ำซาก",
    "Buggy": "บั๊กเยอะ",
    "Bad Optimization": "กินสเปค",
    "Laggy": "แลก/กระตุก",
    "Expensive": "แพงเกินไป",
    "Short": "สั้นเกินไป",
    "Pay to Win": "เทพทรู",
    "Toxic Community": "สังคมแย่",
    "Crash": "เกมเด้ง",
    "Bad Controls": "บังคับยาก",
    "Grindy": "ฟาร์มหนัก",
    "Unfinished": "เกมยังไม่เสร็จ",
    "Dead Game": "เกมร้าง",
    "Cheaters": "โปรเยอะ",
    
    # Mechanics / Gameplay
    "Combat System": "ระบบการต่อสู้",
    "Art Direction": "งานภาพศิลป์",
    "Voice Acting": "เสียงพากย์",
    "Main Story": "เนื้อเรื่องหลัก",
    "Parry System": "ระบบปัดป้อง",
    "First Act": "บทแรก",
    "Enemy Attacks": "การโจมตีศัตรู",
    "Attack Patterns": "รูปแบบโจมตี",
    "Damage Cap": "ติดแคปดาเมจ",
    "Core Gameplay": "เกมเพลย์หลัก",
    "Boss Fights": "สู้บอส",
    "Skill Tree": "ผังสกิล",
    "Mechanics": "ระบบเกม",
    
    # Comparisons (often used)
    "Dark Souls": "คล้าย Dark Souls",
    "Elden Ring": "คล้าย Elden Ring"
}

def translate_tag(tag_name: str, tag_type: str) -> str:
    """
    Translate a tag name from English to Thai based on its type.
    
    Args:
        tag_name: English tag name
        tag_type: Type of tag ('genre', 'platform', 'player_mode', 'review_tag')
    
    Returns:
        Thai translation if available, otherwise returns original name
    """
    # Normalize keys for lookup (case-insensitive)
    tag_clean = tag_name.strip()
    
    if tag_type == "genre":
        return GENRE_TRANSLATIONS.get(tag_clean, tag_name)
    elif tag_type == "platform":
        return PLATFORM_TRANSLATIONS.get(tag_clean, tag_name)
    elif tag_type == "player_mode":
        return PLAYER_MODE_TRANSLATIONS.get(tag_clean, tag_name)
    elif tag_type == "review_tag":
        # Case insensitive lookup for review tags
        for k, v in REVIEW_TAG_TRANSLATIONS.items():
            if k.lower() == tag_clean.lower():
                return v
        return tag_name
    else:
        return tag_name


def get_all_translations():
    """Get all available translations grouped by type"""
    return {
        "genres": GENRE_TRANSLATIONS,
        "platforms": PLATFORM_TRANSLATIONS,
        "player_modes": PLAYER_MODE_TRANSLATIONS,
        "review_tags": REVIEW_TAG_TRANSLATIONS
    }

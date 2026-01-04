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


def translate_tag(tag_name: str, tag_type: str) -> str:
    """
    Translate a tag name from English to Thai based on its type.
    
    Args:
        tag_name: English tag name
        tag_type: Type of tag ('genre', 'platform', 'player_mode')
    
    Returns:
        Thai translation if available, otherwise returns original name
    """
    if tag_type == "genre":
        return GENRE_TRANSLATIONS.get(tag_name, tag_name)
    elif tag_type == "platform":
        return PLATFORM_TRANSLATIONS.get(tag_name, tag_name)
    elif tag_type == "player_mode":
        return PLAYER_MODE_TRANSLATIONS.get(tag_name, tag_name)
    else:
        return tag_name


def get_all_translations():
    """Get all available translations grouped by type"""
    return {
        "genres": GENRE_TRANSLATIONS,
        "platforms": PLATFORM_TRANSLATIONS,
        "player_modes": PLAYER_MODE_TRANSLATIONS
    }

"""
Script to add Thai game details to the database
This example adds Thai content for Palworld
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Thai translation for Palworld
PALWORLD_THAI = """เกี่ยวกับเกม
Q. เกมนี้เป็นเกมแนวไหน?

A. ในเกมนี้ คุณสามารถใช้ชีวิตอย่างสงบสุขร่วมกับสิ่งมีชีวิตลึกลับที่เรียกว่า Pals หรือเสี่ยงชีวิตเพื่อต่อสู้กับกลุ่มนักล่าที่โหดเหี้ยม

Pals สามารถใช้ในการต่อสู้ หรือทำงานในฟาร์มหรือโรงงานได้
คุณยังสามารถขายหรือกินพวกมันได้อีกด้วย!

การเอาตัวรอด
ในสภาพแวดล้อมที่โหดร้าย ซึ่งอาหารหายากและนักล่าที่โหดเหี้ยมเดินทางไปมา อันตรายรออยู่ทุกมุม เพื่อความอยู่รอด คุณต้องเดินอย่างระมัดระวังและตัดสินใจที่ยากลำบาก...แม้กระทั่งการกิน Pals ของคุณเองเมื่อถึงเวลา

การขี่และการสำรวจ
Pals สามารถขี่เพื่อเดินทางบนบก ทะเล และท้องฟ้า—ช่วยให้คุณสำรวจทุกสภาพแวดล้อมในโลกนี้

การสร้างสิ่งปลูกสร้าง
ต้องการสร้างปิรามิด? ให้กองทัพ Pals ทำงานนี้ ไม่ต้องกังวล ไม่มีกฎหมายแรงงานสำหรับ Pals

การผลิต
ใช้ Pals และทักษะของพวกมันในการจุดไฟ ผลิตไฟฟ้า หรือขุดแร่ เพื่อให้คุณมีชีวิตที่สะดวกสบาย

การทำฟาร์ม
Pals บางตัวเก่งในการปลูกเมล็ด ในขณะที่บางตัวมีทักษะในการรดน้ำหรือเก็บเกี่ยว ทำงานร่วมกับ Pals ของคุณเพื่อสร้างฟาร์มในอุดมคติ

โรงงานและระบบอัตโนมัติ
การให้ Pals ทำงานคือกุญแจสำคัญของระบบอัตโนมัติ สร้างโรงงาน วาง Pal ไว้ในนั้น และพวกมันจะทำงานต่อไปตราบใดที่ได้รับอาหาร—จนกว่าพวกมันจะตาย

การสำรวจดันเจี้ยน
ด้วย Pals อยู่เคียงข้าง คุณสามารถเผชิญหน้ากับพื้นที่อันตรายที่สุดได้ เมื่อถึงเวลา คุณอาจต้องเสียสละหนึ่งตัวเพื่อช่วยชีวิตคุณ พวกมันจะปกป้องชีวิตคุณ—แม้ว่าจะต้องเสียชีวิตของพวกมันเอง

การผสมพันธุ์และพันธุกรรม
ผสมพันธุ์ Pal และมันจะสืบทอดลักษณะของพ่อแม่ ผสม Pals หายากเพื่อสร้าง Pal ที่แข็งแกร่งที่สุด!

การล่าและอาชญากรรม
Pals ที่ใกล้สูญพันธุ์อาศัยอยู่ในเขตอนุรักษ์สัตว์ป่า แอบเข้าไปและจับ Pals หายากเพื่อรวยเร็ว มันไม่ใช่อาชญากรรมถ้าคุณไม่ถูกจับ

มัลติเพลเยอร์
รองรับมัลติเพลเยอร์ ดังนั้นชวนเพื่อนและไปผจญภัยด้วยกัน และแน่นอนคุณสามารถต่อสู้กับเพื่อนและแลกเปลี่ยน Pals ได้ด้วย

ในโหมดเล่นร่วมออนไลน์ ผู้เล่นสูงสุด 4 คนสามารถเล่นด้วยกันได้
นอกจากนี้ เซิร์ฟเวอร์เฉพาะสามารถรองรับผู้เล่นได้สูงสุด 32 คน"""

def add_thai_content():
    """Add Thai content to games"""
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            print("Error: DATABASE_URL not found in environment variables")
            return
        
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # First, let's see what games we have
            result = connection.execute(text("SELECT id, name FROM game LIMIT 10"))
            games = result.fetchall()
            
            print("Available games:")
            for game in games:
                print(f"  ID: {game[0]}, Name: {game[1]}")
            
            print("\n" + "="*50)
            
            # Check if Palworld exists
            result = connection.execute(text("SELECT id FROM game WHERE name ILIKE '%palworld%'"))
            palworld = result.fetchone()
            
            if palworld:
                game_id = palworld[0]
                print(f"\nFound Palworld with ID: {game_id}")
                print("Adding Thai content...")
                
                connection.execute(
                    text("UPDATE game SET about_game_th = :thai_content WHERE id = :game_id"),
                    {"thai_content": PALWORLD_THAI, "game_id": game_id}
                )
                connection.commit()
                
                print("SUCCESS: Thai content added to Palworld!")
            else:
                print("\nPalworld not found in database.")
                print("You can manually add Thai content to any game using:")
                print("UPDATE game SET about_game_th = 'Thai content here...' WHERE id = <game_id>;")
            
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    print("Adding Thai game details to database...")
    add_thai_content()

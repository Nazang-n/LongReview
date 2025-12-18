"""Test clean_description with actual API data"""
import sys
sys.path.insert(0, '.')

from app.utils.mappers import clean_description

# Test cases from actual API
test_cases = [
    {
        "name": "API Example 1 - No text after [...]",
        "input": "กกท. หนุนสมาคมอีสปอร์ตฯ เอาผิด \"Tokyogurl\" [...]",
        "expected": "Should keep text before [...] and replace with ..."
    },
    {
        "name": "API Example 2 - No text after [...]",
        "input": "อรวรรณ-สุธาสินี แชมป์ปิงปองหญิงคู่ซีเกมส์ 4 สมัยติด การ [...]",
        "expected": "Should keep text before [...] and replace with ..."
    },
    {
        "name": "API Example 3 - Text after [...] with WordPress footer",
        "input": "ข้อมูลล่าสุดเกี่ยวกับ Samsung Galaxy S26 ถูกยืนยันทางอ้ [...]The post Samsung Galaxy S26 เผยขนาดตัวเครื่องจากผู้ผลิตกระจก สอดคล้องข้อมูลหลุดก่อนหน้า appeared first on แอพดิสคัส.",
        "expected": "Should keep text after [...] but remove WordPress footer"
    },
    {
        "name": "Hypothetical - Text after [...] without footer",
        "input": "This is a description [...] and this text should be preserved.",
        "expected": "Should keep all text and replace [...] with ..."
    }
]

with open('clean_description_test_results.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("TESTING clean_description FUNCTION\n")
    f.write("=" * 80 + "\n\n")
    
    for i, test in enumerate(test_cases, 1):
        f.write(f"\n{'='*80}\n")
        f.write(f"Test {i}: {test['name']}\n")
        f.write(f"{'='*80}\n")
        f.write(f"Input ({len(test['input'])} chars):\n{test['input']}\n\n")
        
        result = clean_description(test['input'])
        
        f.write(f"Output ({len(result)} chars):\n{result}\n\n")
        f.write(f"Expected: {test['expected']}\n")
        
        # Check if text was lost
        input_before_marker = test['input'].split('[...]')[0] if '[...]' in test['input'] else test['input']
        if '[...]' in test['input'] and len(test['input'].split('[...]')) > 1:
            text_after_marker = test['input'].split('[...]')[1]
            # Remove WordPress footer from text_after for comparison
            text_after_clean = text_after_marker.split('The post')[0] if 'The post' in text_after_marker else text_after_marker
            text_after_clean = text_after_clean.strip()
            
            if text_after_clean and text_after_clean not in result:
                f.write(f"\n❌ ERROR: Text after [...] was lost!\n")
                f.write(f"Lost text: {text_after_clean}\n")
            elif text_after_clean:
                f.write(f"\n✓ OK: Text after [...] preserved\n")
        
        f.write("\n")

print("Test results written to clean_description_test_results.txt")

"""Comprehensive test of clean_description to ensure no text is deleted after ..."""
import sys
sys.path.insert(0, '.')

from app.utils.mappers import clean_description

# Test cases that specifically check text after ...
test_cases = [
    {
        "name": "Test 1: [...] with text after",
        "input": "Game description [...] and more text here",
        "should_contain": "and more text here"
    },
    {
        "name": "Test 2: [...] with long text after",
        "input": "This is a game [...] with amazing graphics and gameplay features",
        "should_contain": "with amazing graphics and gameplay features"
    },
    {
        "name": "Test 3: Regular ... with text after (no brackets)",
        "input": "Description... and continuation text",
        "should_contain": "and continuation text"
    },
    {
        "name": "Test 4: [...] in middle with more content",
        "input": "First part [...] middle section [...] final part",
        "should_contain": "final part"
    },
    {
        "name": "Test 5: Real example from database",
        "input": "ผู้จัดจําหน่ายเกม Cult of The Lamb ปล่อยตัวอย่างใหม่ของ DLC Woolhaven [...] และร่วมผจญภัยในดันเจี้ยนใหม่",
        "should_contain": "และร่วมผจญภัยในดันเจี้ยนใหม่"
    },
    {
        "name": "Test 6: [...] with WordPress footer",
        "input": "Game info [...] more details The post Title appeared first on Site.",
        "should_contain": "more details",
        "should_not_contain": "The post"
    }
]


with open('text_preservation_test_results.txt', 'w', encoding='utf-8') as output:
    output.write("=" * 80 + "\n")
    output.write("COMPREHENSIVE TEST: Ensuring text after ... is preserved\n")
    output.write("=" * 80 + "\n")

    all_passed = True
    for i, test in enumerate(test_cases, 1):
        result = clean_description(test["input"])
        
        # Check if required text is present
        contains_required = test["should_contain"] in result
        
        # Check if forbidden text is absent (if specified)
        forbidden_absent = True
        if "should_not_contain" in test:
            forbidden_absent = test["should_not_contain"] not in result
        
        passed = contains_required and forbidden_absent
        all_passed = all_passed and passed
        
        output.write(f"\n{test['name']}\n")
        output.write(f"Input:  {test['input']}\n")
        output.write(f"Output: {result}\n")
        output.write(f"Should contain: '{test['should_contain']}'\n")
        output.write(f"Actually contains: {contains_required}\n")
        if "should_not_contain" in test:
            output.write(f"Should NOT contain: '{test['should_not_contain']}'\n")
            output.write(f"Correctly absent: {forbidden_absent}\n")
        output.write(f"Status: {'PASS' if passed else 'FAIL'}\n")

    output.write("\n" + "=" * 80 + "\n")
    if all_passed:
        output.write("SUCCESS: All tests passed! Text after ... is preserved.\n")
        print("SUCCESS: All tests passed! Text after ... is preserved.")
    else:
        output.write("FAILURE: Some tests failed! Text is being deleted.\n")
        print("FAILURE: Some tests failed! Text is being deleted.")
    output.write("=" * 80 + "\n")

print("Results written to text_preservation_test_results.txt")

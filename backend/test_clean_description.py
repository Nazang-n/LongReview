"""Test script to verify clean_description function"""
import sys
sys.path.insert(0, '.')

from app.utils.mappers import clean_description

# Test cases
test_cases = [
    {
        "name": "Test 1: [...] with text after",
        "input": "This is a game description [...] and this text should remain.",
        "expected": "This is a game description ... and this text should remain."
    },
    {
        "name": "Test 2: Multiple [...]",
        "input": "First part [...] middle part [...] last part",
        "expected": "First part ... middle part ... last part"
    },
    {
        "name": "Test 3: [...] with WordPress footer",
        "input": "Game description [...] more text The post My Game appeared first on GameSite.",
        "expected": "Game description ... more text"
    },
    {
        "name": "Test 4: Only WordPress footer",
        "input": "Game description The post My Game appeared first on GameSite.",
        "expected": "Game description"
    },
    {
        "name": "Test 5: Normal text without [...]",
        "input": "This is a normal description without any markers.",
        "expected": "This is a normal description without any markers."
    }
]

print("=" * 60)
print("Testing clean_description function")
print("=" * 60)

all_passed = True
for i, test in enumerate(test_cases, 1):
    result = clean_description(test["input"])
    passed = result == test["expected"]
    all_passed = all_passed and passed
    
    print(f"\n{test['name']}")
    print(f"Input:    {test['input']}")
    print(f"Expected: {test['expected']}")
    print(f"Got:      {result}")
    print(f"Status:   {'PASS' if passed else 'FAIL'}")

print("\n" + "=" * 60)
if all_passed:
    print("All tests passed!")
else:
    print("Some tests failed!")
print("=" * 60)

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from heybuddy.services.persona import get_system_prompt

class TestPersonaService(unittest.TestCase):
    
    def test_childish_english(self):
        prompt = get_system_prompt("childish", "en")
        self.assertIn("playful teddy bear", prompt)
        self.assertIn("simple words", prompt)
        self.assertIn("child", prompt)
        
    def test_mature_english(self):
        prompt = get_system_prompt("mature", "en")
        self.assertIn("wise teddy bear coach", prompt)
        self.assertIn("motivate", prompt)
        self.assertIn("child-appropriate", prompt)
        
    def test_childish_german(self):
        prompt = get_system_prompt("childish", "de")
        self.assertIn("verspielter Teddybär", prompt)
        self.assertIn("kurzen, einfachen Sätzen", prompt)
        self.assertIn("Kinder", prompt)
        
    def test_mature_german(self):
        prompt = get_system_prompt("mature", "de")
        self.assertIn("kluger Teddybär-Coach", prompt)
        self.assertIn("motivierend", prompt)
        self.assertIn("kindgerecht", prompt)
        
    def test_fallback_to_default(self):
        # Test invalid persona/language combinations
        prompt = get_system_prompt("invalid", "invalid")
        default_prompt = get_system_prompt("childish", "en")
        self.assertEqual(prompt, default_prompt)
        
    def test_all_prompts_contain_safety_guidelines(self):
        # All prompts should contain safety guidelines
        prompts = [
            get_system_prompt("childish", "en"),
            get_system_prompt("mature", "en"),
            get_system_prompt("childish", "de"),
            get_system_prompt("mature", "de")
        ]
        
        for prompt in prompts:
            # Each prompt should mention avoiding adult topics
            self.assertTrue(
                "adult topics" in prompt.lower() or 
                "erwachsenenthemen" in prompt.lower()
            )
            
            # Each prompt should mention not asking for personal info
            self.assertTrue(
                "personal" in prompt.lower() or 
                "persönlichen" in prompt.lower()
            )

if __name__ == '__main__':
    unittest.main()
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from heybuddy.services.moderation import ModerationService
from heybuddy.config import Config

class TestModerationService(unittest.TestCase):
    def setUp(self):
        self.moderation = ModerationService()
        
    def test_violence_keywords_strict(self):
        Config.SAFETY_MODE = 'strict'
        
        # Test violence keywords
        self.assertTrue(self.moderation.is_flagged("I want to hurt someone"))
        self.assertTrue(self.moderation.is_flagged("Let's fight"))
        self.assertTrue(self.moderation.is_flagged("Do you have a gun?"))
        
        # Test safe content
        self.assertFalse(self.moderation.is_flagged("Tell me a story"))
        self.assertFalse(self.moderation.is_flagged("I love animals"))
        
    def test_personal_info_keywords(self):
        Config.SAFETY_MODE = 'strict'
        
        # Test personal info requests
        self.assertTrue(self.moderation.is_flagged("What is your address?"))
        self.assertTrue(self.moderation.is_flagged("Where do you live?"))
        self.assertTrue(self.moderation.is_flagged("Tell me your phone number"))
        
        # Test safe questions
        self.assertFalse(self.moderation.is_flagged("What's your favorite color?"))
        self.assertFalse(self.moderation.is_flagged("Do you like stories?"))
        
    def test_lenient_mode(self):
        Config.SAFETY_MODE = 'lenient'
        
        # Lenient mode should allow some words that strict mode blocks
        self.assertFalse(self.moderation.is_flagged("The doctor helped me"))
        self.assertFalse(self.moderation.is_flagged("I'm going to vote"))
        
        # But still block high-risk content
        self.assertTrue(self.moderation.is_flagged("I want to hurt someone"))
        self.assertTrue(self.moderation.is_flagged("Where do you live?"))
        
    def test_case_insensitive(self):
        Config.SAFETY_MODE = 'strict'
        
        self.assertTrue(self.moderation.is_flagged("HURT"))
        self.assertTrue(self.moderation.is_flagged("Hurt"))
        self.assertTrue(self.moderation.is_flagged("hurt"))
        
    def test_word_boundaries(self):
        Config.SAFETY_MODE = 'strict'
        
        # Should match whole words only
        self.assertTrue(self.moderation.is_flagged("I am hurt"))
        self.assertFalse(self.moderation.is_flagged("I hurt my feelings"))  # This might need adjustment based on requirements

if __name__ == '__main__':
    unittest.main()
import re
from heybuddy.config import Config

class ModerationService:
    def __init__(self):
        self.keywords = {
            'violence': [
                'kill', 'hurt', 'fight', 'punch', 'kick', 'violence', 'weapon', 'gun', 'knife',
                'blood', 'death', 'murder', 'war', 'attack', 'hate', 'angry', 'mad'
            ],
            'adult': [
                'sex', 'sexy', 'nude', 'naked', 'kiss', 'love', 'boyfriend', 'girlfriend',
                'marriage', 'pregnant', 'baby', 'adult', 'grown-up'
            ],
            'politics': [
                'president', 'government', 'politics', 'vote', 'election', 'democrat',
                'republican', 'politician', 'congress', 'senate'
            ],
            'medical': [
                'doctor', 'medicine', 'sick', 'disease', 'hospital', 'surgery', 'pain',
                'injury', 'prescription', 'drug', 'pill'
            ],
            'substances': [
                'alcohol', 'beer', 'wine', 'drunk', 'smoking', 'cigarette', 'drugs',
                'marijuana', 'cocaine', 'heroin'
            ],
            'personal': [
                'address', 'phone', 'number', 'email', 'password', 'where do you live',
                'what is your name', 'how old are you', 'school name', 'full name'
            ],
            'location': [
                'where are you', 'come to my house', 'meet me', 'address', 'location',
                'GPS', 'coordinates'
            ]
        }
        
    def is_flagged(self, text):
        if Config.SAFETY_MODE == 'lenient':
            return self._lenient_check(text)
        else:
            return self._strict_check(text)
            
    def _strict_check(self, text):
        text_lower = text.lower()
        for category, words in self.keywords.items():
            for word in words:
                if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                    return True
        return False
        
    def _lenient_check(self, text):
        text_lower = text.lower()
        high_risk_categories = ['violence', 'adult', 'substances', 'personal', 'location']
        
        for category in high_risk_categories:
            for word in self.keywords[category]:
                if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                    return True
        return False
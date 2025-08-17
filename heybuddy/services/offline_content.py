import os
import random
import glob
from heybuddy.config import Config

class OfflineContent:
    def __init__(self):
        self.stories_dir = Config.OFFLINE_STORIES_DIR
        
    def get_random_story(self):
        story_files = glob.glob(os.path.join(self.stories_dir, "*.wav"))
        
        if story_files:
            return random.choice(story_files)
        else:
            return None
            
    def get_all_stories(self):
        return glob.glob(os.path.join(self.stories_dir, "*.wav"))
        
    def has_stories(self):
        return len(self.get_all_stories()) > 0
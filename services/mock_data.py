import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

class MockDataService:
    def __init__(self):
        # Only Instagram mock data is available
        pass
    
    def get_mock_instagram_posts(self) -> List[Dict]:
        """
        Get mock Instagram trending restaurant posts
        Mock trending restaurants in San Francisco based on real Instagram trends
        This simulates what you'd get from Instagram API
        Loads data from JSON file and converts hours_ago to actual timestamps
        """
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, '..', 'mock_data', 'instagram_posts.json')
        
        try:
            with open(json_path, 'r') as f:
                posts = json.load(f)
            
            # Convert hours_ago to actual timestamps
            for post in posts:
                hours_ago = post.get('hours_ago', 0)
                post['timestamp'] = (datetime.now() - timedelta(hours=hours_ago)).isoformat()
                # Remove hours_ago as it's no longer needed
                post.pop('hours_ago', None)
            
            return posts
        except FileNotFoundError:
            print(f"⚠️ Instagram mock data file not found at {json_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing Instagram mock data JSON: {e}")
            return []

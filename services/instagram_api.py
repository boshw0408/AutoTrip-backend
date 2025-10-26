import requests
from core.config import settings
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from services.mock_data import MockDataService

class InstagramAPIService:
    def __init__(self):
        self.access_token = settings.instagram_access_token
        self.page_id = settings.instagram_page_id
        self.business_account_id = settings.instagram_business_account_id
        self.base_url = "https://graph.facebook.com/v18.0"
        self.api_version = "v18.0"
        self.mock_service = MockDataService()
        
    async def search_trending_restaurants(self, location: str = "San Francisco", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for trending restaurants in San Francisco using Instagram hashtags
        
        Strategy:
        1. Search San Francisco food hashtags to find trending posts
        2. Extract venue names from posts that have location tags
        3. Rank by engagement metrics (likes + comments + shares)
        4. Filter for recent posts (within last 7 days for trending)
        """
        if not self.access_token:
            print("⚠️ Instagram access token not available")
            return []
        
        try:
            # San Francisco specific hashtags
            hashtags = [
                "sanfranciscofood",
                "sfdesserts", 
                "bayareafood",
                "sanfranciscoeats",
                "sffoodie",
                "sanfranciscorestaurants"
            ]
            
            all_posts = []
            
            # Search each hashtag
            for hashtag in hashtags:
                posts = await self._search_hashtag(hashtag)
                all_posts.extend(posts)
            
            # Process and rank posts
            restaurants = self._extract_restaurants_from_posts(all_posts, location)
            
            # Sort by trending score (engagement + recency)
            trending_restaurants = sorted(
                restaurants, 
                key=lambda x: x.get('trending_score', 0), 
                reverse=True
            )[:limit]
            
            return trending_restaurants
            
        except Exception as e:
            print(f"❌ Error searching trending restaurants: {e}")
            return []
    
    async def search_dessert_places(self, location: str = "San Francisco", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for trending dessert places in San Francisco
        """
        if not self.access_token:
            return []
        
        try:
            # Dessert-specific hashtags
            hashtags = [
                "sfdesserts",
                "sanfranciscodesserts",
                "bayareadesserts",
                "dessertfood",
                "sweetsiegesf"
            ]
            
            all_posts = []
            
            for hashtag in hashtags:
                posts = await self._search_hashtag(hashtag)
                all_posts.extend(posts)
            
            desserts = self._extract_restaurants_from_posts(all_posts, location, category="dessert")
            
            trending_desserts = sorted(
                desserts,
                key=lambda x: x.get('trending_score', 0),
                reverse=True
            )[:limit]
            
            return trending_desserts
            
        except Exception as e:
            print(f"❌ Error searching dessert places: {e}")
            return []
    
    async def _search_hashtag(self, hashtag: str) -> List[Dict]:
        """Search Instagram posts by hashtag"""
        try:
            # Use Instagram Basic Display API to search hashtags
            # Note: Instagram Graph API requires media objects from pages, 
            # but we can simulate trending by using hashtag search
            
            url = f"{self.base_url}/ig_hashtag_search"
            params = {
                "user_id": "me",  # You need a user ID with granted permissions
                "q": hashtag,
                "access_token": self.access_token
            }
            
            # Since hashtag search requires specific permissions, we'll use a mock approach
            # with the available permissions (pages_show_list, business_management, etc.)
            
            # Alternative: Search recent posts via pages or media endpoints
            return await self._get_recent_media_by_location()
            
        except Exception as e:
            print(f"Error searching hashtag {hashtag}: {e}")
            return []
    
    async def _get_recent_media_by_location(self) -> List[Dict]:
        """
        Get recent media from Instagram Business account
        Uses Instagram Graph API to fetch real posts
        """
        try:
            # Use real Instagram API if credentials are available
            if self.business_account_id and self.access_token:
                return await self._fetch_real_instagram_media()
            else:
                # Fallback to mock data if credentials not configured
                print("⚠️ Instagram credentials not configured, using mock data")
                return self.mock_service.get_mock_instagram_posts()
            
        except Exception as e:
            print(f"Error getting recent media: {e}")
            return self.mock_service.get_mock_instagram_posts()
    
    async def _fetch_real_instagram_media(self) -> List[Dict]:
        """
        Fetch real Instagram media using Graph API
        API endpoint: GET /{ig-business-account-id}/media
        """
        try:
            url = f"{self.base_url}/{self.business_account_id}/media"
            params = {
                "fields": "id,caption,media_url,permalink,timestamp,like_count,comments_count,location",
                "access_token": self.access_token,
                "limit": 25  # Fetch recent 25 posts
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get('data', [])
            
            # Transform Instagram API response to our format
            transformed_posts = []
            for post in posts:
                # Extract location data if available
                location_data = post.get('location', {})
                
                transformed_post = {
                    "id": post.get('id'),
                    "username": "your_business_account",  # Can be fetched separately
                    "caption": post.get('caption', ''),
                    "media_url": post.get('media_url', ''),
                    "permalink": post.get('permalink', ''),
                    "timestamp": post.get('timestamp', ''),
                    "like_count": post.get('like_count', 0),
                    "views_count": post.get('like_count', 0) * 5,  # Estimate views as 5x likes
                    "comments_count": post.get('comments_count', 0),
                    "location": {
                        "id": location_data.get('id', ''),
                        "name": location_data.get('name', ''),
                        "latitude": location_data.get('latitude', 37.7749),
                        "longitude": location_data.get('longitude', -122.4194)
                    }
                }
                transformed_posts.append(transformed_post)
            
            print(f"✅ Fetched {len(transformed_posts)} real Instagram posts")
            return transformed_posts
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Instagram API request failed: {e}")
            print("Falling back to mock data")
            return self.mock_service.get_mock_instagram_posts()
        except Exception as e:
            print(f"❌ Error processing Instagram data: {e}")
            return self.mock_service.get_mock_instagram_posts()
    
    def _extract_restaurants_from_posts(self, posts: List[Dict], location: str, category: str = "restaurant") -> List[Dict[str, Any]]:
        """
        Extract restaurant information from Instagram posts
        
        New Trending Score Formula:
        score = 0.45 * freq_norm + 0.25 * likes_norm + 0.15 * views_norm + 0.10 * comments_norm + 0.05 * recency_norm
        
        Where:
        - freq_norm: Normalized hashtag frequency (weighted highest)
        - likes_norm: Normalized likes count
        - views_norm: Normalized views count
        - comments_norm: Normalized comments count
        - recency_norm: Time decay (max(0, 1 - days_since_post / 30))
        """
        restaurants = {}
        
        # First pass: count hashtag frequency per venue
        venue_hashtag_counts = {}
        for post in posts:
            location_data = post.get('location', {})
            venue_name = location_data.get('name')
            
            if not venue_name:
                venue_name = self._extract_venue_from_caption(post.get('caption', ''))
            
            if venue_name:
                venue_hashtag_counts[venue_name] = venue_hashtag_counts.get(venue_name, 0) + 1
        
        # Find max hashtag count for normalization
        max_freq = max(venue_hashtag_counts.values()) if venue_hashtag_counts else 1
        
        # Second pass: calculate trending scores
        for post in posts:
            location_data = post.get('location', {})
            venue_name = location_data.get('name')
            
            if not venue_name:
                venue_name = self._extract_venue_from_caption(post.get('caption', ''))
            
            if not venue_name:
                continue
            
            # Extract engagement metrics
            likes = post.get('like_count', 0)
            views = post.get('views_count', 0)  # Add views to mock data
            comments = post.get('comments_count', 0)
            
            # Calculate days since post
            days_ago = self._get_days_ago(post.get('timestamp'))
            
            # Frequency: count of hashtag appearances for this venue
            freq = venue_hashtag_counts.get(venue_name, 0)
            
            # Normalize all metrics (0-1 scale)
            freq_norm = freq / max_freq if max_freq > 0 else 0
            
            # Normalize likes (assume max ~10,000 for scaling)
            likes_norm = min(1.0, likes / 10000.0)
            
            # Normalize views (assume max ~50,000 for scaling)
            views_norm = min(1.0, views / 50000.0)
            
            # Normalize comments (assume max ~500 for scaling)
            comments_norm = min(1.0, comments / 500.0)
            
            # Recency decay: max(0, 1 - days_since_post / 30)
            recency_norm = max(0, 1 - days_ago / 30)
            
            # Calculate final trending score with weights
            trending_score = (
                0.45 * freq_norm +
                0.25 * likes_norm +
                0.15 * views_norm +
                0.10 * comments_norm +
                0.05 * recency_norm
            )
            
            # Update if we have better engagement or create new entry
            if venue_name not in restaurants or trending_score > restaurants[venue_name]['trending_score']:
                restaurants[venue_name] = {
                    'id': post.get('id', f"insta_{venue_name.lower().replace(' ', '_')}"),
                    'name': venue_name,
                    'address': self._get_address_from_location(location_data),
                    'rating': self._calculate_rating_from_engagement(likes, comments),
                    'price_level': 2,  # Default moderate pricing
                    'types': [category, 'instagram_trending'],
                    'location': {
                        'lat': location_data.get('latitude', 37.7749),
                        'lng': location_data.get('longitude', -122.4194)
                    },
                    'photos': [post.get('media_url', '')],
                    'description': f"Trending on Instagram 📸 {post.get('caption', '')[:100]}",
                    'source': 'instagram',
                    'trending_score': trending_score,
                    'instagram_url': post.get('permalink', ''),
                    'likes': likes,
                    'views': views,
                    'comments': comments,
                    'hashtag_frequency': freq,
                    'post_age_days': days_ago,
                    'score_breakdown': {
                        'frequency': round(freq_norm, 3),
                        'likes': round(likes_norm, 3),
                        'views': round(views_norm, 3),
                        'comments': round(comments_norm, 3),
                        'recency': round(recency_norm, 3)
                    }
                }
        
        return list(restaurants.values())
    
    def _get_hours_ago(self, timestamp: str) -> int:
        """Calculate hours since post was created"""
        try:
            post_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(post_time.tzinfo) if post_time.tzinfo else datetime.now()
            delta = now - post_time
            return int(delta.total_seconds() / 3600)
        except:
            return 999  # Unknown age
    
    def _get_days_ago(self, timestamp: str) -> float:
        """Calculate days since post was created (for recency decay)"""
        try:
            post_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(post_time.tzinfo) if post_time.tzinfo else datetime.now()
            delta = now - post_time
            return delta.total_seconds() / 86400  # Convert to days
        except:
            return 999.0  # Unknown age
    
    def _calculate_rating_from_engagement(self, likes: int, comments: int) -> float:
        """
        Convert Instagram engagement to a 1-5 rating
        Higher engagement = higher rating
        """
        engagement = likes + comments * 3
        
        if engagement > 1000:
            return 4.5
        elif engagement > 500:
            return 4.0
        elif engagement > 200:
            return 3.5
        elif engagement > 100:
            return 3.0
        else:
            return 2.5
    
    def _extract_venue_from_caption(self, caption: str) -> Optional[str]:
        """Try to extract venue name from Instagram caption"""
        # Look for common patterns like "@venue_name" or mentions
        mention_pattern = r'@(\w+)'
        matches = re.findall(mention_pattern, caption)
        if matches:
            return matches[0].replace('_', ' ').title()
        return None
    
    def _get_address_from_location(self, location_data: Dict) -> str:
        """Generate address from location data"""
        venue_name = location_data.get('name', 'Unknown')
        return f"{venue_name}, San Francisco, CA"
    
    async def get_venue_details(self, venue_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific venue"""
        # This would query Instagram for specific venue details
        return None


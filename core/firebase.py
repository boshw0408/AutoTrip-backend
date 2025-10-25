import firebase_admin
from firebase_admin import credentials, firestore
from core.config import settings
import json

class FirebaseClient:
    def __init__(self):
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                # For development, use mock credentials
                if settings.environment == "development":
                    # Create a mock credential for development
                    cred = credentials.Certificate({
                        "type": "service_account",
                        "project_id": "travel-ai-dev",
                        "private_key_id": "mock",
                        "private_key": "-----BEGIN PRIVATE KEY-----\nmock\n-----END PRIVATE KEY-----\n",
                        "client_email": "mock@travel-ai-dev.iam.gserviceaccount.com",
                        "client_id": "mock",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    })
                else:
                    # In production, use the actual service account key
                    cred = credentials.Certificate(json.loads(settings.firebase_key))
                
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Firebase initialized successfully")
            
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            # For development, create a mock database
            if settings.environment == "development":
                self.db = MockFirestore()
                print("🔄 Using mock Firestore for development")

class MockFirestore:
    """Mock Firestore for development"""
    
    def __init__(self):
        self.data = {
            'trips': {},
            'users': {},
            'itineraries': {}
        }
    
    def collection(self, collection_name: str):
        return MockCollection(self.data.get(collection_name, {}))
    
    def document(self, doc_id: str):
        return MockDocument(doc_id, self.data)

class MockCollection:
    def __init__(self, data: dict):
        self.data = data
    
    def document(self, doc_id: str):
        return MockDocument(doc_id, self.data)
    
    def add(self, data: dict):
        doc_id = f"mock_{len(self.data)}"
        self.data[doc_id] = data
        return MockDocument(doc_id, self.data)
    
    def get(self):
        return [MockDocument(doc_id, data) for doc_id, data in self.data.items()]

class MockDocument:
    def __init__(self, doc_id: str, data: dict):
        self.id = doc_id
        self.data = data
    
    def get(self):
        return MockDocumentSnapshot(self.id, self.data.get(self.id, {}))
    
    def set(self, data: dict):
        self.data[self.id] = data
        return self
    
    def update(self, data: dict):
        if self.id in self.data:
            self.data[self.id].update(data)
        return self
    
    def delete(self):
        if self.id in self.data:
            del self.data[self.id]
        return self

class MockDocumentSnapshot:
    def __init__(self, doc_id: str, data: dict):
        self.id = doc_id
        self._data = data
    
    def to_dict(self):
        return self._data
    
    def exists(self):
        return bool(self._data)

# Global Firebase client instance
firebase_client = FirebaseClient()
db = firebase_client.db

# AutoTrip Backend

A FastAPI backend for the AutoTrip travel planning application with AI-powered itinerary generation.

## 🚀 Features

- **AI-Powered Itinerary Generation**: Uses LangChain + OpenAI to create personalized travel plans
- **Smart Recommendations**: Hotel and attraction suggestions based on budget and interests
- **Route Optimization**: Efficient day-by-day planning with travel time optimization
- **Real-time Updates**: Live itinerary modifications and suggestions
- **Comprehensive APIs**: RESTful endpoints for all travel planning features

## 🛠️ Tech Stack

- **Framework**: FastAPI with async support
- **Language**: Python 3.9+
- **AI Integration**: LangChain + OpenAI GPT-3.5-turbo
- **Caching**: Redis for API response caching
- **APIs**: Google Maps, Yelp integration

## 📁 Project Structure

```
backend/
├── routes/             # API routes
│   ├── trips.py
│   ├── places.py
│   ├── hotels.py
│   ├── itinerary.py
│   └── ai.py
├── models/             # Pydantic schemas
├── services/           # Business logic
│   ├── llm_service.py
│   ├── mock_data.py
│   ├── google_maps.py
│   └── yelp_api.py
├── core/               # Configuration
│   └── config.py
└── main.py             # FastAPI application
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Maps API key
- OpenAI API key
- Yelp API key

### Installation

1. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:

   ```bash
   cp env.example .env
   ```

   Edit `.env` with your API keys:

   ```
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   OPENAI_API_KEY=your_openai_api_key
   YELP_API_KEY=your_yelp_api_key
   REDIS_URL=redis://localhost:6379
   ```

4. **Start the server**:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend will be available at `http://localhost:8000`

## 📚 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- `POST /api/trips` - Create a new trip
- `POST /api/hotels/search` - Search for hotels
- `POST /api/itinerary/generate` - Generate AI-powered itinerary
- `POST /api/ai/summarize` - AI-powered itinerary summarization

## 🧪 Testing

### Example API Calls

1. **Create a trip**:

   ```bash
   curl -X POST "http://localhost:8000/api/trips" \
        -H "Content-Type: application/json" \
        -d '{
          "location": "Paris, France",
          "start_date": "2024-06-01",
          "end_date": "2024-06-03",
          "budget": 2000,
          "travelers": 2,
          "interests": ["Culture & History", "Food & Dining"]
        }'
   ```

2. **Generate itinerary**:
   ```bash
   curl -X POST "http://localhost:8000/api/itinerary/generate" \
        -H "Content-Type: application/json" \
        -d '{
          "location": "Paris, France",
          "start_date": "2024-06-01",
          "end_date": "2024-06-03",
          "budget": 2000,
          "travelers": 2,
          "interests": ["Culture & History", "Food & Dining"]
        }'
   ```

## 🔧 Development

### Mock Data

The application uses real APIs with fallback to mock data. To integrate additional APIs:

1. **Google Maps API**: Update `services/google_maps.py` with real API calls
2. **Yelp API**: Already integrated in `services/yelp_api.py`
3. **Data Aggregation**: Centralized in `services/data_aggregation.py`

### LangChain Integration

The AI service (`services/llm_service.py`) uses LangChain with:

- **PromptTemplate**: For structured prompts
- **ChatOpenAI**: For LLM interactions
- **Async support**: For better performance

## 🚀 Deployment

### Render (Recommended)

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy automatically on push to main branch

### Docker

```bash
docker build -t autotrip-backend .
docker run -p 8000:8000 autotrip-backend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

# Financial Transcripts RAG Application

A Retrieval-Augmented Generation (RAG) application for querying and analyzing financial earnings call transcripts using ChromaDB for vector storage and Google's Gemini Pro for intelligent responses.

## 🚀 Overview

This application processes financial transcripts from major technology companies (AAPL, AMD, AMZN, ASML, CSCO, GOOGL, INTC, MSFT, MU, NVDA) spanning from 2016-2020, creates embeddings using state-of-the-art sentence transformers, and provides an intelligent query interface powered by Google's Gemini Pro model.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Transcripts   │───▶│   Embedding     │───▶│   ChromaDB      │
│   (.txt files)  │    │   (Sentence     │    │   (Vector       │
│                 │    │   Transformers) │    │   Storage)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │───▶│   FastAPI       │◄───│   Vector        │
│   Frontend      │    │   Backend       │    │   Similarity    │
│   (User Interface) │ │   (RAG Pipeline) │   │   Search        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │   Gemini Pro    │
         └──────────────│   (LLM)         │
                        └─────────────────┘
```

### Component Breakdown
- **Streamlit Frontend**: Interactive web interface for user queries and results
- **FastAPI Backend**: RESTful API handling RAG pipeline and business logic
- **ChromaDB**: Local vector database for embedding storage and retrieval
- **Sentence Transformers**: HuggingFace models for creating semantic embeddings
- **Gemini Pro**: Google's LLM for generating intelligent responses

## 📁 Project Structure

```
Project RAG/
├── README.md
├── LICENSE
├── Transcripts/           # Raw transcript files
│   ├── AAPL/             # Apple Inc. transcripts
│   ├── AMD/              # Advanced Micro Devices transcripts
│   ├── AMZN/             # Amazon transcripts
│   ├── ASML/             # ASML Holding transcripts
│   ├── CSCO/             # Cisco Systems transcripts
│   ├── GOOGL/            # Alphabet Inc. transcripts
│   ├── INTC/             # Intel Corporation transcripts
│   ├── MSFT/             # Microsoft transcripts
│   ├── MU/               # Micron Technology transcripts
│   └── NVDA/             # NVIDIA Corporation transcripts
├── backend/              # FastAPI Backend (to be created)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py       # FastAPI application entry point
│   │   ├── api/          # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── embeddings.py
│   │   │   ├── query.py
│   │   │   └── health.py
│   │   ├── core/         # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── rag_pipeline.py
│   │   ├── models/       # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── query.py
│   │   │   └── response.py
│   │   └── services/     # Business services
│   │       ├── __init__.py
│   │       ├── embedding_service.py
│   │       ├── chroma_service.py
│   │       └── gemini_service.py
│   └── requirements.txt  # Backend dependencies
├── frontend/             # Streamlit Frontend (to be created)
│   ├── app.py           # Streamlit application
│   ├── components/      # Reusable UI components
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── sidebar.py
│   │   └── results.py
│   ├── utils/           # Utility functions
│   │   ├── __init__.py
│   │   ├── api_client.py
│   │   └── formatters.py
│   └── requirements.txt # Frontend dependencies
├── scripts/             # Utility scripts (to be created)
│   ├── setup_embeddings.py
│   ├── data_loader.py
│   └── health_check.py
├── data/                # Processed data (to be created)
│   ├── chromadb/        # ChromaDB storage
│   └── embeddings/      # Generated embeddings cache
├── config/              # Configuration files (to be created)
│   ├── .env.example
│   └── settings.yaml
├── tests/               # Test suite (to be created)
│   ├── test_backend/
│   ├── test_frontend/
│   └── test_integration/
├── install.sh           # Main setup script for dependencies and environment
├── start.sh             # Main startup script for both services
├── backend/
│   ├── b_install.sh     # Backend-specific installation script
│   └── b_start.sh       # Backend-specific startup script
├── frontend/
│   ├── f_install.sh     # Frontend-specific installation script
│   └── f_start.sh       # Frontend-specific startup script
└── requirements.txt     # Root dependencies (to be created)
```

## 🛠️ Technology Stack

### Core Components
- **Frontend**: Streamlit - Interactive web interface
- **Backend API**: FastAPI - High-performance REST API
- **Vector Database**: ChromaDB (local deployment)
- **Embeddings**: Sentence Transformers (Hugging Face)
- **Language Model**: Google Gemini Pro
- **Data Processing**: pandas, numpy

### Key Libraries
#### Backend (FastAPI)
- `fastapi` - Modern, fast web framework for building APIs
- `uvicorn` - ASGI server for FastAPI
- `chromadb` - Vector database for embeddings storage
- `sentence-transformers` - Creating semantic embeddings
- `google-generativeai` - Gemini Pro integration
- `pydantic` - Data validation and serialization
- `python-multipart` - File upload support

#### Frontend (Streamlit)
- `streamlit` - Interactive web app framework
- `requests` - HTTP library for API communication
- `plotly` - Interactive visualizations
- `pandas` - Data manipulation and display

#### Shared
- `langchain` - RAG pipeline orchestration
- `numpy` - Numerical computations
- `python-dotenv` - Environment variable management

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8+
- Google API key for Gemini Pro
- 8GB+ RAM (recommended for local ChromaDB)

### Quick Start (Recommended)

1. **Clone and navigate to the project**
   ```bash
   cd "Project RAG"
   ```

2. **Set up Google API key**
   ```bash
   cp env.example .env
   # Edit .env file with your Google API key for Gemini Pro
   ```

3. **Run the installation script**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

4. **Start both services**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

5. **Access the application**
   - Frontend (Streamlit): http://localhost:8501
   - Backend API (FastAPI): http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Component-Specific Installation & Startup

For more granular control, you can install and start components separately:

#### Backend Only
```bash
# Install backend
chmod +x backend/b_install.sh
cd backend && ./b_install.sh && cd ..

# Start backend
chmod +x backend/b_start.sh
cd backend && ./b_start.sh && cd ..
```

#### Frontend Only
```bash
# Install frontend
chmod +x frontend/f_install.sh
cd frontend && ./f_install.sh && cd ..

# Start frontend
chmod +x frontend/f_start.sh
cd frontend && ./f_start.sh && cd ..
```

#### Component Script Options
- **Backend**: `cd backend && ./b_start.sh --background && cd ..` (run in background)
- **Backend**: `cd backend && ./b_start.sh --stop && cd ..` (stop background process)
- **Frontend**: `cd frontend && ./f_start.sh --port 8502 && cd ..` (use different port)
- **Both**: `cd backend && ./b_start.sh --help` or `cd frontend && ./f_start.sh --help` (see all options)

### Manual Installation (Alternative)

1. **Backend Setup (FastAPI)**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux (or venv\Scripts\activate on Windows)
   pip install -r requirements.txt
   ```

2. **Frontend Setup (Streamlit)**
   ```bash
   # Open new terminal window
   cd frontend
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux (or venv\Scripts\activate on Windows)
   pip install -r requirements.txt
   ```

3. **Initialize the database and create embeddings**
   ```bash
   cd backend
   source venv/bin/activate
   python ../scripts/setup_embeddings.py
   ```

4. **Manual startup (two terminals required)**
   
   **Terminal 1 - Start FastAPI Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   **Terminal 2 - Start Streamlit Frontend:**
   ```bash
   cd frontend
   source venv/bin/activate
   streamlit run app.py --server.port 8501
   ```

### Shell Scripts Overview

**`install.sh`** - Automated setup script that:
- Creates Python virtual environments for both backend and frontend
- Installs all dependencies from requirements.txt files
- Sets up ChromaDB directories
- Validates Python and pip versions
- Checks for required system dependencies

**`start.sh`** - Startup script that:
- Activates virtual environments
- Starts FastAPI backend in background
- Starts Streamlit frontend
- Provides graceful shutdown handling
- Shows service status and logs

## 📊 Data Overview

The application processes earnings call transcripts from 10 major technology companies:

| Company | Symbol | Transcripts | Period |
|---------|--------|-------------|--------|
| Apple Inc. | AAPL | 19 files | 2016-2020 |
| Advanced Micro Devices | AMD | 19 files | 2016-2020 |
| Amazon.com Inc. | AMZN | 19 files | 2016-2020 |
| ASML Holding N.V. | ASML | 19 files | 2016-2020 |
| Cisco Systems Inc. | CSCO | 19 files | 2016-2020 |
| Alphabet Inc. | GOOGL | 19 files | 2016-2020 |
| Intel Corporation | INTC | 19 files | 2016-2020 |
| Microsoft Corporation | MSFT | 19 files | 2016-2020 |
| Micron Technology | MU | 16 files | 2016-2020 |
| NVIDIA Corporation | NVDA | 19 files | 2016-2020 |

**Total**: ~187 earnings call transcripts

## 🧠 Embedding Strategy

### Model Selection
- **Primary Model**: `all-MiniLM-L6-v2`
  - 384-dimensional embeddings
  - Balanced performance and speed
  - Optimized for semantic similarity

### Processing Pipeline
1. **Text Preprocessing**
   - Remove special characters and formatting
   - Split into semantic chunks (512 tokens max)
   - Preserve company and date metadata

2. **Embedding Generation**
   - Process transcripts in batches
   - Generate embeddings for each chunk
   - Store with rich metadata

3. **ChromaDB Storage**
   - Create company-specific collections
   - Index by date and content type
   - Enable hybrid search capabilities

## 🔍 RAG Implementation

### Retrieval Strategy
- **Semantic Search**: Find contextually relevant transcript chunks
- **Hybrid Approach**: Combine semantic similarity with metadata filtering
- **Dynamic K**: Adjust number of retrieved documents based on query complexity

### Generation Enhancement
- **Context Augmentation**: Provide relevant transcript excerpts
- **Prompt Engineering**: Specialized prompts for financial analysis
- **Source Attribution**: Reference specific transcripts and dates

## 💡 Usage Examples

### Query Types Supported

1. **Company-Specific Analysis**
   ```
   "What were Apple's main concerns about supply chain in 2020?"
   ```

2. **Cross-Company Comparisons**
   ```
   "Compare NVIDIA and AMD's AI strategy discussions from 2019-2020"
   ```

3. **Temporal Analysis**
   ```
   "How did tech companies' cloud revenue discussions evolve from 2016 to 2020?"
   ```

4. **Financial Metrics**
   ```
   "What were the key revenue drivers mentioned by Microsoft in Q4 2019?"
   ```

5. **Strategic Insights**
   ```
   "Identify emerging technology trends discussed across all companies in 2020"
   ```

## 🚀 FastAPI Backend Endpoints

### Core Endpoints
- `POST /api/v1/query` - Submit RAG queries and get AI responses
- `GET /api/v1/companies` - List available companies and transcript counts
- `GET /api/v1/transcripts/{company}` - Get transcripts metadata for specific company
- `POST /api/v1/search` - Direct vector similarity search
- `GET /api/v1/embeddings/status` - Check embedding generation status
- `POST /api/v1/embeddings/create` - Trigger embedding creation for new transcripts
- `GET /health` - System health check and service status

### Request/Response Examples

#### Query Endpoint
**Request:**
```json
POST /api/v1/query
{
  "question": "What were Apple's main concerns about supply chain in 2020?",
  "company_filter": ["AAPL"],
  "date_range": {
    "start": "2020-01-01",
    "end": "2020-12-31"
  },
  "max_results": 5
}
```

**Response:**
```json
{
  "query": "What were Apple's main concerns about supply chain in 2020?",
  "answer": "Based on Apple's 2020 earnings calls, the main supply chain concerns were...",
  "sources": [
    {
      "company": "AAPL",
      "date": "2020-Jul-30",
      "quarter": "Q3 2020",
      "chunk": "relevant text excerpt about supply chain challenges",
      "similarity_score": 0.85,
      "document_id": "aapl_2020_q3_001"
    }
  ],
  "metadata": {
    "processing_time": "1.2s",
    "total_chunks_searched": 1250,
    "model_used": "all-MiniLM-L6-v2",
    "llm_model": "gemini-pro"
  }
}
```

### Streamlit Frontend Features
- **Interactive Chat Interface**: Real-time querying with conversation history
- **Company Selection**: Filter queries by specific companies
- **Date Range Picker**: Focus analysis on specific time periods
- **Results Visualization**: Rich display of sources and similarity scores
- **Export Functionality**: Download results as PDF or CSV
- **Response Streaming**: Real-time display of AI-generated responses

## 🎯 Performance Metrics

### Target Specifications
- **Query Response Time**: < 3 seconds
- **Embedding Accuracy**: > 85% relevance score
- **Database Size**: ~500MB (compressed embeddings)
- **Concurrent Users**: 10+ simultaneous queries

## 🔒 Configuration

### Environment Variables (.env)
```bash
# Google Gemini Pro API
GOOGLE_API_KEY=your_gemini_api_key

# ChromaDB Configuration
CHROMADB_PATH=./data/chromadb
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
BATCH_SIZE=32

# RAG Pipeline Settings
MAX_CHUNKS_PER_QUERY=5
SIMILARITY_THRESHOLD=0.7
TEMPERATURE=0.7

# FastAPI Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:8501"]

# Streamlit Configuration
FRONTEND_PORT=8501
BACKEND_URL=http://localhost:8000
```

### Service Architecture
- **Port 8000**: FastAPI backend server
- **Port 8501**: Streamlit frontend application
- **Communication**: Frontend makes HTTP requests to backend API
- **Data Flow**: Streamlit UI → FastAPI → ChromaDB → Gemini Pro → Response

## 🛠️ Shell Scripts

### Main Scripts

#### install.sh
Comprehensive setup script that automates the entire installation process:

**Features:**
- Python version validation (requires Python 3.8+)
- Automatic virtual environment creation for both services
- Dependency installation with error handling
- ChromaDB data directory setup
- Environment variable validation
- Uses component-specific scripts when available

**Usage:**
```bash
./install.sh           # Full installation
./install.sh --clean   # Clean previous installation
./install.sh --help    # Show help
```

#### start.sh
Production-ready startup script for running both services:

**Features:**
- Dual-service orchestration (backend + frontend)
- Background FastAPI server with PID tracking
- Foreground Streamlit interface
- Graceful shutdown handling (Ctrl+C)
- Service health checks and process monitoring
- Uses component-specific scripts when available

**Usage:**
```bash
./start.sh                    # Start both services
./start.sh --backend-only     # Start only backend
./start.sh --frontend-only    # Start only frontend
./start.sh --stop            # Stop all services
./start.sh --status          # Show service status
./start.sh --help            # Show help
```

### Component-Specific Scripts

#### Backend Scripts

**backend/b_install.sh** - Backend Installation
```bash
cd backend && ./b_install.sh           # Install backend dependencies
cd backend && ./b_install.sh --clean   # Clean backend installation
cd backend && ./b_install.sh --help    # Show help
```

**backend/b_start.sh** - Backend Startup
```bash
cd backend && ./b_start.sh                    # Start backend (foreground)
cd backend && ./b_start.sh --background       # Start backend (background)
cd backend && ./b_start.sh --port 8001        # Start on custom port
cd backend && ./b_start.sh --stop             # Stop background backend
cd backend && ./b_start.sh --status           # Show backend status
cd backend && ./b_start.sh --logs             # Show backend logs
cd backend && ./b_start.sh --help             # Show help
```

#### Frontend Scripts

**frontend/f_install.sh** - Frontend Installation
```bash
cd frontend && ./f_install.sh           # Install frontend dependencies
cd frontend && ./f_install.sh --clean   # Clean frontend installation
cd frontend && ./f_install.sh --help    # Show help
```

**frontend/f_start.sh** - Frontend Startup
```bash
cd frontend && ./f_start.sh                           # Start frontend
cd frontend && ./f_start.sh --port 8502               # Start on custom port
cd frontend && ./f_start.sh --backend http://api.com  # Use remote backend
cd frontend && ./f_start.sh --check-only              # Check prerequisites only
cd frontend && ./f_start.sh --help                    # Show help
```

## 🧪 Testing

### Test Categories
- Unit tests for embedding generation
- Integration tests for ChromaDB operations
- End-to-end RAG pipeline testing
- Performance benchmarking

### Run Tests
```bash
# Activate backend environment and run tests
cd backend
source venv/bin/activate
pytest ../tests/ -v

# Run performance benchmarks
python ../tests/benchmark.py
```

## 🔧 Service Management

### Starting Services
```bash
# Quick start (recommended)
./start.sh

# Manual start with logs
./start.sh --verbose

# Start individual services
./start.sh --backend-only
./start.sh --frontend-only
```

### Stopping Services
```bash
# Graceful shutdown (Ctrl+C in terminal running start.sh)
# Or use stop command
./start.sh --stop

# Force kill all related processes
pkill -f "uvicorn app.main:app"
pkill -f "streamlit run"
```

### Troubleshooting

**Port Already in Use:**
```bash
# Check what's using the ports
lsof -i :8000  # FastAPI
lsof -i :8501  # Streamlit

# Kill processes if needed
kill -9 $(lsof -t -i:8000)
kill -9 $(lsof -t -i:8501)
```

**Virtual Environment Issues:**
```bash
# Recreate environments
rm -rf backend/venv frontend/venv
./install.sh
```

**Dependency Conflicts:**
```bash
# Clean install
pip cache purge
./install.sh --clean
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📈 Roadmap

### Phase 1: Core Implementation ✅
- [x] FastAPI backend with RESTful API endpoints
- [x] Streamlit frontend with interactive UI
- [x] ChromaDB setup and embedding storage
- [x] Sentence transformer integration
- [x] Basic RAG pipeline
- [x] Gemini Pro integration

### Phase 2: Enhancement (Next)
- [ ] Advanced query processing with filters
- [ ] Real-time response streaming in Streamlit
- [ ] Conversation history and session management
- [ ] Enhanced UI with data visualizations
- [ ] Performance optimization and caching
- [ ] API authentication and rate limiting

### Phase 3: Advanced Features (Future)
- [ ] Fine-tuned embeddings for financial domain
- [ ] Multi-modal search capabilities (text + tables + charts)
- [ ] Automated insight generation and trending topics
- [ ] Real-time transcript ingestion pipeline
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Production deployment with process managers (PM2, systemd)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Hugging Face for sentence-transformers
- ChromaDB team for the vector database
- Google for Gemini Pro API
- Financial transcript data providers

## 📞 Support

For questions and support:
- Create an issue in the repository
- Check the documentation
- Review example queries

---

**Built with ❤️ for financial analysis and AI-powered insights**
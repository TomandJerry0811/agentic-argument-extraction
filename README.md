# 🗺️ Argument Cartographer

## Overview

The **Argument Cartographer** is an AI-powered web platform designed to deconstruct and visualize the logical structure of any topic. This sophisticated tool helps users understand complex arguments by breaking them down into structured, interactive visual maps.

### Core Capabilities
- **Multi-Input Analysis**: Analyze content from text, URLs, or uploaded documents (.txt, .pdf, .doc)
- **AI-Powered Logic Mapping**: Uses advanced AI to identify thesis, supporting claims, evidence, counterclaims, and logical fallacies
- **Interactive Visualizations**: Multiple viewing styles (Classic Tree, Org Chart, Pillar View)
- **Real-time Web Context**: Enhanced with current web information via DuckDuckGo search
- **Modern React Frontend**: Professional, responsive interface with real-time updates

## 🏗️ Technical Architecture

### System Components
1. **Backend**: Flask-based Python server with CORS support
2. **Frontend**: React TypeScript application with modern UI
3. **AI Integration**: Local AI model via Ollama (OpenAI-compatible API)
4. **Web Scraping**: DuckDuckGo news search and content extraction
5. **RAG Pipeline**: Retrieval-Augmented Generation for contextually rich responses

### Technology Stack
- **Backend**: Python 3.8+, Flask 2.3.3, Flask-CORS
- **Frontend**: React 18+, TypeScript, Modern CSS
- **AI Engine**: Ollama with Gemma3/Llama3.1 model
- **Web Scraping**: BeautifulSoup4, DuckDuckGo Search (ddgs)
- **Data Processing**: JSON parsing, structured output validation

## 📋 Prerequisites

Before starting, ensure you have:

### Required Software
- **Python 3.8+** ([Download here](https://python.org/downloads/))
- **Node.js 16+** ([Download here](https://nodejs.org/))
- **Git** ([Download here](https://git-scm.com/))
- **Ollama** ([Download here](https://ollama.ai/))

### System Requirements
- 8GB+ RAM (for AI model)
- 10GB+ free disk space
- Stable internet connection
- Modern web browser (Chrome, Firefox, Safari, Edge)

## 🚀 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/BHARTIYAYASH/Argument-Cartographer.git
cd Argument-Cartographer
```

### Step 2: Backend Setup (Python/Flask)

#### Create Virtual Environment
```bash
python -m venv env
```

#### Activate Virtual Environment
**Windows (PowerShell):**
```bash
env\Scripts\activate
```

**macOS/Linux:**
```bash
source env/bin/activate
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: AI Model Setup (Ollama)

#### Install and Start Ollama
1. Download and install Ollama from [ollama.ai](https://ollama.ai/)
2. Start Ollama service:
   ```bash
   ollama serve
   ```

#### Pull Required AI Model
```bash
# Pull Gemma3 model (recommended)
ollama pull gemma3

# OR pull Llama3.1 as alternative
ollama pull llama3.1
```

#### Verify Ollama is Running
```bash
curl http://localhost:11434/v1/models
```
You should see a JSON response with available models.

### Step 4: Frontend Setup (React)

#### Navigate to Frontend Directory
```bash
cd frontend
```

#### Install Node Dependencies
```bash
npm install
```

### Step 5: Configure Application

#### Update IP Whitelist (Optional)
Edit `pap.py` to add your IP address to the `ALLOWED_IPS` list:
```python
ALLOWED_IPS = ['127.0.0.1', 'YOUR_IP_ADDRESS_HERE']
```

## 🎯 Running the Application

**⚠️ IMPORTANT: Use only `pap.py` as the main backend file. Do not use `app.py` or other Python files.**

### Step 1: Start Ollama AI Service
```bash
ollama serve
```
Leave this terminal running.

### Step 2: Start Flask Backend
Open a new terminal, navigate to the project root, and activate the virtual environment:
```bash
cd Argument-Cartographer
env\Scripts\activate  # Windows
# OR
source env/bin/activate  # macOS/Linux

# Run the main backend file
python pap.py
```

The backend will start at: `http://localhost:5000`

### Step 3: Start React Frontend
Open another terminal:
```bash
cd Argument-Cartographer/frontend
npm start
```

The frontend will start at: `http://localhost:3000`

### Step 4: Access the Application
Open your browser and go to: **http://localhost:3000**

## 📖 How to Use

### Basic Usage
1. **Enter a Question/Topic**: Type your research question or topic
2. **Choose Input Method**:
   - **📝 Text**: Paste content directly or leave empty for web search
   - **🔗 URL**: Enter a webpage URL to analyze
   - **📄 Document**: Upload a .txt, .pdf, or .doc file
3. **Click "🚀 Analyze Arguments"**
4. **View Results**: Explore the interactive argument map
5. **Change Visualization**: Use the dropdown to switch between styles

### Example Queries
- "AI regulation in Europe 2024"
- "Climate change arguments and evidence"
- "Cryptocurrency adoption benefits and risks"
- "Social media impact on mental health"

## 🔧 Troubleshooting

### Common Issues

**1. CORS/Network Errors**
- Ensure Flask backend is running on port 5000
- Check that CORS is properly configured in `pap.py`
- Verify your IP is in the `ALLOWED_IPS` list

**2. AI Model Connection Failed**
- Make sure Ollama is running: `ollama serve`
- Check if model is installed: `ollama list`
- Test AI endpoint: `curl http://localhost:11434/v1/models`

**3. Web Scraping Issues**
- Check internet connection
- Some websites may block scraping
- Try different URLs or use text input instead

**4. Frontend Not Loading**
- Ensure Node.js dependencies are installed: `npm install`
- Check if port 3000 is available
- Clear browser cache and reload

### Diagnostic Commands

```bash
# Check if backend is running
curl http://localhost:5000/

# Check if AI model is accessible
curl http://localhost:11434/v1/models

# Test backend API
curl -X POST "http://localhost:5000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"test query"}'
```

## 📁 Project Structure

```
Argument-Cartographer/
├── 📄 pap.py                     # ⭐ MAIN BACKEND FILE (USE THIS)
├── 📄 requirements.txt           # Python dependencies
├── 📄 README.md                  # This file
├── 📁 frontend/                  # React TypeScript application
│   ├── 📁 src/
│   │   ├── 📁 components/        # React components
│   │   ├── 📁 services/          # API integration
│   │   ├── 📁 types/             # TypeScript interfaces
│   │   └── 📄 App.tsx            # Main React component
│   ├── 📄 package.json          # Node.js dependencies
│   └── 📄 public/               # Static assets
├── 📁 static/                    # Legacy static files
│   ├── 📁 css/
│   └── 📁 js/
├── 📁 templates/                 # Legacy templates
└── 📄 Other files...            # Additional project files
```

## 🔒 Security Notes

- **IP Whitelisting**: Only specified IPs can access the API
- **CORS Configuration**: Properly configured for frontend-backend communication
- **Input Validation**: All user inputs are validated and sanitized
- **No Persistent Storage**: Stateless operation for security

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Flask**: Lightweight web framework
- **React**: Modern frontend library
- **Ollama**: Local AI model hosting
- **DuckDuckGo**: Privacy-focused search API
- **BeautifulSoup**: Web scraping library

## 📞 Support

If you encounter issues:

1. Check this README first
2. Look at the troubleshooting section
3. Create an issue on GitHub
4. Include error messages and system info

---

**Happy Argument Mapping! 🗺️✨**
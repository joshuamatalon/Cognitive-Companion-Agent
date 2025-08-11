# 🧠 Cognitive Companion Agent

> Your intelligent knowledge companion powered by AI

A sophisticated Retrieval-Augmented Generation (RAG) application that transforms how you interact with knowledge. Built with modern AI technologies and featuring a professional, intuitive interface.

![Version](https://img.shields.io/badge/version-1.2-blue.svg)
![Release](https://img.shields.io/badge/production--ready-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.11+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/framework-streamlit-red.svg)

## ✨ Features

### 🔍 **Intelligent Knowledge Management**
- **Smart PDF Ingestion**: Upload and process documents with progress tracking
- **OCR Support**: Extract text from scanned PDFs using advanced OCR technology
- **Advanced Search**: Semantic search through your knowledge base
- **AI-Powered Answers**: Get informed responses based on your stored content
- **Memory Management**: Organize, view, and delete knowledge entries

### 🎨 **Professional Interface**
- **Modern UI Design**: Beautiful gradient themes and card-based layouts
- **Responsive Layout**: Works seamlessly across different screen sizes  
- **Interactive Elements**: Hover effects, animations, and smooth transitions
- **Real-time Feedback**: Progress indicators and status updates

### 🔒 **Enterprise-Grade Security**
- **Secure API Key Management**: Centralized configuration with validation
- **Pre-commit Security Hooks**: Automatic detection of hardcoded secrets
- **Input Sanitization**: Protection against malicious inputs
- **Safe Error Handling**: No sensitive information leakage
- **Cross-platform Path Security**: No hardcoded user paths

### 📊 **Advanced Analytics**
- **Search Metrics**: Track your knowledge exploration
- **System Health**: Real-time status monitoring
- **Usage Statistics**: Insights into your knowledge interactions
- **Export Capabilities**: Backup your entire knowledge base

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- OpenAI API key
- Pinecone API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/joshuamatalon/Cognitive-Companion-Agent.git
   cd Cognitive-Companion-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**
   
   **🎯 Easy Launch Options:**
   
   **Windows Users (Recommended):**
   - **Double-click `launch.bat`** - Easiest way to start the app
   - **PowerShell:** Double-click `RunApp.ps1` for virtual environment support
   - **Desktop Shortcut:** Right-click `launch.bat` → Create shortcut → Drag to desktop
   
   **Mac/Linux Users:**
   - **Terminal:** `streamlit run app.py`
   - **Virtual Environment:** Activate your venv first, then run the above command
   
   **Manual Method:**
   ```bash
   streamlit run app.py
   ```

### Environment Setup

Create a `.env` file with your API credentials:

```env
OPENAI_API_KEY=your-openai-api-key-here
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENV=us-east-1
```

### Optional: OCR Support

For scanned PDF processing, install additional OCR dependencies:

```bash
# Install OCR packages
pip install pytesseract pdf2image pillow

# Install Tesseract OCR (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Or use: winget install UB-Mannheim.TesseractOCR

# Install Poppler (Windows) 
# Download from: https://github.com/oschwartz10612/poppler-windows
```

The app will automatically detect and use OCR capabilities if available.

## 🎯 How It Works

1. **📥 Ingest Knowledge**: Upload PDFs or manually add notes, facts, and insights
2. **🧠 AI Processing**: Content is chunked, embedded, and stored in vector database
3. **🔍 Smart Search**: Semantic search finds relevant context for your questions
4. **💬 Intelligent Answers**: RAG system provides informed responses using your knowledge
5. **📊 Track & Manage**: Monitor usage, manage memories, and export data

## 🛠 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│  RAG Pipeline   │────│  Vector Store   │
│  (Frontend)     │    │   (Backend)     │    │   (Pinecone)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ├─ PDF Processing       ├─ OpenAI Embeddings    ├─ Semantic Search
         ├─ User Interface       ├─ Context Retrieval    ├─ Memory Storage
         └─ Session Management   └─ Answer Generation    └─ Data Persistence
```

## 🔧 Configuration

### API Keys
The application uses a centralized configuration system (`config.py`) that:
- Validates API key formats
- Provides helpful error messages
- Masks sensitive information in logs
- Supports environment variable overrides

### Customization
- **Chunk Size**: Adjust PDF processing chunk sizes
- **Search Results**: Configure number of results returned
- **UI Theme**: Modify CSS in `app.py` for custom styling
- **Memory Types**: Add custom knowledge categories

## 📚 Documentation

- **Security**: Pre-commit hooks automatically scan for exposed API keys
- **Installation Guide**: [Quick Start](#quick-start) - Step-by-step setup
- **Architecture Overview**: [System Architecture](#architecture) - Design and components
- **Launcher Scripts**: Use `launch.bat` (Windows) or `RunApp.ps1` (PowerShell)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - For GPT models and embeddings
- **Pinecone** - For vector database technology  
- **Streamlit** - For the beautiful web framework
- **LangChain** - For RAG pipeline components

## 📧 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/joshuamatalon/Cognitive-Companion-Agent/issues).

---

<div align="center">

**Built with ❤️ for intelligent knowledge interaction**

[🚀 Live Demo](#) • [📖 Documentation](#) • [🐛 Report Bug](https://github.com/joshuamatalon/Cognitive-Companion-Agent/issues)

</div>
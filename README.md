# DCPR 2034 Bot

A RAG (Retrieval Augmented Generation) system for the Mumbai Development Control and Promotion Regulations 2034. This bot uses **Self-Querying** to filter regulations by Zone (Island City, Suburbs) and Category (Residential, Commercial, etc.) before providing an answer.

## Project Structure

### **1. Core Infrastructure (`core/`)**
*   **`core/ingestion.py`**: Handles parsing the PDF and building the vector database.
    *   Uses `LlamaParse` to convert PDF tables to Markdown.
    *   Injects metadata (Zone, Category) into chunks for self-querying.
    *   Creates embeddings and saves the FAISS index.
*   **`core/retrieval.py`**: The brain of the retrieval system.
    *   Implements `SelfQueryRetriever` to filter data based on user questions.
    *   Uses a `FunctionalTranslator` to make LangChain queries compatible with FAISS.
    *   Applies a Cross-Encoder Reranker to surface the most relevant legal clauses.

### **2. Domain Logic (`domain/`)**
*   **`domain/config.py`**: Central configuration file (Paths, Model names, API Keys).
*   **`domain/prompts.py`**: Contains the "Senior Legal Analyst" system prompt.
*   **`domain/metadata_schema.py`**: Defines the fields (`zone`, `category`, `road_width`) that the AI can use for filtering.

### **3. Application**
*   **`app.py`**: The Streamlit user interface. Connects the user input to the RAG chain and displays answers with source citations.
*   **`.env`**: Stores your API keys (`ANTHROPIC_API_KEY`, `LLAMA_CLOUD_API_KEY`). **Do not share this file.**
*   **`requirements.txt`**: List of all Python dependencies.

---

## How to Run

### **Prerequisites**
1.  **Python 3.9+** installed.
2.  **API Keys** for Anthropic and LlamaCloud in your `.env` file.

### **Step 1: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 2: Ingest the Data (Build the Brain)**
Run this command whenever you change the PDF or the ingestion logic. It creates the `faiss_index` folder.
```bash
python -m core.ingestion
```
*Note: This uses the `LlamaParse` API and may take a few minutes.*

### **Step 3: Run the Chatbot**
Start the web interface.
```bash
streamlit run app.py
```

## Common Issues
*   **Model Not Found (404)**: If you see an error about the Claude model, check `domain/config.py` and ensure `LLM_MODEL` is set to a model you have access to (e.g., `claude-sonnet-4-5-20250929` or `claude-3-5-sonnet-20240620`).
*   **Module Not Found**: Always run the ingestion script as a module (`python -m core.ingestion`) from the root directory, not by entering the `core` folder.

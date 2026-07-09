import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from legal_engine import create_legal_graph, process_legal_document
# Load it
load_dotenv()

# CLEAN the key immediately after loading
if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY").strip()# 2. Now import the graph and processing logic
try:
    from legal_engine import create_legal_graph, process_legal_document
except ImportError as e:
    print(f"Import Error: {e}")
    raise

app = Flask(__name__)

# Initialize the Multi-Agent Graph
# This will trigger LegalAgents() __init__
graph = create_legal_graph()

# --- Database Setup ---
def init_db():
    """Initializes the SQLite database for legal metadata."""
    conn = sqlite3.connect('legal_docs.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS legal_metadata 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  filename TEXT, 
                  court TEXT, 
                  year INTEGER, 
                  category TEXT)''')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# --- Routes ---

@app.route('/')
def index():
    """Serves the main frontend dashboard."""
    return render_template('index.html')



@app.route('/upload', methods=['POST'])
def upload_doc():
    """Stores document metadata in SQLite."""
    data = request.json
    try:
        conn = sqlite3.connect('legal_docs.db')
        c = conn.cursor()
        c.execute('''INSERT INTO legal_metadata (filename, court, year, category) 
                     VALUES (?, ?, ?, ?)''',
                  (data['name'], data['court'], data['year'], data['category']))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Document '{data['name']}' indexed in metadata store."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_legal_ai():
    data = request.json
    user_query = data.get('query')
    
    try:
        inputs = {"query": user_query}
        # This is where the crash usually happens
        result = graph.invoke(inputs) 
        
        return jsonify({
            "answer": result.get('final_response'),
            "status": "Success"
        })
    except Exception as e:
        # THIS WILL PRINT THE ACTUAL ERROR IN YOUR TERMINAL
        print(f"CRITICAL ERROR DURING GRAPH INVOKE: {str(e)}") 
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    init_db()
    # Run Flask on port 5000
    app.run(debug=True, port=5000)

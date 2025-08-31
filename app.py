"""
Flask Application: Idea-to-UI Generator with Iterative Refinement
Users can provide their own Gemini API key and refine generated UIs
"""

import os
import json
import re
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import google.generativeai as genai
from datetime import datetime
import secrets

app = Flask(__name__)
CORS(app)

# Set a secret key for session management
app.secret_key = secrets.token_hex(16)

# Create directory for saving generated files
UPLOAD_FOLDER = 'generated_uis'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Store current code in memory (in production, use Redis or similar)
current_sessions = {}

# HTML template for the main page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Idea-to-UI Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            text-align: center;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            text-align: center;
            color: #666;
            font-size: 1.1rem;
        }
        
        .api-key-section {
            background: rgba(255, 255, 255, 0.98);
            margin: 2rem auto;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            max-width: 600px;
            transition: all 0.3s ease;
        }
        
        .api-key-section.collapsed {
            padding: 1rem;
            background: rgba(255, 255, 255, 0.9);
        }
        
        .api-key-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .api-key-section.collapsed .api-key-header {
            margin-bottom: 0;
        }
        
        .api-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            background: #f0f0f0;
        }
        
        .api-status.connected {
            background: #d4f4dd;
            color: #2e7d32;
        }
        
        .api-status.disconnected {
            background: #ffebee;
            color: #c62828;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .api-key-content {
            display: block;
        }
        
        .api-key-section.collapsed .api-key-content {
            display: none;
        }
        
        .api-key-info {
            background: #f7f9fc;
            border-left: 4px solid #667eea;
            padding: 1rem;
            margin-bottom: 1.5rem;
            border-radius: 4px;
        }
        
        .api-key-info h3 {
            color: #667eea;
            margin-bottom: 0.5rem;
            font-size: 1rem;
        }
        
        .api-key-info ol {
            margin-left: 1.5rem;
            color: #555;
            line-height: 1.8;
        }
        
        .api-key-info a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        
        .api-key-info a:hover {
            text-decoration: underline;
        }
        
        .api-input-group {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .api-input-wrapper {
            flex: 1;
            position: relative;
        }
        
        .api-input {
            width: 100%;
            padding: 0.75rem 2.5rem 0.75rem 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            font-family: monospace;
            transition: border-color 0.3s;
        }
        
        .api-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .toggle-visibility {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            cursor: pointer;
            color: #666;
            font-size: 1.2rem;
        }
        
        .connect-btn {
            padding: 0.75rem 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .connect-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .connect-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .main-content {
            display: none;
            animation: fadeIn 0.5s ease;
        }
        
        .main-content.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .container {
            display: flex;
            max-width: 100%;
            margin: 2rem;
            gap: 2rem;
        }
        
        .input-panel {
            flex: 0 0 400px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            max-height: calc(100vh - 200px);
            overflow-y: auto;
        }
        
        .preview-panel {
            flex: 1;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 600;
            font-size: 1rem;
        }
        
        .form-group textarea {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            resize: vertical;
            min-height: 120px;
            transition: border-color 0.3s;
        }
        
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .prompt-enhance-toggle {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            padding: 0.75rem;
            background: #f0f4f8;
            border-radius: 8px;
        }
        
        .prompt-enhance-toggle input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        .prompt-enhance-toggle label {
            cursor: pointer;
            font-size: 0.95rem;
            color: #555;
            margin: 0;
        }
        
        .examples {
            background: #f7f7f7;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }
        
        .examples h3 {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .example-btn {
            display: block;
            width: 100%;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            cursor: pointer;
            text-align: left;
            font-size: 0.9rem;
            transition: all 0.3s;
        }
        
        .example-btn:hover {
            background: #667eea;
            color: white;
            transform: translateX(5px);
        }
        
        .generate-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            margin-bottom: 1rem;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .generate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Refinement Section Styles */
        .refinement-section {
            display: none;
            background: linear-gradient(135deg, #f0f4f8 0%, #e8ecf1 100%);
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 1.5rem;
            border: 2px solid #667eea;
            animation: slideIn 0.3s ease;
        }
        
        .refinement-section.active {
            display: block;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .refinement-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            color: #667eea;
        }
        
        .refinement-header h3 {
            font-size: 1.1rem;
            margin: 0;
        }
        
        .refinement-textarea {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #667eea;
            border-radius: 6px;
            font-size: 0.95rem;
            min-height: 80px;
            resize: vertical;
            transition: all 0.3s;
        }
        
        .refinement-textarea:focus {
            outline: none;
            border-color: #764ba2;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .refinement-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .refine-btn {
            flex: 1;
            padding: 0.75rem;
            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .refine-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        
        .refine-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .regenerate-btn {
            flex: 1;
            padding: 0.75rem;
            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .regenerate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
        }
        
        .history-badge {
            background: #667eea;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-left: auto;
        }
        
        .suggestion-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }
        
        .suggestion-chip {
            padding: 0.4rem 0.8rem;
            background: white;
            border: 1px solid #667eea;
            border-radius: 20px;
            font-size: 0.85rem;
            color: #667eea;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .suggestion-chip:hover {
            background: #667eea;
            color: white;
            transform: scale(1.05);
        }
        
        .action-buttons {
            display: flex;
            gap: 1rem;
            margin-top: auto;
            padding-top: 1rem;
        }
        
        .action-btn {
            flex: 1;
            padding: 0.75rem;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .action-btn:hover {
            background: #667eea;
            color: white;
        }
        
        .action-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .preview-header {
            background: #f7f7f7;
            padding: 1rem;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .preview-header h2 {
            font-size: 1.2rem;
            color: #333;
        }
        
        .preview-controls {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        
        .preview-control-btn {
            padding: 0.5rem 1rem;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.3s;
        }
        
        .preview-control-btn:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .version-indicator {
            padding: 0.25rem 0.75rem;
            background: #e8f5e9;
            color: #2e7d32;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .preview-content {
            flex: 1;
            position: relative;
            background: white;
        }
        
        #preview-iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            flex-direction: column;
            gap: 1rem;
        }
        
        .loading-overlay.active {
            display: flex;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        .loading-text {
            color: #667eea;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .code-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 2000;
            justify-content: center;
            align-items: center;
        }
        
        .code-modal.active {
            display: flex;
        }
        
        .modal-content {
            background: white;
            border-radius: 12px;
            width: 80%;
            max-width: 800px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
        }
        
        .modal-header {
            padding: 1.5rem;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-body {
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
        }
        
        .code-block {
            background: #f7f7f7;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
        }
        
        .code-block pre {
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }
        
        .close-btn {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #666;
        }
        
        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            display: none;
        }
        
        .error-message.active {
            display: block;
        }
        
        .disconnect-btn {
            background: #ff5252;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .disconnect-btn:hover {
            background: #ff1744;
        }
        
        .enhanced-prompt-display {
            background: #e8f5e9;
            border: 1px solid #4caf50;
            border-radius: 6px;
            padding: 0.75rem;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: #2e7d32;
            display: none;
        }
        
        .enhanced-prompt-display.active {
            display: block;
        }
        
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
                margin: 1rem;
            }
            
            .input-panel {
                flex: none;
                width: 100%;
                max-height: none;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Idea-to-UI Generator</h1>
        <p>Transform your ideas into working UI prototypes with Google Gemini AI</p>
    </div>
    
    <!-- API Key Setup Section -->
    <div class="api-key-section" id="apiKeySection">
        <div class="api-key-header">
            <div class="api-status disconnected" id="apiStatus">
                <span class="status-dot"></span>
                <span id="statusText">Not Connected</span>
            </div>
            <button class="disconnect-btn" id="disconnectBtn" style="display: none;" onclick="disconnect()">Disconnect</button>
        </div>
        
        <div class="api-key-content" id="apiKeyContent">
            <div class="api-key-info">
                <h3>🔑 Get Started with Your Gemini API Key</h3>
                <ol>
                    <li>Get your free API key from <a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a></li>
                    <li>Paste your API key below</li>
                    <li>Click Connect to start generating UIs!</li>
                </ol>
                <p style="margin-top: 1rem; font-size: 0.9rem; color: #666;">
                    ✅ Your API key is never stored and only used for this session
                </p>
            </div>
            
            <div class="api-input-group">
                <div class="api-input-wrapper">
                    <input 
                        type="password" 
                        id="apiKeyInput" 
                        class="api-input" 
                        placeholder="Enter your Gemini API key..."
                        autocomplete="off"
                    >
                    <button class="toggle-visibility" onclick="toggleApiKeyVisibility()">👁️</button>
                </div>
                <button class="connect-btn" onclick="connectAPI()">Connect</button>
            </div>
            
            <div class="error-message" id="errorMessage"></div>
        </div>
    </div>
    
    <!-- Main Application (Hidden until API key is provided) -->
    <div class="main-content" id="mainContent">
        <div class="container">
            <div class="input-panel">
                <div class="form-group">
                    <label for="description">Describe Your UI:</label>
                    <textarea id="description" placeholder="Example: Create a modern dashboard with a dark sidebar, three colorful charts showing sales data, and a header with user profile..."></textarea>
                </div>
                
                <div class="prompt-enhance-toggle">
                    <input type="checkbox" id="enhancePrompt" checked>
                    <label for="enhancePrompt">🚀 Auto-enhance prompt for better results</label>
                </div>
                
                <div class="enhanced-prompt-display" id="enhancedPromptDisplay">
                    <strong>Enhanced prompt:</strong> <span id="enhancedText"></span>
                </div>
                
                <div class="examples">
                    <h3>Quick Examples</h3>
                    <button class="example-btn" onclick="setExample('finance')">📊 Finance Dashboard</button>
                    <button class="example-btn" onclick="setExample('blog')">📝 Blog Homepage</button>
                    <button class="example-btn" onclick="setExample('ecommerce')">🛒 E-commerce Product Page</button>
                    <button class="example-btn" onclick="setExample('portfolio')">💼 Portfolio Website</button>
                    <button class="example-btn" onclick="setExample('landing')">🚀 SaaS Landing Page</button>
                </div>
                
                <button class="generate-btn" onclick="generateUI()">Generate UI</button>
                
                <!-- Refinement Section -->
                <div class="refinement-section" id="refinementSection">
                    <div class="refinement-header">
                        <h3>🔧 Refine Your UI</h3>
                        <span class="history-badge" id="versionBadge">v1</span>
                    </div>
                    
                    <p style="font-size: 0.9rem; color: #666; margin-bottom: 0.75rem;">
                        Found an issue? Describe what needs to be fixed or improved:
                    </p>
                    
                    <div class="suggestion-chips">
                        <button class="suggestion-chip" onclick="addSuggestion('Make the colors more vibrant')">🎨 More vibrant colors</button>
                        <button class="suggestion-chip" onclick="addSuggestion('Add more spacing between elements')">📐 Better spacing</button>
                        <button class="suggestion-chip" onclick="addSuggestion('Make it mobile responsive')">📱 Mobile responsive</button>
                        <button class="suggestion-chip" onclick="addSuggestion('Add animations')">✨ Add animations</button>
                        <button class="suggestion-chip" onclick="addSuggestion('Fix the layout')">🔧 Fix layout</button>
                    </div>
                    
                    <textarea 
                        id="refinementPrompt" 
                        class="refinement-textarea" 
                        placeholder="e.g., Change the sidebar color to dark blue, make the charts bigger, add a footer with contact info..."
                    ></textarea>
                    
                    <div class="refinement-buttons">
                        <button class="refine-btn" onclick="refineUI()">
                            🔧 Apply Fixes
                        </button>
                        <button class="regenerate-btn" onclick="regenerateUI()">
                            🔄 Regenerate
                        </button>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button class="action-btn" id="viewCodeBtn" onclick="viewCode()" disabled>View Code</button>
                    <button class="action-btn" id="downloadBtn" onclick="downloadCode()" disabled>Download</button>
                </div>
            </div>
            
            <div class="preview-panel">
                <div class="preview-header">
                    <h2>Live Preview</h2>
                    <div class="preview-controls">
                        <span class="version-indicator" id="versionIndicator" style="display: none;">Version 1</span>
                        <button class="preview-control-btn" onclick="resetPreview()">🔄 Reset</button>
                        <span id="status">Ready</span>
                    </div>
                </div>
                <div class="preview-content">
                    <iframe 
                        id="preview-iframe" 
                        sandbox="allow-scripts allow-forms allow-same-origin allow-modals allow-popups"
                        srcdoc="<html><body style='display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; color: #999;'><h2>Your UI will appear here...</h2></body></html>">
                    </iframe>
                    <div class="loading-overlay" id="loading">
                        <div class="spinner"></div>
                        <div class="loading-text" id="loadingText">Generating...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Code Modal -->
    <div class="code-modal" id="codeModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Generated Code</h2>
                <button class="close-btn" onclick="closeModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="code-block">
                    <pre id="codeContent"></pre>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentCode = '';
        let apiKey = '';
        let isConnected = false;
        let sessionId = '';
        let currentVersion = 0;
        
        // Generate a unique session ID
        function generateSessionId() {
            return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        
        const examples = {
            finance: "Create a finance dashboard with a dark blue sidebar on the left containing menu items for Dashboard, Transactions, Analytics, and Settings. The main area should have three colorful charts: a line chart showing revenue trends, a bar chart for monthly expenses, and a pie chart for portfolio distribution. Add a top header with the company name and user profile section.",
            blog: "Design a clean blog homepage with a large hero section featuring a background image and the blog title. Below that, create a grid of blog post cards with featured images, titles, excerpts, and read more buttons. Include a sticky navigation bar with Home, Articles, About, and Contact links.",
            ecommerce: "Build an e-commerce product page with a large product image gallery on the left and product details on the right including title, price, description, size selector, quantity input, and an add to cart button. Include customer reviews section below with star ratings.",
            portfolio: "Create a modern portfolio website with a hero section containing name and title, an about section with skills, a projects grid showcasing work with hover effects, and a contact form at the bottom. Use a gradient background and smooth animations.",
            landing: "Design a SaaS landing page with a navigation bar, hero section with headline and CTA buttons, features section with icons and descriptions in a grid, pricing cards with different tiers, testimonials carousel, and a footer with links and newsletter signup."
        };
        
        function toggleApiKeyVisibility() {
            const input = document.getElementById('apiKeyInput');
            const button = event.target;
            if (input.type === 'password') {
                input.type = 'text';
                button.textContent = '🙈';
            } else {
                input.type = 'password';
                button.textContent = '👁️';
            }
        }
        
        async function connectAPI() {
            const apiKeyInput = document.getElementById('apiKeyInput');
            const errorMessage = document.getElementById('errorMessage');
            const connectBtn = event.target;
            
            apiKey = apiKeyInput.value.trim();
            
            if (!apiKey) {
                showError('Please enter your Gemini API key');
                return;
            }
            
            connectBtn.disabled = true;
            connectBtn.textContent = 'Connecting...';
            errorMessage.classList.remove('active');
            
            try {
                // Test the API key
                const response = await fetch('/test-api-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ api_key: apiKey })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Successfully connected
                    isConnected = true;
                    sessionId = generateSessionId();
                    showConnected();
                } else {
                    showError(data.error || 'Invalid API key. Please check and try again.');
                }
            } catch (error) {
                showError('Failed to connect. Please check your API key and try again.');
            } finally {
                connectBtn.disabled = false;
                connectBtn.textContent = 'Connect';
            }
        }
        
        function showConnected() {
            const apiKeySection = document.getElementById('apiKeySection');
            const mainContent = document.getElementById('mainContent');
            const apiStatus = document.getElementById('apiStatus');
            const statusText = document.getElementById('statusText');
            const disconnectBtn = document.getElementById('disconnectBtn');
            const apiKeyContent = document.getElementById('apiKeyContent');
            
            apiKeySection.classList.add('collapsed');
            mainContent.classList.add('active');
            apiStatus.classList.remove('disconnected');
            apiStatus.classList.add('connected');
            statusText.textContent = 'Connected';
            disconnectBtn.style.display = 'block';
            apiKeyContent.style.display = 'none';
        }
        
        function disconnect() {
            const apiKeySection = document.getElementById('apiKeySection');
            const mainContent = document.getElementById('mainContent');
            const apiStatus = document.getElementById('apiStatus');
            const statusText = document.getElementById('statusText');
            const disconnectBtn = document.getElementById('disconnectBtn');
            const apiKeyContent = document.getElementById('apiKeyContent');
            const apiKeyInput = document.getElementById('apiKeyInput');
            
            apiKey = '';
            isConnected = false;
            sessionId = '';
            currentVersion = 0;
            apiKeyInput.value = '';
            currentCode = '';
            
            // Hide refinement section
            document.getElementById('refinementSection').classList.remove('active');
            
            apiKeySection.classList.remove('collapsed');
            mainContent.classList.remove('active');
            apiStatus.classList.add('disconnected');
            apiStatus.classList.remove('connected');
            statusText.textContent = 'Not Connected';
            disconnectBtn.style.display = 'none';
            apiKeyContent.style.display = 'block';
        }
        
        function showError(message) {
            const errorMessage = document.getElementById('errorMessage');
            errorMessage.textContent = message;
            errorMessage.classList.add('active');
        }
        
        function setExample(type) {
            document.getElementById('description').value = examples[type];
        }
        
        function addSuggestion(text) {
            const refinementPrompt = document.getElementById('refinementPrompt');
            if (refinementPrompt.value) {
                refinementPrompt.value += '. ' + text;
            } else {
                refinementPrompt.value = text;
            }
        }
        
        function resetPreview() {
            const iframe = document.getElementById('preview-iframe');
            if (currentCode) {
                iframe.srcdoc = currentCode;
            } else {
                iframe.srcdoc = "<html><body style='display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; color: #999;'><h2>Your UI will appear here...</h2></body></html>";
            }
        }
        
        async function generateUI() {
            if (!isConnected || !apiKey) {
                alert('Please connect your Gemini API key first!');
                return;
            }
            
            const description = document.getElementById('description').value;
            if (!description.trim()) {
                alert('Please describe your UI idea first!');
                return;
            }
            
            const enhancePrompt = document.getElementById('enhancePrompt').checked;
            const loadingOverlay = document.getElementById('loading');
            const loadingText = document.getElementById('loadingText');
            const generateBtn = document.querySelector('.generate-btn');
            const status = document.getElementById('status');
            const viewCodeBtn = document.getElementById('viewCodeBtn');
            const downloadBtn = document.getElementById('downloadBtn');
            const enhancedPromptDisplay = document.getElementById('enhancedPromptDisplay');
            const enhancedText = document.getElementById('enhancedText');
            
            loadingOverlay.classList.add('active');
            loadingText.textContent = 'Generating your UI...';
            generateBtn.disabled = true;
            status.textContent = 'Generating...';
            
            // Reset version
            currentVersion = 1;
            
            // Show enhanced prompt if enabled
            if (enhancePrompt) {
                enhancedPromptDisplay.classList.add('active');
                enhancedText.textContent = 'Enhancing your prompt...';
            }
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        description: description,
                        api_key: apiKey,
                        enhance_prompt: enhancePrompt,
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentCode = data.code;
                    
                    // Show enhanced prompt if it was used
                    if (data.enhanced_prompt && enhancePrompt) {
                        enhancedText.textContent = data.enhanced_prompt;
                    }
                    
                    // Update iframe with new content
                    document.getElementById('preview-iframe').srcdoc = currentCode;
                    
                    // Show refinement section
                    document.getElementById('refinementSection').classList.add('active');
                    document.getElementById('versionBadge').textContent = 'v1';
                    document.getElementById('versionIndicator').textContent = 'Version 1';
                    document.getElementById('versionIndicator').style.display = 'inline-block';
                    
                    status.textContent = 'Generated Successfully!';
                    viewCodeBtn.disabled = false;
                    downloadBtn.disabled = false;
                    
                    // Clear refinement textarea
                    document.getElementById('refinementPrompt').value = '';
                } else {
                    alert('Error: ' + data.error);
                    status.textContent = 'Error';
                    enhancedPromptDisplay.classList.remove('active');
                }
            } catch (error) {
                alert('Failed to generate UI: ' + error.message);
                status.textContent = 'Error';
                enhancedPromptDisplay.classList.remove('active');
            } finally {
                loadingOverlay.classList.remove('active');
                generateBtn.disabled = false;
            }
        }
        
        async function refineUI() {
            if (!isConnected || !apiKey) {
                alert('Please connect your Gemini API key first!');
                return;
            }
            
            const refinementPrompt = document.getElementById('refinementPrompt').value;
            if (!refinementPrompt.trim()) {
                alert('Please describe what needs to be fixed or improved!');
                return;
            }
            
            if (!currentCode) {
                alert('Please generate a UI first before refining!');
                return;
            }
            
            const loadingOverlay = document.getElementById('loading');
            const loadingText = document.getElementById('loadingText');
            const refineBtn = document.querySelector('.refine-btn');
            const status = document.getElementById('status');
            
            loadingOverlay.classList.add('active');
            loadingText.textContent = 'Applying fixes to your UI...';
            refineBtn.disabled = true;
            status.textContent = 'Refining...';
            
            try {
                const response = await fetch('/refine', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        current_code: currentCode,
                        refinement_prompt: refinementPrompt,
                        api_key: apiKey,
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentCode = data.code;
                    currentVersion++;
                    
                    // Update iframe with refined content
                    document.getElementById('preview-iframe').srcdoc = currentCode;
                    
                    // Update version indicators
                    document.getElementById('versionBadge').textContent = `v${currentVersion}`;
                    document.getElementById('versionIndicator').textContent = `Version ${currentVersion}`;
                    
                    status.textContent = 'Refined Successfully!';
                    
                    // Clear refinement textarea
                    document.getElementById('refinementPrompt').value = '';
                } else {
                    alert('Error: ' + data.error);
                    status.textContent = 'Refinement Error';
                }
            } catch (error) {
                alert('Failed to refine UI: ' + error.message);
                status.textContent = 'Error';
            } finally {
                loadingOverlay.classList.remove('active');
                refineBtn.disabled = false;
            }
        }
        
        async function regenerateUI() {
            if (confirm('This will create a completely new version. Are you sure?')) {
                generateUI();
            }
        }
        
        function viewCode() {
            if (!currentCode) {
                alert('Generate a UI first!');
                return;
            }
            document.getElementById('codeContent').textContent = currentCode;
            document.getElementById('codeModal').classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('codeModal').classList.remove('active');
        }
        
        function downloadCode() {
            if (!currentCode) {
                alert('Generate a UI first!');
                return;
            }
            
            const blob = new Blob([currentCode], { type: 'text/html' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ui-prototype-v${currentVersion}-${Date.now()}.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
        
        // Close modal when clicking outside
        document.getElementById('codeModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
        
        // Allow Enter key to connect API
        document.getElementById('apiKeyInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                connectAPI();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/test-api-key', methods=['POST'])
def test_api_key():
    """Test if the provided API key is valid"""
    try:
        data = request.json
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'No API key provided'})
        
        # Configure Gemini with the provided API key
        genai.configure(api_key=api_key)
        
        # Try a simple test to verify the API key works
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content("Say 'Hello'")
        
        return jsonify({'success': True})
        
    except Exception as e:
        error_message = str(e)
        if 'API_KEY_INVALID' in error_message or 'invalid' in error_message.lower():
            return jsonify({'success': False, 'error': 'Invalid API key. Please check your key and try again.'})
        else:
            return jsonify({'success': False, 'error': f'Connection failed: {error_message}'})

def enhance_user_prompt(description):
    """
    Enhance the user's prompt to ensure better UI generation
    """
    # Keywords that indicate specific UI elements
    ui_patterns = {
        'dashboard': 'with sidebar navigation, header with user profile, main content area with cards and charts',
        'landing': 'with hero section, features grid, testimonials, pricing section, and footer',
        'blog': 'with header navigation, article cards in grid layout, sidebar for categories',
        'ecommerce': 'with product gallery, add to cart functionality, reviews section',
        'portfolio': 'with projects showcase, about section, contact form, smooth scrolling'
    }
    
    # Check if description is too short or vague
    if len(description.split()) < 10:
        description += ". Make it modern, responsive, and visually appealing with proper colors and spacing."
    
    # Add pattern-specific enhancements
    lower_desc = description.lower()
    for pattern, enhancement in ui_patterns.items():
        if pattern in lower_desc and enhancement not in lower_desc:
            description += f" {enhancement}"
    
    # Add technical requirements if not present
    technical_additions = []
    
    if 'responsive' not in lower_desc and 'mobile' not in lower_desc:
        technical_additions.append("Make it fully responsive for all devices")
    
    if 'color' not in lower_desc and 'theme' not in lower_desc:
        technical_additions.append("Use a modern color scheme with good contrast")
    
    if 'navigation' not in lower_desc and 'nav' not in lower_desc and 'menu' not in lower_desc:
        if any(word in lower_desc for word in ['website', 'site', 'page', 'app']):
            technical_additions.append("Include proper navigation")
    
    if technical_additions:
        description += ". " + ". ".join(technical_additions)
    
    # Add interaction requirements
    if 'button' in lower_desc or 'link' in lower_desc or 'tab' in lower_desc:
        description += ". IMPORTANT: Make all navigation links and tabs work within the page using JavaScript (single-page behavior). Use # anchors or JavaScript to show/hide content instead of loading new pages."
    
    return description

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        description = data.get('description', '')
        api_key = data.get('api_key', '')
        enhance_prompt = data.get('enhance_prompt', True)
        session_id = data.get('session_id', '')
        
        if not description:
            return jsonify({'success': False, 'error': 'No description provided'})
        
        if not api_key:
            return jsonify({'success': False, 'error': 'No API key provided'})
        
        # Enhance the prompt if enabled
        enhanced_description = description
        if enhance_prompt:
            enhanced_description = enhance_user_prompt(description)
        
        # Generate UI code using Gemini API
        generated_code = generate_ui_code(enhanced_description, api_key)
        
        # Process the generated code to fix navigation issues
        generated_code = fix_navigation_issues(generated_code)
        
        # Store in session
        if session_id:
            current_sessions[session_id] = {
                'code': generated_code,
                'version': 1,
                'original_prompt': description
            }
        
        # Save the generated code
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ui_{timestamp}.html'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        
        return jsonify({
            'success': True,
            'code': generated_code,
            'filename': filename,
            'enhanced_prompt': enhanced_description if enhance_prompt else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/refine', methods=['POST'])
def refine():
    """Refine the existing UI based on user feedback"""
    try:
        data = request.json
        current_code = data.get('current_code', '')
        refinement_prompt = data.get('refinement_prompt', '')
        api_key = data.get('api_key', '')
        session_id = data.get('session_id', '')
        
        if not current_code:
            return jsonify({'success': False, 'error': 'No current code provided'})
        
        if not refinement_prompt:
            return jsonify({'success': False, 'error': 'No refinement prompt provided'})
        
        if not api_key:
            return jsonify({'success': False, 'error': 'No API key provided'})
        
        # Refine the UI code using Gemini API
        refined_code = refine_ui_code(current_code, refinement_prompt, api_key)
        
        # Process the refined code to fix navigation issues
        refined_code = fix_navigation_issues(refined_code)
        
        # Update session
        if session_id and session_id in current_sessions:
            current_sessions[session_id]['code'] = refined_code
            current_sessions[session_id]['version'] += 1
        
        # Save the refined code
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ui_refined_{timestamp}.html'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(refined_code)
        
        return jsonify({
            'success': True,
            'code': refined_code,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def refine_ui_code(current_code, refinement_prompt, api_key):
    """
    Refine existing HTML/CSS code based on user feedback using Gemini API
    """
    
    prompt = f"""
    You have the following HTML/CSS/JavaScript code that needs to be refined:
    
    ```html
    {current_code}
    ```
    
    The user has requested the following changes/fixes:
    {refinement_prompt}
    
    REQUIREMENTS:
    1. Apply ONLY the requested changes while keeping everything else intact
    2. Maintain the single-page application structure
    3. Keep all styles inline in the <style> tag
    4. Keep all JavaScript inline in <script> tags
    5. Ensure all navigation and tabs continue to work within the same page
    6. Do not remove any existing functionality
    7. Fix any issues mentioned by the user
    8. Improve the specific areas requested
    9. Maintain responsive design
    10. Keep the code self-contained with no external dependencies
    
    IMPORTANT:
    - Focus on the specific changes requested
    - Don't completely rewrite the code unless necessary
    - Preserve the overall structure and design
    - Make sure all interactive elements continue to work
    - The page will be displayed in an iframe, so maintain single-page behavior
    
    Return ONLY the complete updated HTML code with no explanations, no markdown formatting, no code blocks - just pure HTML.
    """
    
    try:
        # Configure Gemini with the user's API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Generate refined content
        response = model.generate_content(prompt)
        code = response.text
        
        # Clean up the response - remove any markdown formatting if present
        if '```html' in code:
            code = code.split('```html')[1].split('```')[0]
        elif '```' in code:
            code = code.split('```')[1].split('```')[0]
        
        # Ensure it starts with DOCTYPE
        code = code.strip()
        if not code.lower().startswith('<!doctype'):
            code = '<!DOCTYPE html>\n' + code
            
        return code
        
    except Exception as e:
        # Return the original code with an error message
        return current_code

def fix_navigation_issues(html_code):
    """
    Fix navigation issues in generated HTML to prevent iframe breakout
    """
    # Add base tag to ensure all relative URLs stay in the iframe
    if '<head>' in html_code and '<base' not in html_code:
        html_code = html_code.replace('<head>', '<head>\n    <base target="_self">')
    
    # Add JavaScript to intercept all link clicks and prevent navigation
    navigation_fix_script = """
    <script>
    // Prevent all links from navigating away
    document.addEventListener('DOMContentLoaded', function() {
        // Handle all link clicks
        document.addEventListener('click', function(e) {
            if (e.target.tagName === 'A' || e.target.closest('a')) {
                e.preventDefault();
                const link = e.target.tagName === 'A' ? e.target : e.target.closest('a');
                const href = link.getAttribute('href');
                
                // Handle anchor links (e.g., #section)
                if (href && href.startsWith('#')) {
                    const targetId = href.substring(1);
                    const targetElement = document.getElementById(targetId);
                    if (targetElement) {
                        targetElement.scrollIntoView({ behavior: 'smooth' });
                    }
                    
                    // Handle tab switching if using tabs
                    handleTabSwitch(targetId);
                }
                
                // Log navigation attempt for debugging
                console.log('Navigation prevented:', href);
            }
        });
        
        // Function to handle tab switching
        function handleTabSwitch(tabId) {
            // Hide all tab contents
            const allTabs = document.querySelectorAll('.tab-content, .tab-pane, [role="tabpanel"]');
            allTabs.forEach(tab => {
                tab.style.display = 'none';
                tab.classList.remove('active', 'show');
            });
            
            // Show selected tab
            const selectedTab = document.getElementById(tabId);
            if (selectedTab) {
                selectedTab.style.display = 'block';
                selectedTab.classList.add('active', 'show');
            }
            
            // Update active tab button
            const allTabButtons = document.querySelectorAll('.tab-button, .nav-link, [role="tab"]');
            allTabButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            
            const activeButton = document.querySelector(`[href="#${tabId}"], [data-target="#${tabId}"]`);
            if (activeButton) {
                activeButton.classList.add('active');
            }
        }
        
        // Prevent form submissions from navigating
        document.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submission prevented');
            // You can add form handling logic here
            alert('Form submitted! (This is a prototype - no actual submission)');
        });
    });
    </script>
    """
    
    # Insert the script before closing body tag
    if '</body>' in html_code:
        html_code = html_code.replace('</body>', navigation_fix_script + '\n</body>')
    else:
        html_code += navigation_fix_script
    
    return html_code

def generate_ui_code(description, api_key):
    """
    Generate HTML/CSS code based on the description using Gemini API
    """
    
    prompt = f"""
    Create a complete, working HTML page with embedded CSS and JavaScript based on this description:
    {description}
    
    CRITICAL REQUIREMENTS:
    1. Generate a complete HTML document with <!DOCTYPE html>
    2. Include all CSS in a <style> tag in the <head>
    3. Include all JavaScript in <script> tags
    4. Make it a SINGLE PAGE APPLICATION - all navigation must work within the same page
    5. For tabs, menus, or multi-section layouts:
       - Use JavaScript to show/hide content
       - Use # anchors for navigation (e.g., href="#dashboard")
       - Never use external links or page reloads
       - Implement tab switching with JavaScript
    6. Make it visually appealing with modern, professional design
    7. Use beautiful colors, proper spacing, and modern typography
    8. Include smooth animations and transitions
    9. Make it fully responsive (mobile-friendly)
    10. Use realistic placeholder content/data
    11. Do not include ANY external dependencies - everything must be inline
    12. If charts are requested, create them using Canvas, SVG, or CSS
    13. Ensure all interactive elements work (buttons, forms, tabs, etc.)
    14. Use modern CSS features like flexbox, grid, gradients, shadows
    15. For navigation/tabs: Always use JavaScript to show/hide sections, never load new pages
    
    IMPORTANT: The page will be displayed in an iframe, so:
    - All links must use # anchors or JavaScript
    - No external navigation
    - Forms should not actually submit (use preventDefault)
    - Everything must work within a single HTML document
    
    The output should be production-ready code that looks professional and polished.
    
    Return ONLY the complete HTML code with no explanations, no markdown formatting, no code blocks - just pure HTML.
    """
    
    try:
        # Configure Gemini with the user's API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Generate content
        response = model.generate_content(prompt)
        code = response.text
        
        # Clean up the response - remove any markdown formatting if present
        if '```html' in code:
            code = code.split('```html')[1].split('```')[0]
        elif '```' in code:
            code = code.split('```')[1].split('```')[0]
        
        # Ensure it starts with DOCTYPE
        code = code.strip()
        if not code.lower().startswith('<!doctype'):
            code = '<!DOCTYPE html>\n' + code
            
        return code
        
    except Exception as e:
        # Return a nice error page if generation fails
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Generation Error</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 2rem;
                }}
                .error-container {{
                    background: white;
                    border-radius: 12px;
                    padding: 3rem;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
                    max-width: 600px;
                    text-align: center;
                }}
                h1 {{
                    color: #e53e3e;
                    margin-bottom: 1rem;
                }}
                p {{
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 1rem;
                }}
                .error-details {{
                    background: #f7f7f7;
                    padding: 1rem;
                    border-radius: 8px;
                    font-family: monospace;
                    font-size: 0.9rem;
                    color: #333;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>⚠️ Generation Failed</h1>
                <p>Unable to generate UI based on your description.</p>
                <div class="error-details">Error: {str(e)}</div>
                <p style="margin-top: 2rem;">Please try again with a different description or check your API key.</p>
            </div>
        </body>
        </html>
        """

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, port=5000)
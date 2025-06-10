#!/usr/bin/env python3
"""
Backend Server for CutieChatter
Menghubungkan frontend HTML dengan backend PyQt6 DeepSeek-R1
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import time
import uvicorn
import ollama
from threading import Thread
import queue
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(title="CutieChatter Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    model: str = "deepseek-r1:1.5b"
    conversation_history: List[ChatMessage] = []
    stream: bool = True
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 1.2

class ChatResponse(BaseModel):
    content: str
    model: str
    timestamp: str

# Global variables
model_status = {
    "deepseek-r1:1.5b": {"available": False, "loading": False},
    "qwen": {"available": False, "loading": False},
    "ollama": {"available": False, "loading": False}
}

# Text cleaning class (from your backend)
class TextCleaner:
    def __init__(self, text):
        self.text_to_be_cleaned = text

    def replace_italic_text(self, text):
        import re
        return re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    def replace_think_tags(self, text):
        import re
        text = re.sub(r'<\s*/\s*div\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*response\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*button\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'---', '</think', text)
        text = re.sub(r'<\s*/\s*br\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*Compose\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*think\s*>', '<span style="font-style: italic; font-weight: 200;">', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*think\s*>', '</span><br><br>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/?\s*th?i?n?k?\s*/?>', '', text, flags=re.IGNORECASE)
        return text
    
    def response_only(self, text):
        import re
        text = re.sub(r'.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<\s*/\s*div\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*br\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*response\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'---', '', text)
        text = re.sub(r'<\s*think\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*think\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/?\s*th?i?n?k?\s*/?>', '', text, flags=re.IGNORECASE)
        return text

    def process_content(self, text):
        if not text:
            return text
        processed = self.text_to_be_cleaned.replace('\n', '<br>')
        processed = self.replace_italic_text(processed)
        processed = self.replace_think_tags(processed)
        return processed

# API Endpoints
@app.get("/")
async def root():
    return {"message": "CutieChatter Backend Server", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models": model_status,
        "timestamp": time.time()
    }

@app.get("/models")
async def get_available_models():
    """Get list of available models"""
    available_models = []
    
    # Check Ollama models
    try:
        ollama_models = ollama.list()
        for model in ollama_models.get('models', []):
            model_name = model.get('name', '')
            if 'deepseek-r1' in model_name.lower():
                available_models.append({
                    "name": model_name,
                    "type": "ollama",
                    "size": model.get('size', 0),
                    "available": True
                })
                model_status[model_name] = {"available": True, "loading": False}
    except Exception as e:
        logger.warning(f"Could not connect to Ollama: {e}")
    
    return {"models": available_models, "status": model_status}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with streaming support"""
    try:
        if request.stream:
            return StreamingResponse(
                stream_chat_response(request),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream",
                }
            )
        else:
            # Non-streaming response
            response = await generate_chat_response(request)
            return response
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_chat_response(request: ChatRequest):
    """Stream chat response using Server-Sent Events"""
    try:
        # Format conversation history
        messages = []
        for msg in request.conversation_history:
            messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Add current user message
        messages.append({
            'role': 'user',
            'content': request.message
        })

        # Determine model and generate response
        model_name = request.model
        
        if model_name == "deepseek-r1:1.5b" or "deepseek" in model_name.lower():
            async for chunk in stream_deepseek_response(messages, request):
                yield f"data: {json.dumps({'content': chunk, 'model': model_name})}\n\n"
        
        elif model_name == "ollama":
            async for chunk in stream_ollama_response(messages, request):
                yield f"data: {json.dumps({'content': chunk, 'model': model_name})}\n\n"
        
        else:
            # Fallback to Ollama
            async for chunk in stream_ollama_response(messages, request):
                yield f"data: {json.dumps({'content': chunk, 'model': model_name})}\n\n"
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

async def stream_deepseek_response(messages, request):
    """Stream response from DeepSeek-R1 model via Ollama"""
    try:
        # Use Ollama to access DeepSeek-R1
        response_queue = queue.Queue()
        
        def ollama_stream_worker():
            try:
                stream = ollama.chat(
                    model="deepseek-r1:1.5b",
                    messages=messages,
                    stream=True,
                    options={
                        "temperature": request.temperature or 1.2,
                        "num_ctx": 4096,
                        "num_predict": request.max_tokens or 512,
                        "top_k": 40,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,
                    }
                )
                
                for chunk in stream:
                    content = chunk.get('message', {}).get('content', '')
                    if content:
                        response_queue.put(('content', content))
                
                response_queue.put(('done', None))
                
            except Exception as e:
                logger.error(f"Ollama streaming error: {e}")
                response_queue.put(('error', str(e)))
        
        # Start Ollama in background thread
        thread = Thread(target=ollama_stream_worker)
        thread.start()
        
        full_content = ""
        while True:
            try:
                # Get from queue with timeout
                item_type, content = response_queue.get(timeout=30.0)
                
                if item_type == 'done':
                    break
                elif item_type == 'error':
                    raise Exception(content)
                elif item_type == 'content' and content:
                    # Process content with text cleaner
                    text_cleaner = TextCleaner(content)
                    processed_content = text_cleaner.process_content(content)
                    
                    full_content += content
                    yield processed_content
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
                
            except queue.Empty:
                logger.warning("Queue timeout - ending stream")
                break
        
        # Clean final response
        if full_content:
            text_cleaner = TextCleaner(full_content)
            cleaned_response = text_cleaner.response_only(full_content)
            logger.info(f"Final cleaned response: {cleaned_response[:100]}...")
        
        thread.join(timeout=5.0)
        
    except Exception as e:
        logger.error(f"DeepSeek streaming error: {e}")
        yield f"Error: {str(e)}"

async def stream_ollama_response(messages, request):
    """Stream response from general Ollama models"""
    try:
        response_queue = queue.Queue()
        
        def ollama_worker():
            try:
                # Determine model name
                model_name = request.model
                if model_name == "ollama":
                    # Try to find a good model
                    try:
                        models = ollama.list()
                        available_models = [m['name'] for m in models.get('models', [])]
                        
                        # Prefer DeepSeek models
                        for model in available_models:
                            if 'deepseek' in model.lower():
                                model_name = model
                                break
                        else:
                            # Use first available model
                            model_name = available_models[0] if available_models else "llama2"
                    except:
                        model_name = "llama2"
                
                stream = ollama.chat(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    options={
                        "temperature": request.temperature or 1.0,
                        "num_ctx": 2048,
                        "num_predict": request.max_tokens or 256,
                    }
                )
                
                for chunk in stream:
                    content = chunk.get('message', {}).get('content', '')
                    if content:
                        response_queue.put(('content', content))
                
                response_queue.put(('done', None))
                
            except Exception as e:
                response_queue.put(('error', str(e)))
        
        thread = Thread(target=ollama_worker)
        thread.start()
        
        while True:
            try:
                item_type, content = response_queue.get(timeout=30.0)
                
                if item_type == 'done':
                    break
                elif item_type == 'error':
                    raise Exception(content)
                elif item_type == 'content' and content:
                    yield content
                
                await asyncio.sleep(0.01)
                
            except queue.Empty:
                break
        
        thread.join(timeout=5.0)
        
    except Exception as e:
        logger.error(f"Ollama streaming error: {e}")
        yield f"Error: {str(e)}"

async def generate_chat_response(request: ChatRequest):
    """Generate non-streaming chat response"""
    try:
        messages = []
        for msg in request.conversation_history:
            messages.append({'role': msg.role, 'content': msg.content})
        
        messages.append({'role': 'user', 'content': request.message})
        
        # Use Ollama for response
        response = ollama.chat(
            model=request.model if request.model != "deepseek-r1:1.5b" else "deepseek-r1:1.5b",
            messages=messages,
            stream=False,
            options={
                "temperature": request.temperature or 1.2,
                "num_ctx": 4096,
                "num_predict": request.max_tokens or 512,
            }
        )
        
        content = response.get('message', {}).get('content', '')
        
        # Clean response
        text_cleaner = TextCleaner(content)
        cleaned_content = text_cleaner.response_only(content)
        
        return ChatResponse(
            content=cleaned_content,
            model=request.model,
            timestamp=str(time.time())
        )
        
    except Exception as e:
        logger.error(f"Generate response error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# Check model availability on startup
@app.on_event("startup")
async def startup_event():
    """Check model availability on startup"""
    logger.info("Starting CutieChatter Backend Server...")
    
    # Check Ollama connection
    try:
        models = ollama.list()
        logger.info(f"Connected to Ollama. Available models: {len(models.get('models', []))}")
        
        for model in models.get('models', []):
            model_name = model.get('name', '')
            if model_name:
                model_status[model_name] = {"available": True, "loading": False}
                logger.info(f"Found model: {model_name}")
        
        # Check specifically for DeepSeek-R1
        deepseek_models = [m for m in models.get('models', []) if 'deepseek-r1' in m.get('name', '').lower()]
        if deepseek_models:
            model_status["deepseek-r1:1.5b"]["available"] = True
            logger.info("✅ DeepSeek-R1 model is available!")
        else:
            logger.warning("⚠️  DeepSeek-R1 model not found. Please install it with: ollama pull deepseek-r1:1.5b")
            
    except Exception as e:
        logger.error(f"Could not connect to Ollama: {e}")
        logger.error("Make sure Ollama is installed and running!")

if __name__ == "__main__":
    print("🚀 Starting CutieChatter Backend Server...")
    print("📱 Frontend URL: http://localhost:8000")
    print("🔗 Backend URL: http://localhost:8000")
    print("📋 API Docs: http://localhost:8000/docs")
    print("🤖 Make sure Ollama is running with DeepSeek-R1:1.5b model!")
    print("-" * 50)
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
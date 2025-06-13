"""
Backend Server for CutieChatter - FIXED VERSION
Menghubungkan frontend HTML dengan backend DeepSeek-R1
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
from threading import Thread, Event
import queue
import logging
import sys
import os
import multiprocessing
import re
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    full_history: Optional[List[ChatMessage]] = None  # Added to return updated history

class ModelInfo(BaseModel):
    name: str
    type: str
    size: Optional[int] = None
    available: bool = True
    loading: bool = False

# FIXED: Pure Python OllamaWorker (removed PyQt6 dependency)
class OllamaWorker:
    """Pure Python Ollama worker without PyQt6 dependencies"""
    
    def __init__(self, user_message, conversation_history, model_name):
        self.user_message = user_message
        self.conversation_history = conversation_history.copy()
        self.num_threads = max(1, multiprocessing.cpu_count() // 2)
        self.model_name = model_name
        self.stop_event = Event()
        
    def run(self, chunk_callback=None, finish_callback=None):
        """Run the worker with callbacks"""
        try:
            logger.info(f"🤖 OllamaWorker running: {self.model_name}")
            logger.info(f"📝 History length: {len(self.conversation_history)}")
            
            # Test connection first
            try:
                ollama.list()
            except Exception as e:
                error_msg = f"❌ Ollama tidak bisa diakses: {str(e)}"
                if finish_callback:
                    finish_callback(error_msg)
                return error_msg
            
            # Start streaming
            stream = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history,
                stream=True,
                options={
                    "num_thread": self.num_threads,
                    "temperature": 1.1,
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_ctx": 2048,
                    "num_batch": 16,
                    "num_predict": 256,
                    "repeat_penalty": 1.1
                }
            )
            
            full_content = ''
            received_chunks = 0
            
            logger.info("🚀 Starting DeepSeek streaming...")
            
            for chunk in stream:
                try:
                    # Check if we should stop
                    if self.stop_event.is_set():
                        logger.info("⏹️ Stop event triggered")
                        break
                    
                    content = chunk.get('message', {}).get('content', '')
                    
                    if content:
                        full_content += content
                        received_chunks += 1
                        
                        # Process with TextCleaner
                        try:
                            processor = TextCleaner(content)
                            processed = processor.process_content(content)
                            if chunk_callback:
                                chunk_callback(processed)
                        except Exception as clean_error:
                            logger.warning(f"Text cleaning error: {clean_error}")
                            if chunk_callback:
                                chunk_callback(content)
                        
                        # Log progress
                        if received_chunks % 5 == 0:
                            logger.debug(f"📥 Chunks: {received_chunks}, Length: {len(full_content)}")
                    
                    # Check if done
                    if chunk.get('done', False):
                        logger.info("✅ DeepSeek marked response as done")
                        break
                        
                except Exception as chunk_error:
                    logger.warning(f"⚠️ Chunk error: {chunk_error}")
                    continue  # Skip bad chunks
            
            logger.info(f"🏁 Streaming complete: {received_chunks} chunks, {len(full_content)} chars")
            
            # Always call finish callback
            final_response = full_content if full_content.strip() else "Maaf, tidak ada response dari DeepSeek-R1."
            if finish_callback:
                finish_callback(final_response)
            
            return final_response

        except Exception as e:
            error_msg = f"❌ DeepSeek Error: {str(e)}"
            logger.error(f"❌ OllamaWorker error: {e}")
            if finish_callback:
                finish_callback(error_msg)
            return error_msg
        
        finally:
            logger.info("🧹 OllamaWorker finished")
    
    def stop(self):
        """Stop the worker"""
        self.stop_event.set()

# FIXED: Improved TextCleaner class
class TextCleaner:
    """Text cleaning and processing utilities"""
    
    def __init__(self, text):
        self.text_to_be_cleaned = text

    def replace_italic_text(self, text):
        """Replace italic markdown with HTML"""
        return re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    def replace_think_tags(self, text):
        """Clean and replace thinking tags"""
        # Remove various HTML/XML tags that might appear
        text = re.sub(r'<\s*/\s*div\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*response\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*button\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'---', '</think>', text)
        text = re.sub(r'<\s*/\s*br\s*>', '</think>', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*Compose\s*>', '</think>', text, flags=re.IGNORECASE)
        
        # Replace think tags with styled spans
        text = re.sub(r'<\s*think\s*>', '<span style="font-style: italic; font-weight: 200;">', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*think\s*>', '</span><br><br>', text, flags=re.IGNORECASE)
        
        # Clean up malformed think tags
        text = re.sub(r'<\s*/?\s*th?i?n?k?\s*/?>', '', text, flags=re.IGNORECASE)
        
        return text
    
    def response_only(self, text):
        """Extract only the response content, removing thinking sections"""
        if not text:
            return text
            
        # Remove thinking sections
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'.*?</think>', '', text, flags=re.DOTALL)
        
        # Clean HTML tags
        text = re.sub(r'<\s*/\s*div\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*br\s*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*response\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'---', '', text)
        
        # Remove any remaining think tags
        text = re.sub(r'<\s*think\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/\s*think\s*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\s*/?\s*th?i?n?k?\s*/?>', '', text, flags=re.IGNORECASE)
        
        return text.strip()

    def process_content(self, text):
        """Process content for display"""
        if not text:
            return text
            
        # Replace newlines with HTML breaks
        processed = text.replace('\n', '<br>')
        
        # Process italic text
        processed = self.replace_italic_text(processed)
        
        # Process think tags
        processed = self.replace_think_tags(processed)
        
        return processed

# Global variables
model_status = {
    "deepseek-r1:1.5b": {"available": False, "loading": False},
    "qwen": {"available": False, "loading": False},
    "ollama": {"available": False, "loading": False}
}

# Store conversation sessions (in production, use Redis or database)
conversation_sessions = {}

# FIXED: Improved startup/shutdown handling
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting CutieChatter Backend Server...")
    await check_model_availability()
    yield
    # Shutdown
    logger.info("👋 Shutting down CutieChatter Backend Server...")

# FastAPI app initialization with lifespan
app = FastAPI(
    title="CutieChatter Backend", 
    version="1.0.0",
    description="Backend server for CutieChatter with DeepSeek-R1 support",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CutieChatter Backend Server", 
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Quick Ollama health check
        ollama_healthy = False
        try:
            ollama.list()
            ollama_healthy = True
        except:
            pass
            
        return {
            "status": "healthy" if ollama_healthy else "degraded",
            "ollama_connection": ollama_healthy,
            "models": model_status,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/models", response_model=Dict[str, Any])
async def get_available_models():
    """Get list of available models"""
    available_models = []
    
    try:
        ollama_models = ollama.list()
        for model in ollama_models.get('models', []):
            model_name = model.get('name', '')
            if model_name:
                available_models.append(ModelInfo(
                    name=model_name,
                    type="ollama",
                    size=model.get('size', 0),
                    available=True,
                    loading=False
                ))
                
                # Update global status
                model_status[model_name] = {"available": True, "loading": False}
                
    except Exception as e:
        logger.warning(f"Could not connect to Ollama: {e}")
        return {
            "models": [],
            "status": model_status,
            "error": "Could not connect to Ollama server"
        }
    
    return {
        "models": [model.dict() for model in available_models],
        "status": model_status,
        "total_models": len(available_models)
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with streaming support"""
    try:
        logger.info(f"📥 Chat request: {request.message[:50]}... (model: {request.model})")
        
        if request.stream:
            return StreamingResponse(
                stream_chat_response(request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
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
    """FIXED: Stream chat response using Server-Sent Events with history tracking"""
    try:
        # Format conversation history
        messages = []
        
        # Add system prompt if not present
        if not request.conversation_history or request.conversation_history[0].role != 'system':
            messages.append({
                'role': 'system',
                'content': '''You're CutieChatter, your directive should be:
                1. Playful.
                2. Personally engaging with the user.
                3. Maintain a consistent personal tone.
                4. Avoid responding using double quotation marks.
                5. Generate natural responses.'''
            })
        
        # Add conversation history
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

        logger.info(f"📝 Conversation length: {len(messages)} messages")

        # Track full response for history
        full_response = ""
        
        # Determine model and generate response
        model_name = request.model
        
        if model_name == "deepseek-r1:1.5b" or "deepseek" in model_name.lower():
            async for chunk in stream_deepseek_response(messages, request):
                if chunk:  # Only yield non-empty chunks
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk, 'model': model_name})}\n\n"
        else:
            # Fallback to general Ollama
            async for chunk in stream_ollama_response(messages, request):
                if chunk:  # Only yield non-empty chunks
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk, 'model': model_name})}\n\n"
        
        # Send the complete conversation history including the new response
        if full_response:
            # Clean the response for history
            text_cleaner = TextCleaner(full_response)
            cleaned_response = text_cleaner.response_only(full_response)
            
            # Build updated history
            updated_history = []
            
            # Keep existing history
            for msg in request.conversation_history:
                updated_history.append(msg.dict())
            
            # Add user message
            updated_history.append({
                'role': 'user',
                'content': request.message,
                'timestamp': str(time.time())
            })
            
            # Add AI response
            updated_history.append({
                'role': 'assistant',
                'content': cleaned_response,
                'timestamp': str(time.time())
            })
            
            # Send history update
            yield f"data: {json.dumps({'type': 'history_update', 'history': updated_history})}\n\n"
        
        # Send completion signal
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'error': str(e), 'model': request.model})}\n\n"

async def stream_deepseek_response(messages, request):
    """FIXED: Stream response from DeepSeek-R1 model via Ollama"""
    try:
        response_queue = asyncio.Queue()
        stop_event = Event()
        
        def ollama_stream_worker():
            """Worker function to handle Ollama streaming in separate thread"""
            try:
                logger.info("🤖 Starting DeepSeek-R1 streaming worker...")
                
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
                    if stop_event.is_set():
                        break
                        
                    content = chunk.get('message', {}).get('content', '')
                    if content:
                        # Use asyncio-safe way to put into queue
                        asyncio.run_coroutine_threadsafe(
                            response_queue.put(('content', content)),
                            asyncio.get_event_loop()
                        )
                
                # Signal completion
                asyncio.run_coroutine_threadsafe(
                    response_queue.put(('done', None)),
                    asyncio.get_event_loop()
                )
                
            except Exception as e:
                logger.error(f"Ollama streaming error: {e}")
                asyncio.run_coroutine_threadsafe(
                    response_queue.put(('error', str(e))),
                    asyncio.get_event_loop()
                )
        
        # Start Ollama in background thread
        thread = Thread(target=ollama_stream_worker)
        thread.daemon = True
        thread.start()
        
        text_cleaner = TextCleaner("")
        
        try:
            while True:
                try:
                    # Get from queue with timeout
                    item_type, content = await asyncio.wait_for(response_queue.get(), timeout=30.0)
                    
                    if item_type == 'done':
                        logger.info("✅ Streaming completed")
                        break
                    elif item_type == 'error':
                        logger.error(f"Stream error: {content}")
                        yield f"Error: {content}"
                        break
                    elif item_type == 'content' and content:
                        # Process content with text cleaner
                        text_cleaner.text_to_be_cleaned = content
                        processed_content = text_cleaner.process_content(content)
                        
                        yield processed_content
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.01)
                    
                except asyncio.TimeoutError:
                    logger.warning("Queue timeout - ending stream")
                    break
        finally:
            # Cleanup
            stop_event.set()
        
    except Exception as e:
        logger.error(f"DeepSeek streaming error: {e}")
        yield f"Error: {str(e)}"

async def stream_ollama_response(messages, request):
    """FIXED: Stream response from general Ollama models"""
    try:
        response_queue = asyncio.Queue()
        stop_event = Event()
        
        def ollama_worker():
            """Worker function for general Ollama models"""
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
                
                logger.info(f"🤖 Using Ollama model: {model_name}")
                
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
                    if stop_event.is_set():
                        break
                        
                    content = chunk.get('message', {}).get('content', '')
                    if content:
                        asyncio.run_coroutine_threadsafe(
                            response_queue.put(('content', content)),
                            asyncio.get_event_loop()
                        )
                
                asyncio.run_coroutine_threadsafe(
                    response_queue.put(('done', None)),
                    asyncio.get_event_loop()
                )
                
            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    response_queue.put(('error', str(e))),
                    asyncio.get_event_loop()
                )
        
        thread = Thread(target=ollama_worker)
        thread.daemon = True
        thread.start()
        
        try:
            while True:
                try:
                    item_type, content = await asyncio.wait_for(response_queue.get(), timeout=30.0)
                    
                    if item_type == 'done':
                        break
                    elif item_type == 'error':
                        yield f"Error: {content}"
                        break
                    elif item_type == 'content' and content:
                        yield content
                    
                    await asyncio.sleep(0.01)
                    
                except asyncio.TimeoutError:
                    logger.warning("Ollama stream timeout")
                    break
        finally:
            stop_event.set()
        
    except Exception as e:
        logger.error(f"Ollama streaming error: {e}")
        yield f"Error: {str(e)}"

async def generate_chat_response(request: ChatRequest):
    """FIXED: Generate non-streaming chat response with history tracking"""
    try:
        messages = []
        
        # Add system prompt if not present
        if not request.conversation_history or request.conversation_history[0].role != 'system':
            messages.append({
                'role': 'system',
                'content': '''You're CutieChatter, your directive should be:
                1. Playful.
                2. Personally engaging with the user.
                3. Maintain a consistent personal tone.
                4. Avoid responding using double quotation marks.
                5. Generate natural responses.'''
            })
        
        # Add conversation history
        for msg in request.conversation_history:
            messages.append({'role': msg.role, 'content': msg.content})
        
        # Add current message
        messages.append({'role': 'user', 'content': request.message})
        
        # Use Ollama for response
        model_name = request.model if request.model != "deepseek-r1:1.5b" else "deepseek-r1:1.5b"
        
        response = ollama.chat(
            model=model_name,
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
        
        # Build updated history
        updated_history = []
        
        # Keep existing history
        for msg in request.conversation_history:
            updated_history.append(msg)
        
        # Add user message
        updated_history.append(ChatMessage(
            role='user',
            content=request.message,
            timestamp=str(time.time())
        ))
        
        # Add AI response
        updated_history.append(ChatMessage(
            role='assistant',
            content=cleaned_content,
            timestamp=str(time.time())
        ))
        
        return ChatResponse(
            content=cleaned_content,
            model=request.model,
            timestamp=str(time.time()),
            full_history=updated_history  # Return updated history
        )
        
    except Exception as e:
        logger.error(f"Generate response error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

async def check_model_availability():
    """Check model availability on startup"""
    logger.info("🔍 Checking model availability...")
    
    try:
        models = ollama.list()
        logger.info(f"Connected to Ollama. Available models: {len(models.get('models', []))}")
        
        # Reset model status
        for key in model_status:
            model_status[key] = {"available": False, "loading": False}
        
        # Update with actual models
        for model in models.get('models', []):
            model_name = model.get('name', '')
            if model_name:
                model_status[model_name] = {"available": True, "loading": False}
                logger.info(f"✅ Found model: {model_name}")
        
        # Check specifically for DeepSeek-R1
        deepseek_models = [
            m for m in models.get('models', []) 
            if 'deepseek-r1' in m.get('name', '').lower()
        ]
        
        if deepseek_models:
            model_status["deepseek-r1:1.5b"]["available"] = True
            logger.info("✅ DeepSeek-R1 model is available!")
        else:
            logger.warning("⚠️  DeepSeek-R1 model not found. Please install it with: ollama pull deepseek-r1:1.5b")
            
    except Exception as e:
        logger.error(f"Could not connect to Ollama: {e}")
        logger.error("❌ Make sure Ollama is installed and running!")
        
        # Set all models as unavailable
        for key in model_status:
            model_status[key] = {"available": False, "loading": False}

# Additional utility endpoints
@app.get("/models/refresh")
async def refresh_models():
    """Refresh model availability"""
    await check_model_availability()
    return {
        "message": "Model availability refreshed",
        "models": model_status,
        "timestamp": time.time()
    }

@app.post("/models/pull")
async def pull_model(model_name: str):
    """Pull a model from Ollama (async operation)"""
    try:
        # This would typically be a background task
        # For now, just check if model exists
        models = ollama.list()
        existing_models = [m['name'] for m in models.get('models', [])]
        
        if model_name in existing_models:
            return {"message": f"Model {model_name} already exists", "status": "exists"}
        else:
            return {"message": f"Model {model_name} not found. Use 'ollama pull {model_name}' in terminal", "status": "not_found"}
            
    except Exception as e:
        logger.error(f"Error checking model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/new")
async def create_new_session():
    """Create a new conversation session"""
    session_id = str(time.time())
    conversation_sessions[session_id] = []
    return {"session_id": session_id, "created": time.time()}

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get conversation history for a session"""
    if session_id in conversation_sessions:
        return {"session_id": session_id, "history": conversation_sessions[session_id]}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

if __name__ == "__main__":
    print("🚀 Starting CutieChatter Backend Server...")
    print("=" * 50)
    print("📱 Server URL: http://localhost:8000")
    print("📋 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🤖 Models: http://localhost:8000/models")
    print("💬 Chat: POST http://localhost:8000/chat")
    print("=" * 50)
    print("⚠️  Requirements:")
    print("   1. Ollama server must be running")
    print("   2. DeepSeek-R1:1.5b model should be installed")
    print("   3. Run: ollama pull deepseek-r1:1.5b")
    print("=" * 50)
    
    uvicorn.run(
        "backend2:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
from flask import Flask, request, session, jsonify, Response
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth, credentials
import os
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime
import json
from dotenv import load_dotenv
from resume_processor import ResumeProcessor
# Replace RAG service with chatbot integration
from chatbot_integration import get_chatbot_integration
from faculty_data_mapper import mongo_faculty_to_admin_format, admin_format_to_mongo_faculty
import logging
import time
import redis
from functools import wraps
import uuid
from langchain_core.documents import Document

# --- MongoDB Setup ---
from pymongo import MongoClient
from bson import ObjectId
MONGO_URI = os.environ.get('MONGO_URI')
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client['AdvisorAI']

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
JWTManager(app)

# Enable CORS for all routes and allow credentials (cookies)
CORS(app, supports_credentials=True, origins=[
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",  # React dev server (alternative)
    "http://localhost:3002",  # Vite dev server (port 3002)
    "http://127.0.0.1:3002",  # Vite dev server (port 3002 alternative)
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",  # Vite dev server (alternative)
    "http://localhost:4173",  # Vite preview server
    "http://127.0.0.1:4173",  # Vite preview server (alternative)
    "http://localhost:5003",  # Backend server (new port)
    "http://127.0.0.1:5003",  # Backend server (new port alternative)
])  # Make sure all frontend dev ports are included for CORS

# Initialize Resume Processor
try:
    resume_processor = ResumeProcessor()
    print("  Resume processor initialized")
except Exception as e:
    print(f"  Resume processor initialization failed: {e}")
    resume_processor = None

# Initialize Redis for caching
try:
    redis_client = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=int(os.environ.get('REDIS_PORT', 6379)),
        db=int(os.environ.get('REDIS_DB', 0)),
        decode_responses=True
    )
    # Test Redis connection
    redis_client.ping()
    print("  Redis client initialized")
except Exception as e:
    print(f"  Redis client initialization failed: {e}")
    redis_client = None

# Restore only Firebase Admin SDK initialization for authentication
if not firebase_admin._apps:
    cred = credentials.Certificate('firebae_key1.json')
firebase_admin.initialize_app(cred)

# Cache decorator for chat sessions
def cache_chat_sessions(expiry=3600):  # 1 hour cache
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not redis_client:
                return f(*args, **kwargs)
            
            user_id = get_jwt_identity()
            cache_key = f"chat_sessions:{user_id}"
            
            # Try to get from cache first
            cached_data = redis_client.get(cache_key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except:
                    pass
            
            # If not in cache, get from database
            result = f(*args, **kwargs)
            
            # Cache the result
            try:
                redis_client.setex(cache_key, expiry, json.dumps(result))
            except:
                pass
            
            return result
        return decorated_function
    return decorator

# Invalidate cache when sessions are modified
def invalidate_chat_cache(user_id):
    if redis_client:
        try:
            cache_key = f"chat_sessions:{user_id}"
            redis_client.delete(cache_key)
        except:
            pass

# Utility function to convert MongoDB documents for JSON serialization

def mongo_doc_to_json(doc):
    if not doc:
        return doc
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, list):
        return [mongo_doc_to_json(item) for item in doc]
    if isinstance(doc, dict):
        doc = dict(doc)
        if '_id' in doc:
            doc['id'] = str(doc['_id'])
            del doc['_id']
        for k, v in doc.items():
            doc[k] = mongo_doc_to_json(v)
        return doc
    return doc

def bson_safe(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [bson_safe(item) for item in obj]
    if isinstance(obj, dict):
        return {k: bson_safe(v) for k, v in obj.items()}
    return obj

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "firebase_initialized": bool(firebase_admin._apps),
        "firestore_available": mongo_db is not None,
        "resume_processor_available": resume_processor is not None
    })

# LLM status endpoint
@app.route('/api/llm/status', methods=['GET'])
def llm_status():
    """Get LLM service status"""
    try:
        if resume_processor and resume_processor.llm_service:
            return jsonify({
                "status": "available",
                "provider": resume_processor.llm_service.provider,
                "openai_configured": bool(resume_processor.llm_service.openai_api_key),
                "gemini_configured": bool(resume_processor.llm_service.gemini_api_key)
            }), 200
        else:
            return jsonify({
                "status": "unavailable",
                "message": "LLM service not initialized"
            }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Debug text extraction endpoint
@app.route('/api/resume/debug-extraction', methods=['POST'])
@jwt_required()
def debug_text_extraction():
    """Debug text extraction from resume file"""
    try:
        user_id = get_jwt_identity()
        print(f"🔍 Debug text extraction for user: {user_id}")
        
        if 'resume' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Create uploads directory if it doesn't exist
        upload_dir = 'uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Save file
        filename = f"debug_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Extract text
        if resume_processor:
            text = resume_processor.extract_text_from_file(file_path, file.content_type)
            cleaned_text = resume_processor.clean_text(text)
            
            return jsonify({
                "success": True,
                "originalText": text,
                "cleanedText": cleaned_text,
                "textLength": len(text),
                "cleanedLength": len(cleaned_text),
                "fileType": file.content_type,
                "fileName": file.filename
            }), 200
        else:
            return jsonify({"error": "Resume processor not available"}), 500
            
    except Exception as e:
        print(f"  Debug extraction error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Authentication endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User signup endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('fullName', '')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Create user in Firebase
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=full_name
        )

        # Create user document in Firestore
        if mongo_db is not None:
            user_doc = {
                'uid': user_record.uid,
                'email': email,
                'fullName': full_name,
                'createdAt': datetime.now(),
                'profileCompleted': False,
                'resumeData': {},
                'role': 'user' # Add role field
            }
            mongo_db.users.insert_one(user_doc)

        # Create JWT token
        access_token = create_access_token(identity=user_record.uid)

        return jsonify({
            "message": "User created successfully",
            "user": {
                "uid": user_record.uid,
                "email": email,
                "fullName": full_name
            },
            "access_token": access_token
        }), 201

    except Exception as e:
        print(f"  Signup error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/signin', methods=['POST'])
def signin():
    """User signin endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Verify user credentials with Firebase
        user_record = auth.get_user_by_email(email)

        # Create JWT token
        access_token = create_access_token(identity=user_record.uid)

        return jsonify({
            "message": "Signin successful",
            "user": {
                "uid": user_record.uid,
                "email": user_record.email,
                "fullName": user_record.display_name or ""
            },
            "access_token": access_token
        }), 200

    except Exception as e:
        print(f"  Signin error: {str(e)}")
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/auth/signin-with-token', methods=['POST'])
def signin_with_token():
    """Signin with Firebase ID token"""
    try:
        data = request.get_json()
        id_token = data.get('idToken')

        if not id_token:
            return jsonify({"error": "ID token is required"}), 400

        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']

        # Get user record
        user_record = auth.get_user(user_id)

        # Create JWT token
        access_token = create_access_token(identity=user_id)

        return jsonify({
            "message": "Signin successful",
            "user": {
                "uid": user_record.uid,
                "email": user_record.email,
                "fullName": user_record.display_name or ""
            },
            "access_token": access_token
        }), 200

    except Exception as e:
        print(f"  Token signin error: {str(e)}")
        return jsonify({"error": "Invalid token"}), 401

# Resume upload and parsing endpoint
@app.route('/api/resume/upload-and-parse', methods=['POST'])
@jwt_required()
def upload_and_parse_resume():
    """Upload and parse resume file"""
    try:
        # Get current user ID from JWT
        user_id = get_jwt_identity()
        print(f"🔑 Processing resume upload for user: {user_id}")
        
        if 'resume' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check file type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
        
        if file.content_type not in allowed_types:
            return jsonify({"error": "Invalid file type. Only PDF, DOCX, and DOC files are allowed"}), 400
        
        # Create uploads directory if it doesn't exist
        upload_dir = 'uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Save file
        filename = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        print(f"📁 File saved: {file_path}")
        
        # Process resume
        if resume_processor:
            result = resume_processor.process_resume(file_path, file.content_type)
            
            if result['success']:
                # Update user document in Firestore
                if mongo_db is not None:
                    user_ref = mongo_db.users.find_one({'uid': user_id})
                    if user_ref:
                        # Update existing document
                        user_ref['resumeData'] = result['parsedData']
                        user_ref['profileCompleted'] = True
                        user_ref['lastResumeUpdate'] = datetime.now()
                        user_ref['resumeText'] = result['originalText']
                        mongo_db.users.replace_one({'uid': user_id}, user_ref)
                
                return jsonify({
                    "success": True,
                    "message": "Resume parsed successfully",
                    "data": result['parsedData'],
                    "originalText": result['originalText'],
                    "llmProvider": result.get('llmProvider', 'none')
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 400
        else:
            return jsonify({"error": "Resume processor not available"}), 500
            
    except Exception as e:
        print(f"  Resume upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Debug endpoint to check token
@app.route('/api/debug/token', methods=['GET'])
@jwt_required()
def debug_token():
    """Debug endpoint to check JWT token"""
    user_id = get_jwt_identity()
    return jsonify({
        "message": "Token is valid",
        "user_id": user_id,
        "timestamp": str(datetime.now())
    })

# Get user profile
@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get user profile data"""
    try:
        user_id = get_jwt_identity()
        
        if mongo_db is not None:
            user_doc = mongo_db.users.find_one({'uid': user_id})
            if user_doc:
                # Ensure profileCompleted field is always present
                profile = mongo_doc_to_json(user_doc)
                if 'profileCompleted' not in profile:
                    profile['profileCompleted'] = False
                return jsonify({
                    "success": True,
                    "profile": profile
                }), 200
            else:
                return jsonify({"error": "User profile not found"}), 404
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Get profile error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Update user profile
@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """Update user profile data"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if mongo_db is not None:
            user_ref = mongo_db.users.find_one({'uid': user_id})
            if user_ref:
                # Update existing document
                user_ref.update(data)
                user_ref['updatedAt'] = datetime.now()
                # Set profileCompleted to True when profile is saved
                user_ref['profileCompleted'] = True
                mongo_db.users.replace_one({'uid': user_id}, user_ref)
            else:
                # Create new document
                user_ref = {
                    'uid': user_id,
                    **data,
                    'createdAt': datetime.now(),
                    'updatedAt': datetime.now(),
                    'profileCompleted': True  # Set profileCompleted to True for new profiles
                }
                mongo_db.users.insert_one(user_ref)
            
            return jsonify({
                "success": True,
                "message": "Profile updated successfully"
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Update profile error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Public portfolio endpoint
@app.route('/api/public-profile/<user_id>', methods=['GET'])
def get_public_profile(user_id):
    """Get public/portfolio profile data for a user (view-only, no auth required)"""
    try:
        if mongo_db is not None:
            user_doc = mongo_db.users.find_one({'uid': user_id})
            if user_doc:
                profile = mongo_doc_to_json(user_doc)
                # Only include public/important fields
                public_fields = [
                    'fullName', 'email', 'location', 'summary',
                    'github', 'linkedin',
                    'experience', 'education', 'skills', 'certifications', 'projects',
                    'portfolioTheme'
                ]
                public_profile = {k: profile.get(k) for k in public_fields if k in profile}
                # For each project, only include github if present
                if 'projects' in public_profile and isinstance(public_profile['projects'], list):
                    for proj in public_profile['projects']:
                        if 'github' not in proj:
                            proj['github'] = None
                return jsonify({
                    "success": True,
                    "profile": public_profile
                }), 200
            else:
                return jsonify({"success": False, "error": "Profile not found"}), 404
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
    except Exception as e:
        print(f"  Get public profile error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Chat endpoints
@app.route('/api/chat/query', methods=['POST'])
@jwt_required()
def chat_query():
    """Process chat query with LangGraph chatbot agents"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        query = data.get('query', '')
        chat_history = data.get('chat_history', [])
        session_id = data.get('session_id')
        
        if not query.strip():
            return jsonify({"error": "Query is required"}), 400
        
        print(f"🔍 Processing chat query for user {user_id} in session {session_id}: {query}")
        
        # Get chatbot integration service
        chatbot_service = get_chatbot_integration()
        
        # Process query with LangGraph chatbot agents
        result = chatbot_service.process_query(
            user_query=query,
            user_id=user_id,
            chat_history=chat_history
        )
        
        # Extract chat name from the result if available
        chat_name = result.get('chat_name', 'New Chat')
        
        # Save messages to session document if available and session_id provided
        if mongo_db is not None and result.get('response') and session_id:
            try:
                # Get the session document
                session_ref = mongo_db.chat_sessions.find_one({'_id': ObjectId(session_id)})
                
                if session_ref:
                    session_data = session_ref
                    messages = session_data.get('messages', [])
                    
                    # Add user message
                    user_message = {
                        'id': f"user_{int(time.time() * 1000)}",
                        'role': 'user',
                        'content': query,
                        'timestamp': datetime.now().isoformat()
                    }
                    messages.append(user_message)
                    
                    # Add AI response with agent metadata
                    ai_message = {
                        'id': f"ai_{int(time.time() * 1000)}",
                        'role': 'assistant',
                        'content': result['response'],
                        'timestamp': datetime.now().isoformat(),
                        'sources': result.get('sources', {}),
                        'processing_time': result.get('processing_time', 0),
                        'agent_metadata': {
                            'tools_used': result.get('sources', {}).get('collections_used', []),
                            'web_search_performed': result.get('sources', {}).get('web_search_performed', False),
                            'general_tool_used': result.get('sources', {}).get('general_tool_used', False),
                            'chat_history_included': result.get('sources', {}).get('chat_history_included', False)
                        }
                    }
                    messages.append(ai_message)
                    
                    # Update session with new messages and chat name if it's still "New Chat"
                    update_data = {
                        **session_data,
                        'messages': messages,
                        'last_updated': datetime.now(),
                        'message_count': len(messages)
                    }
                    
                    # Update chat name if it's still "New Chat" and we have a better name
                    if session_data.get('title') == 'New Chat' and chat_name != 'New Chat':
                        update_data['title'] = chat_name
                        print(f"📝 Updating chat title to: {chat_name}")
                    
                    mongo_db.chat_sessions.replace_one({'_id': ObjectId(session_id)}, update_data)
                    
                    # Invalidate cache
                    invalidate_chat_cache(user_id)
                    
                    print(f"💾 Chat messages saved to session {session_id} for user {user_id}")
                else:
                    print(f"  Session {session_id} not found")
                    
            except Exception as e:
                print(f"  Error saving chat messages to session: {e}")
                # Don't fail the request if session saving fails
        
        # Also save to legacy chat_history for backward compatibility
        if mongo_db is not None and result.get('response'):
            try:
                chat_doc = {
                    'user_id': user_id,
                    'query': query,
                    'response': result['response'],
                    'timestamp': datetime.now(),
                    'sources': result.get('sources', {}),
                    'processing_time': result.get('processing_time', 0),
                    'session_id': session_id
                }
                mongo_db.chat_history.insert_one(chat_doc)
            except Exception as e:
                print(f"  Error saving to legacy chat_history: {e}")
        
        return jsonify({
            "success": True,
            "response": result['response'],
            "sources": result.get('sources', {}),
            "processing_time": result.get('processing_time', 0),
            "error": result.get('error', False)
        }), 200
        
    except Exception as e:
        print(f"  Chat query error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "I apologize, but I encountered an error processing your query."
        }), 500

@app.route('/api/chat/stream', methods=['POST'])
@jwt_required()
def chat_stream():
    """Stream chat response"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        query = data.get('query', '')
        chat_history = data.get('chat_history', [])
        
        if not query.strip():
            return jsonify({"error": "Query is required"}), 400
        
        print(f"🌊 Streaming chat response for user {user_id}: {query}")
        
        def generate():
            try:
                for token in get_chatbot_integration().stream_query(
                    user_query=query,
                    user_id=user_id,
                    chat_history=chat_history
                ):
                    yield f"data: {json.dumps({'token': token})}\n\n"
                
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                error_data = json.dumps({'error': str(e)})
                yield f"data: {error_data}\n\n"
        
        return Response(
            generate(),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        )
        
    except Exception as e:
        print(f"  Chat stream error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    """Get user's chat sessions with caching"""
    try:
        user_id = get_jwt_identity()
        
        # Try to get from cache first
        if redis_client:
            cache_key = f"chat_sessions:{user_id}"
            cached_data = redis_client.get(cache_key)
            if cached_data:
                try:
                    return jsonify(json.loads(cached_data))
                except:
                    pass
        
        if mongo_db is not None:
            # Query chat sessions from Firestore (without ordering to avoid index requirement)
            session_refs = mongo_db.chat_sessions.find({'user_id': user_id})
            
            sessions = []
            for session_ref in session_refs:
                session_data = mongo_doc_to_json(session_ref)
                session_data['created_at'] = session_data['created_at'].isoformat() if hasattr(session_data['created_at'], 'isoformat') else str(session_data['created_at'])
                session_data['last_updated'] = session_data['last_updated'].isoformat() if hasattr(session_data['last_updated'], 'isoformat') else str(session_data['last_updated'])
                sessions.append(session_data)
            
            # Sort sessions by last_updated in Python (descending)
            sessions.sort(key=lambda x: x['last_updated'], reverse=True)
            
            result = {
                "success": True,
                "sessions": sessions
            }
            
            # Cache the result
            if redis_client:
                try:
                    cache_key = f"chat_sessions:{user_id}"
                    redis_client.setex(cache_key, 3600, json.dumps(result))  # 1 hour cache
                except:
                    pass
            
            return jsonify(result), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Get chat sessions error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions', methods=['POST'])
@jwt_required()
def create_chat_session():
    """Create a new chat session"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        title = data.get('title', 'New Chat')
        
        if mongo_db is not None:
            session_doc = {
                'user_id': user_id,
                'title': title,
                'created_at': datetime.now(),
                'last_updated': datetime.now(),
                'message_count': 0,
                'messages': []  # Store all messages as JSON array
            }
            
            session_ref = mongo_db.chat_sessions.insert_one(session_doc)
            session_id = str(session_ref.inserted_id)
            
            # Invalidate cache
            invalidate_chat_cache(user_id)
            
            return jsonify({
                "success": True,
                "session_id": session_id,
                "message": "Chat session created successfully"
            }), 201
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Create chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['GET'])
@jwt_required()
def get_chat_session_messages(session_id):
    """Get messages for a specific chat session"""
    try:
        user_id = get_jwt_identity()
        
        if mongo_db is not None:
            # Verify session belongs to user
            session_ref = mongo_db.chat_sessions.find_one({'_id': ObjectId(session_id)})
            
            if not session_ref:
                return jsonify({"error": "Chat session not found"}), 404
                
            session_data = mongo_doc_to_json(session_ref)
            if session_data['user_id'] != user_id:
                return jsonify({"error": "Unauthorized access to chat session"}), 403
            
            return jsonify({
                "success": True,
                "session": session_data,
                "messages": session_data.get('messages', [])
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Get chat session messages error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['PUT'])
@jwt_required()
def update_chat_session(session_id):
    """Update chat session title"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        title = data.get('title', '')
        
        if not title.strip():
            return jsonify({"error": "Title is required"}), 400
        
        if mongo_db is not None:
            # Verify session belongs to user
            session_ref = mongo_db.chat_sessions.find_one({'_id': ObjectId(session_id)})
            
            if not session_ref:
                return jsonify({"error": "Chat session not found"}), 404
                
            session_data = mongo_doc_to_json(session_ref)
            if session_data['user_id'] != user_id:
                return jsonify({"error": "Unauthorized access to chat session"}), 403
            
            # Update session title
            mongo_db.chat_sessions.replace_one({'_id': ObjectId(session_id)}, {
                **session_data,
                'title': title,
                'last_updated': datetime.now()
            })
            
            # Invalidate cache
            invalidate_chat_cache(user_id)
            
            return jsonify({
                "success": True,
                "message": "Chat session updated successfully"
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Update chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_session(session_id):
    """Delete a chat session"""
    try:
        user_id = get_jwt_identity()
        
        if mongo_db is not None:
            # Verify session belongs to user
            session_ref = mongo_db.chat_sessions.find_one({'_id': ObjectId(session_id)})
            
            if not session_ref:
                return jsonify({"error": "Chat session not found"}), 404
                
            session_data = mongo_doc_to_json(session_ref)
            if session_data['user_id'] != user_id:
                return jsonify({"error": "Unauthorized access to chat session"}), 403
            
            # Delete the session (messages are stored within the session document)
            mongo_db.chat_sessions.delete_one({'_id': ObjectId(session_id)})
            
            # Invalidate cache
            invalidate_chat_cache(user_id)
            
            return jsonify({
                "success": True,
                "message": "Chat session deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Delete chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get user's chat history (legacy endpoint)"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        
        if mongo_db is not None:
            # Query chat history from Firestore
            chat_refs = mongo_db.chat_history.find({'user_id': user_id}).sort('timestamp', -1).limit(limit)
            
            chat_history = []
            for chat_ref in chat_refs:
                chat_data = mongo_doc_to_json(chat_ref)
                chat_data['timestamp'] = chat_data['timestamp'].isoformat() if hasattr(chat_data['timestamp'], 'isoformat') else str(chat_data['timestamp'])
                chat_history.append(chat_data)
            
            return jsonify({
                "success": True,
                "chat_history": chat_history
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Get chat history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/rag/stats', methods=['GET'])
@jwt_required()
def get_rag_stats():
    """Get RAG system statistics"""
    try:
        chatbot_service = get_chatbot_integration()
        stats = chatbot_service.get_system_stats()
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        print(f"  RAG stats error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chat/user-history', methods=['GET'])
@jwt_required()
def get_user_chat_history():
    """Get comprehensive chat history for a user"""
    try:
        user_id = get_jwt_identity()
        
        if mongo_db is not None:
            # Get all chat sessions for the user (without ordering to avoid index requirement)
            session_refs = mongo_db.chat_sessions.find({'user_id': user_id})
            
            chat_history = []
            for session_ref in session_refs:
                session_data = mongo_doc_to_json(session_ref)
                session_info = {
                    'session_id': str(session_ref['_id']),
                    'title': session_data.get('title', 'Untitled'),
                    'created_at': session_data['created_at'].isoformat() if hasattr(session_data['created_at'], 'isoformat') else str(session_data['created_at']),
                    'last_updated': session_data['last_updated'].isoformat() if hasattr(session_data['last_updated'], 'isoformat') else str(session_data['last_updated']),
                    'message_count': session_data.get('message_count', 0),
                    'messages': session_data.get('messages', [])
                }
                chat_history.append(session_info)
            
            # Sort sessions by last_updated in Python (descending)
            chat_history.sort(key=lambda x: x['last_updated'], reverse=True)
            
            return jsonify({
                "success": True,
                "user_id": user_id,
                "total_sessions": len(chat_history),
                "total_messages": sum(session['message_count'] for session in chat_history),
                "chat_history": chat_history
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Get user chat history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/courses', methods=['GET'])
@jwt_required()
def get_courses():
    try:
        courses = []
        docs = mongo_db.courses.find()
        for doc in docs:
            course = mongo_doc_to_json(doc)
            courses.append(course)
        return jsonify({'success': True, 'courses': courses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/courses/<id>', methods=['GET'])
@jwt_required()
def get_course(id):
    collection_name = request.args.get('collection_name', 'courses')
    try:
        collection = get_chatbot_integration().load_vector_store(collection_name)
        result = collection.get(ids=[id], include=['metadatas', 'documents'])
        if result['ids']:
            course = {
                'id': result['ids'][0],
                'metadata': result['metadatas'][0],
                'content': result['documents'][0]
            }
            return jsonify({'success': True, 'course': course})
        else:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route('/api/faculty', methods=['GET'])
@jwt_required()
def get_faculty():
    """Fetches all documents from the faculty collection."""
    try:
        faculty_list = []
        # This line correctly points to your 'faculty' collection.
        docs = mongo_db.faculty.find()
        for doc in docs:
            # Convert MongoDB document to JSON
            mongo_faculty = mongo_doc_to_json(doc)
            # Convert to admin dashboard format for consistency
            admin_faculty = mongo_faculty_to_admin_format(mongo_faculty)
            faculty_list.append(admin_faculty)
        # The key 'faculty' matches the frontend code's expectation.
        return jsonify({'success': True, 'faculty': faculty_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/faculty/<id>', methods=['GET'])
@jwt_required()
def get_single_faculty(id):
    """Fetches a single faculty member by their MongoDB document ID."""
    try:
        # Find the document in the 'faculty' collection by its ObjectId
        doc = mongo_db.faculty.find_one({'_id': ObjectId(id)})

        if doc:
            # Convert MongoDB document to JSON
            mongo_faculty = mongo_doc_to_json(doc)
            # Convert to admin dashboard format for consistency
            admin_faculty = mongo_faculty_to_admin_format(mongo_faculty)
            return jsonify({'success': True, 'professor': admin_faculty})
        else:
            return jsonify({'success': False, 'error': 'Faculty not found'}), 404
    except Exception as e:
        # This will catch errors, including an invalid ID format
        return jsonify({'success': False, 'error': str(e)}), 500

# --- Course Reviews Endpoints ---
@app.route('/api/courses/<course_id>/reviews', methods=['GET'])
@jwt_required()
def get_course_reviews(course_id):
    try:
        reviews = []
        docs = mongo_db.course_reviews.find({'course_id': course_id})
        for doc in docs:
            review = mongo_doc_to_json(doc)
            reviews.append(review)
        return jsonify({'success': True, 'reviews': bson_safe(reviews)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/courses/<course_id>/reviews', methods=['POST'])
@jwt_required()
def add_course_review(course_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        rating = data.get('rating')
        text = data.get('text', '')
        isAnonymous = data.get('isAnonymous', False)
        user_doc = mongo_db.users.find_one({'uid': user_id})
        if isAnonymous or not user_doc:
            userName = "Anonymous"
        else:
            userName = user_doc.get('fullName') or user_doc.get('email', '').split('@')[0]
        review_doc = {
            'course_id': course_id,
            'user_id': user_id,
            'userName': userName,
            'rating': rating,
            'text': text,
            'isAnonymous': isAnonymous,
            'createdAt': datetime.now()
        }
        result = mongo_db.course_reviews.insert_one(review_doc)
        return jsonify({'success': True, 'review': bson_safe(review_doc)}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
# --- Professor Reviews Endpoints ---
@app.route('/api/faculty/<faculty_id>/reviews', methods=['GET'])
@jwt_required()
def get_professor_reviews(faculty_id):
    """Fetches all reviews for a specific professor."""
    try:
        reviews = []
        # Find reviews matching the faculty_id in a new 'professor_reviews' collection
        docs = mongo_db.professor_reviews.find({'faculty_id': faculty_id})
        for doc in docs:
            review = mongo_doc_to_json(doc)
            reviews.append(review)
        return jsonify({'success': True, 'reviews': reviews}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/faculty/<faculty_id>/reviews', methods=['POST'])
@jwt_required()
def add_professor_review(faculty_id):
    """Adds a new review for a specific professor."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        rating = data.get('rating')
        text = data.get('text', '')
        isAnonymous = data.get('isAnonymous', False)

        # Get the user's name for the review
        user_doc = mongo_db.users.find_one({'uid': user_id})
        if isAnonymous or not user_doc:
            userName = "Anonymous"
        else:
            userName = user_doc.get('fullName') or user_doc.get('email', '').split('@')[0]

        # Create the review document
        review_doc = {
            'faculty_id': faculty_id,
            'user_id': user_id,
            'userName': userName,
            'rating': rating,
            'text': text,
            'isAnonymous': isAnonymous,
            'createdAt': datetime.now()
        }
        # Insert the review into a new 'professor_reviews' collection
        result = mongo_db.professor_reviews.insert_one(review_doc)
        review_doc['id'] = str(result.inserted_id)

        return jsonify({'success': True, 'review': mongo_doc_to_json(review_doc)}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- fetch all course and professor reviews ---

@app.route('/api/reviews/courses', methods=['GET'])
@jwt_required()
def get_all_course_reviews():
    """Fetches all course reviews from the database."""
    try:
        docs = mongo_db.course_reviews.find()
        reviews = [mongo_doc_to_json(doc) for doc in docs]
        return jsonify({'success': True, 'reviews': reviews}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reviews/professors', methods=['GET'])
@jwt_required()
def get_all_professor_reviews():
    """Fetches all professor reviews from the database."""
    try:
        docs = mongo_db.professor_reviews.find()
        reviews = [mongo_doc_to_json(doc) for doc in docs]
        return jsonify({'success': True, 'reviews': reviews}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        if mongo_db is None:
            return jsonify({"error": "Database not available"}), 500
        user_doc = mongo_db.users.find_one({'uid': user_id})
        if not user_doc or user_doc.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

@app.route('/api/admin/collections', methods=['GET'])
@jwt_required()
@admin_required
def get_collections():
    try:
        stats = get_chatbot_integration().get_system_stats()
        return jsonify({'success': True, 'collections': stats['collection_names']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def sync_course_to_chroma(course_id, course_data):
    """Sync course data to Chroma vector database"""
    try:
        collection = get_chatbot_integration().load_vector_store('AllCourseRelatedData')
        if collection:
            content = json.dumps(course_data)
            metadata = {'title': course_data.get('Course Title', ''), 'code': course_data.get('Course Code', '')}
            collection.upsert(ids=[course_id], documents=[content], metadatas=[metadata])
            print(f"✅ Course {course_id} synced to Chroma")
        else:
            print(f"⚠️  Chroma collection 'AllCourseRelatedData' not available")
    except Exception as e:
        print(f"❌ Error syncing course {course_id} to Chroma: {e}")

def delete_from_chroma(course_id):
    """Delete course data from Chroma vector database"""
    try:
        collection = get_chatbot_integration().load_vector_store('AllCourseRelatedData')
        if collection:
            collection.delete(ids=[course_id])
            print(f"✅ Course {course_id} deleted from Chroma")
        else:
            print(f"⚠️  Chroma collection 'AllCourseRelatedData' not available")
    except Exception as e:
        print(f"❌ Error deleting course {course_id} from Chroma: {e}")

@app.route('/api/admin/courses', methods=['GET'])
@jwt_required()
@admin_required
def get_all_courses():
    try:
        courses = []
        docs = mongo_db.courses.find()
        for doc in docs:
            course = mongo_doc_to_json(doc)
            courses.append(course)
        return jsonify({'success': True, 'courses': courses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/courses', methods=['POST'])
@jwt_required()
@admin_required
def add_course():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Data is required'}), 400
    try:
        result = mongo_db.courses.insert_one(data)
        course_id = str(result.inserted_id)
        sync_course_to_chroma(course_id, data)
        return jsonify({'success': True, 'id': course_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/courses/<id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_course(id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Data is required'}), 400
    try:
        course_ref = mongo_db.courses.find_one({'_id': ObjectId(id)})
        if not course_ref:
            return jsonify({'error': 'Course not found'}), 404
        mongo_db.courses.update_one({'_id': ObjectId(id)}, {'$set': data})
        sync_course_to_chroma(id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/courses/<id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_course(id):
    try:
        course_ref = mongo_db.courses.find_one({'_id': ObjectId(id)})
        if not course_ref:
            return jsonify({'error': 'Course not found'}), 404
        mongo_db.courses.delete_one({'_id': ObjectId(id)})
        delete_from_chroma(id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/courses/<id>', methods=['GET'])
@jwt_required()
@admin_required
def get_admin_course(id):
    try:
        doc = mongo_db.courses.find_one({'_id': ObjectId(id)})
        if doc:
            course = mongo_doc_to_json(doc)
            course['id'] = id
            return jsonify({'success': True, 'course': course})
        return jsonify({'success': False, 'error': 'Course not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- Faculty Admin CRUD Endpoints ---
@app.route('/api/admin/faculty', methods=['GET'])
@jwt_required()
@admin_required
def get_all_faculty():
    """Admin endpoint to get all faculty members"""
    try:
        faculty_list = []
        docs = mongo_db.faculty.find()
        for doc in docs:
            # Convert MongoDB document to JSON
            mongo_faculty = mongo_doc_to_json(doc)
            # Convert to admin dashboard format
            admin_faculty = mongo_faculty_to_admin_format(mongo_faculty)
            faculty_list.append(admin_faculty)
        return jsonify({'success': True, 'faculty': faculty_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/faculty', methods=['POST'])
@jwt_required()
@admin_required
def add_faculty():
    """Admin endpoint to add a new faculty member"""
    admin_data = request.get_json()
    if not admin_data:
        return jsonify({'error': 'Data is required'}), 400
    try:
        # Convert admin format to MongoDB format
        mongo_data = admin_format_to_mongo_faculty(admin_data)
        # Add creation timestamp
        mongo_data['createdAt'] = datetime.now()
        mongo_data['updatedAt'] = datetime.now()
        result = mongo_db.faculty.insert_one(mongo_data)
        faculty_id = str(result.inserted_id)
        return jsonify({'success': True, 'id': faculty_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/faculty/<id>', methods=['GET'])
@jwt_required()
@admin_required
def get_admin_faculty(id):
    """Admin endpoint to get a single faculty member"""
    try:
        doc = mongo_db.faculty.find_one({'_id': ObjectId(id)})
        if doc:
            # Convert MongoDB document to JSON
            mongo_faculty = mongo_doc_to_json(doc)
            # Convert to admin dashboard format
            admin_faculty = mongo_faculty_to_admin_format(mongo_faculty)
            admin_faculty['id'] = id
            return jsonify({'success': True, 'faculty': admin_faculty})
        return jsonify({'success': False, 'error': 'Faculty not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/faculty/<id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_faculty(id):
    """Admin endpoint to update a faculty member"""
    admin_data = request.get_json()
    if not admin_data:
        return jsonify({'error': 'Data is required'}), 400
    try:
        faculty_ref = mongo_db.faculty.find_one({'_id': ObjectId(id)})
        if not faculty_ref:
            return jsonify({'error': 'Faculty not found'}), 404
        
        # Convert admin format to MongoDB format
        mongo_data = admin_format_to_mongo_faculty(admin_data)
        # Add update timestamp
        mongo_data['updatedAt'] = datetime.now()
        mongo_db.faculty.update_one({'_id': ObjectId(id)}, {'$set': mongo_data})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/faculty/<id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_faculty(id):
    """Admin endpoint to delete a faculty member"""
    try:
        faculty_ref = mongo_db.faculty.find_one({'_id': ObjectId(id)})
        if not faculty_ref:
            return jsonify({'error': 'Faculty not found'}), 404
        
        # Also delete related reviews
        mongo_db.professor_reviews.delete_many({'faculty_id': id})
        mongo_db.faculty.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
# Utility endpoint to check and fix profile completion status
@app.route('/api/admin/fix-profile-completion', methods=['POST'])
@jwt_required()
def fix_profile_completion():
    """Fix profile completion status for users who have profile data but missing the flag"""
    try:
        user_id = get_jwt_identity()
        
        if mongo_db is not None:
            # Get user document
            user_doc = mongo_db.users.find_one({'uid': user_id})
            if user_doc:
                # Check if user has profile data but missing profileCompleted flag
                has_profile_data = (
                    user_doc.get('fullName') or 
                    user_doc.get('resumeData') or 
                    any(key in user_doc for key in ['experience', 'education', 'skills', 'summary'])
                )
                
                if has_profile_data and not user_doc.get('profileCompleted'):
                    # Update the document to set profileCompleted to True
                    user_doc['profileCompleted'] = True
                    user_doc['updatedAt'] = datetime.now()
                    mongo_db.users.replace_one({'uid': user_id}, user_doc)
                    
                    return jsonify({
                        "success": True,
                        "message": "Profile completion status fixed",
                        "profileCompleted": True
                    }), 200
                else:
                    return jsonify({
                        "success": True,
                        "message": "Profile completion status is correct",
                        "profileCompleted": user_doc.get('profileCompleted', False)
                    }), 200
            else:
                return jsonify({"success": False, "error": "User not found"}), 404
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
    except Exception as e:
        print(f"  Fix profile completion error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Submit feedback for a chat message"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        message_id = data.get('message_id')
        feedback = data.get('feedback')  # 'positive' or 'negative'
        timestamp = data.get('timestamp')
        
        if not message_id or not feedback:
            return jsonify({"error": "Message ID and feedback are required"}), 400
        
        if feedback not in ['positive', 'negative']:
            return jsonify({"error": "Feedback must be 'positive' or 'negative'"}), 400
        
        # Save feedback to database
        if mongo_db is not None:
            feedback_doc = {
                'user_id': user_id,
                'message_id': message_id,
                'feedback': feedback,
                'timestamp': datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.now(),
                'created_at': datetime.now()
            }
            mongo_db.message_feedback.insert_one(feedback_doc)
            
            # Also update the message in chat_sessions if it exists
            try:
                # Find the message in chat_sessions and update it
                result = mongo_db.chat_sessions.update_one(
                    {'messages.id': message_id},
                    {'$set': {'messages.$.feedback': feedback}}
                )
                print(f"✅ Feedback saved for message {message_id}: {feedback}")
            except Exception as e:
                print(f"⚠️  Could not update message in chat_sessions: {e}")
        
        return jsonify({
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback": feedback
        }), 200
        
    except Exception as e:
        print(f"❌ Feedback submission error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(debug=True, host='0.0.0.0', port=port) 
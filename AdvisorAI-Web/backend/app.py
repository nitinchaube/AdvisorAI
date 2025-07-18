from flask import Flask, request, session, jsonify, Response
from flask_session import Session
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth, credentials, firestore
import os
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime
import json
from dotenv import load_dotenv
from resume_processor import ResumeProcessor
from rag_service import rag_service
import logging
import time
import redis
from functools import wraps

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
Session(app)
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

# Initialize Firebase Admin SDK
try:
    # Check if Firebase app is already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate('firebase_key.json')
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized successfully")
    else:
        print("✅ Firebase Admin SDK already initialized")
except Exception as e:
    print(f"❌ Firebase Admin SDK initialization failed: {e}")

# Initialize Firestore
try:
    db = firestore.client()
    print("✅ Firestore client initialized")
except Exception as e:
    print(f"❌ Firestore client initialization failed: {e}")
    db = None

# Initialize Resume Processor
try:
    resume_processor = ResumeProcessor()
    print("✅ Resume processor initialized")
except Exception as e:
    print(f"❌ Resume processor initialization failed: {e}")
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
    print("✅ Redis client initialized")
except Exception as e:
    print(f"❌ Redis client initialization failed: {e}")
    redis_client = None

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

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "firebase_initialized": bool(firebase_admin._apps),
        "firestore_available": db is not None,
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
        print(f"❌ Debug extraction error: {str(e)}")
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
        if db:
            user_doc = {
                'uid': user_record.uid,
                'email': email,
                'fullName': full_name,
                'createdAt': datetime.now(),
                'profileCompleted': False,
                'resumeData': {}
            }
            db.collection('users').document(user_record.uid).set(user_doc)

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
        print(f"❌ Signup error: {str(e)}")
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
        print(f"❌ Signin error: {str(e)}")
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
        print(f"❌ Token signin error: {str(e)}")
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
                if db:
                    user_ref = db.collection('users').document(user_id)
                    
                    # Check if document exists, if not create it
                    user_doc = user_ref.get()
                    if user_doc.exists:
                        # Update existing document
                        user_ref.update({
                            'resumeData': result['parsedData'],
                            'profileCompleted': True,
                            'lastResumeUpdate': datetime.now(),
                            'resumeText': result['originalText']
                        })
                    else:
                        # Create new document
                        user_ref.set({
                            'uid': user_id,
                            'resumeData': result['parsedData'],
                            'profileCompleted': True,
                            'lastResumeUpdate': datetime.now(),
                            'resumeText': result['originalText'],
                            'createdAt': datetime.now()
                        })
                
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
        print(f"❌ Resume upload error: {str(e)}")
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
        
        if db:
            user_doc = db.collection('users').document(user_id).get()
            if user_doc.exists:
                return jsonify({
                    "success": True,
                    "profile": user_doc.to_dict()
                }), 200
            else:
                return jsonify({"error": "User profile not found"}), 404
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"❌ Get profile error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Update user profile
@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """Update user profile data"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if db:
            user_ref = db.collection('users').document(user_id)
            
            # Check if document exists, if not create it
            user_doc = user_ref.get()
            if user_doc.exists:
                # Update existing document
                user_ref.update({
                    **data,
                    'updatedAt': datetime.now()
                })
            else:
                # Create new document
                user_ref.set({
                    'uid': user_id,
                    **data,
                    'createdAt': datetime.now(),
                    'updatedAt': datetime.now()
                })
            
            return jsonify({
                "success": True,
                "message": "Profile updated successfully"
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"❌ Update profile error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Chat endpoints
@app.route('/api/chat/query', methods=['POST'])
@jwt_required()
def chat_query():
    """Process chat query with RAG"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        query = data.get('query', '')
        chat_history = data.get('chat_history', [])
        session_id = data.get('session_id')
        
        if not query.strip():
            return jsonify({"error": "Query is required"}), 400
        
        print(f"🔍 Processing chat query for user {user_id} in session {session_id}: {query}")
        
        # Process query with RAG service
        result = rag_service.process_query(
            user_query=query,
            user_id=user_id,
            chat_history=chat_history
        )
        
        # Save messages to session document if available and session_id provided
        if db and result.get('response') and session_id:
            try:
                # Get the session document
                session_ref = db.collection('chat_sessions').document(session_id)
                session_doc = session_ref.get()
                
                if session_doc.exists:
                    session_data = session_doc.to_dict()
                    messages = session_data.get('messages', [])
                    
                    # Add user message
                    user_message = {
                        'id': f"user_{int(time.time() * 1000)}",
                        'role': 'user',
                        'content': query,
                        'timestamp': datetime.now().isoformat()
                    }
                    messages.append(user_message)
                    
                    # Add AI response
                    ai_message = {
                        'id': f"ai_{int(time.time() * 1000)}",
                        'role': 'assistant',
                        'content': result['response'],
                        'timestamp': datetime.now().isoformat(),
                        'sources': result.get('sources', {}),
                        'processing_time': result.get('processing_time', 0)
                    }
                    messages.append(ai_message)
                    
                    # Update session with new messages
                    session_ref.update({
                        'messages': messages,
                        'last_updated': datetime.now(),
                        'message_count': len(messages)
                    })
                    
                    # Invalidate cache
                    invalidate_chat_cache(user_id)
                    
                    print(f"💾 Chat messages saved to session {session_id} for user {user_id}")
                else:
                    print(f"❌ Session {session_id} not found")
                    
            except Exception as e:
                print(f"❌ Error saving chat messages to session: {e}")
        
        # Also save to legacy chat_history for backward compatibility
        if db and result.get('response'):
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
                db.collection('chat_history').add(chat_doc)
            except Exception as e:
                print(f"❌ Error saving to legacy chat_history: {e}")
        
        return jsonify({
            "success": True,
            "response": result['response'],
            "sources": result.get('sources', {}),
            "processing_time": result.get('processing_time', 0),
            "error": result.get('error', False)
        }), 200
        
    except Exception as e:
        print(f"❌ Chat query error: {str(e)}")
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
                for token in rag_service.stream_query(
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
        print(f"❌ Chat stream error: {str(e)}")
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
        
        if db:
            # Query chat sessions from Firestore (without ordering to avoid index requirement)
            session_refs = db.collection('chat_sessions').where('user_id', '==', user_id).stream()
            
            sessions = []
            for session_ref in session_refs:
                session_data = session_ref.to_dict()
                session_data['id'] = session_ref.id
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
        print(f"❌ Get chat sessions error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions', methods=['POST'])
@jwt_required()
def create_chat_session():
    """Create a new chat session"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        title = data.get('title', 'New Chat')
        
        if db:
            session_doc = {
                'user_id': user_id,
                'title': title,
                'created_at': datetime.now(),
                'last_updated': datetime.now(),
                'message_count': 0,
                'messages': []  # Store all messages as JSON array
            }
            
            session_ref = db.collection('chat_sessions').add(session_doc)
            session_id = session_ref[1].id
            
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
        print(f"❌ Create chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['GET'])
@jwt_required()
def get_chat_session_messages(session_id):
    """Get messages for a specific chat session"""
    try:
        user_id = get_jwt_identity()
        
        if db:
            # Verify session belongs to user
            session_ref = db.collection('chat_sessions').document(session_id)
            session_doc = session_ref.get()
            
            if not session_doc.exists:
                return jsonify({"error": "Chat session not found"}), 404
                
            session_data = session_doc.to_dict()
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
        print(f"❌ Get chat session messages error: {str(e)}")
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
        
        if db:
            # Verify session belongs to user
            session_ref = db.collection('chat_sessions').document(session_id)
            session_doc = session_ref.get()
            
            if not session_doc.exists:
                return jsonify({"error": "Chat session not found"}), 404
                
            session_data = session_doc.to_dict()
            if session_data['user_id'] != user_id:
                return jsonify({"error": "Unauthorized access to chat session"}), 403
            
            # Update session title
            session_ref.update({
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
        print(f"❌ Update chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_session(session_id):
    """Delete a chat session"""
    try:
        user_id = get_jwt_identity()
        
        if db:
            # Verify session belongs to user
            session_ref = db.collection('chat_sessions').document(session_id)
            session_doc = session_ref.get()
            
            if not session_doc.exists:
                return jsonify({"error": "Chat session not found"}), 404
                
            session_data = session_doc.to_dict()
            if session_data['user_id'] != user_id:
                return jsonify({"error": "Unauthorized access to chat session"}), 403
            
            # Delete the session (messages are stored within the session document)
            session_ref.delete()
            
            # Invalidate cache
            invalidate_chat_cache(user_id)
            
            return jsonify({
                "success": True,
                "message": "Chat session deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"❌ Delete chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get user's chat history (legacy endpoint)"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        
        if db:
            # Query chat history from Firestore
            chat_refs = db.collection('chat_history').where('user_id', '==', user_id).order_by('timestamp', direction='DESCENDING').limit(limit).stream()
            
            chat_history = []
            for chat_ref in chat_refs:
                chat_data = chat_ref.to_dict()
                chat_data['id'] = chat_ref.id
                chat_data['timestamp'] = chat_data['timestamp'].isoformat() if hasattr(chat_data['timestamp'], 'isoformat') else str(chat_data['timestamp'])
                chat_history.append(chat_data)
            
            return jsonify({
                "success": True,
                "chat_history": chat_history
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        print(f"❌ Get chat history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/rag/stats', methods=['GET'])
@jwt_required()
def get_rag_stats():
    """Get RAG system statistics"""
    try:
        stats = rag_service.get_system_stats()
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
    except Exception as e:
        print(f"❌ Get RAG stats error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/user-history', methods=['GET'])
@jwt_required()
def get_user_chat_history():
    """Get comprehensive chat history for a user"""
    try:
        user_id = get_jwt_identity()
        
        if db:
            # Get all chat sessions for the user (without ordering to avoid index requirement)
            session_refs = db.collection('chat_sessions').where('user_id', '==', user_id).stream()
            
            chat_history = []
            for session_ref in session_refs:
                session_data = session_ref.to_dict()
                session_info = {
                    'session_id': session_ref.id,
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
        print(f"❌ Get user chat history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(debug=True, host='0.0.0.0', port=port) 
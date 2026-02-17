from dotenv import load_dotenv
import os

# Load environment variables FIRST — before any os.environ calls
load_dotenv()

from flask import Flask, request, session, jsonify, Response, g
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime
import json
import threading
from urllib.parse import urlparse
from resume_processor import ResumeProcessor
# Replace RAG service with chatbot integration
from chatbot_integration import get_chatbot_integration
from faculty_data_mapper import mongo_faculty_to_admin_format, admin_format_to_mongo_faculty
import logging
import time
from functools import wraps
import uuid
from langchain_core.documents import Document

# Configure logging from environment
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# --- MongoDB Setup ---
from pymongo import MongoClient
from bson import ObjectId
MONGO_URI = os.environ.get('MONGO_URI')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'AdvisorAI')
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]

# Ensure unique index on portfolioName
try:
    mongo_db.users.create_index("portfolioName", unique=True, sparse=True)
    logger.info("Ensured unique index on portfolioName")
except Exception as e:
    logger.warning(f"Could not create unique index on portfolioName: {e}")

# Initialize Flask app
app = Flask(__name__)

# Configure Flask — secrets MUST be set via .env in production
_secret_key = os.environ.get('SECRET_KEY', '')
_jwt_secret_key = os.environ.get('JWT_SECRET_KEY', '')
_flask_env = os.environ.get('FLASK_ENV', 'development')

if _flask_env == 'production' and (not _secret_key or _secret_key == 'CHANGE_ME_TO_A_RANDOM_SECRET'):
    raise RuntimeError("SECRET_KEY must be set to a strong random value in production!")
if _flask_env == 'production' and (not _jwt_secret_key or _jwt_secret_key == 'CHANGE_ME_TO_A_RANDOM_JWT_SECRET'):
    raise RuntimeError("JWT_SECRET_KEY must be set to a strong random value in production!")

app.config['SECRET_KEY'] = _secret_key or 'dev-only-secret-key'
app.config['JWT_SECRET_KEY'] = _jwt_secret_key or 'dev-only-jwt-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(
    hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', '24'))
)

# Initialize extensions
JWTManager(app)

# CORS origins from environment (comma-separated)
_cors_origins_str = os.environ.get('CORS_ORIGINS', '')
if _cors_origins_str:
    CORS_ORIGINS = [origin.strip() for origin in _cors_origins_str.split(',') if origin.strip()]
else:
    # Fallback for development
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:5003",
        "http://127.0.0.1:5003",
    ]

# Enable CORS for all routes and allow credentials (cookies)
CORS(app, 
     supports_credentials=True, 
     origins=CORS_ORIGINS,
     allow_headers=[
         'Content-Type', 
         'Authorization', 
         'X-Requested-With',
         'Accept',
         'Origin',
         'Access-Control-Request-Method',
         'Access-Control-Request-Headers'
     ],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
     expose_headers=['Content-Range', 'X-Content-Range']
)
# Initialize Resume Processor
try:
    resume_processor = ResumeProcessor()
    logger.info("Resume processor initialized")
except Exception as e:
    logger.error(f"Resume processor initialization failed: {e}")
    resume_processor = None

# Initialize Firebase Admin SDK using Application Default Credentials (ADC).
# Local dev: run `gcloud auth application-default login`
# GCP runtime (Cloud Run / GKE / Cloud Functions): uses the default service account automatically.
if not firebase_admin._apps:
    firebase_admin.initialize_app()
    logger.info("Firebase Admin SDK initialized with Application Default Credentials")

# ────────────────────────────────────────────────────────────
# Background Job Scraper (runs in a daemon thread)
# Completely isolated — any crash here will NOT affect the API.
# ────────────────────────────────────────────────────────────
_scraper_status = {
    "enabled": False,
    "last_run": None,
    "last_status": "not started",
    "last_error": None,
    "runs": 0,
    "interval_hours": 0,
}

def _run_scraper_loop():
    """Background loop that scrapes jobs & internships every N hours."""
    interval_hours = float(os.environ.get('SCRAPER_INTERVAL_HOURS', '2'))
    interval_seconds = interval_hours * 3600
    _scraper_status["interval_hours"] = interval_hours

    # Lazy-import so the scraper module is only loaded when enabled
    try:
        from github_jobs_unified_scraper import UnifiedGitHubScraper
        scraper = UnifiedGitHubScraper()
    except Exception as exc:
        logger.error("Scraper import/init failed — disabling: %s", exc)
        _scraper_status["last_status"] = f"init failed: {exc}"
        _scraper_status["last_error"] = str(exc)
        return  # thread exits, app keeps running

    logger.info("Scraper thread started — interval: every %.1f hours", interval_hours)

    while True:
        try:
            logger.info("Scraper: starting run #%d …", _scraper_status["runs"] + 1)
            scraper.scrape_all_repositories()
            _scraper_status["runs"] += 1
            _scraper_status["last_run"] = datetime.utcnow().isoformat() + "Z"
            _scraper_status["last_status"] = "success"
            _scraper_status["last_error"] = None
            logger.info("Scraper: run #%d completed ✓", _scraper_status["runs"])
        except Exception as exc:
            _scraper_status["last_status"] = "error"
            _scraper_status["last_error"] = str(exc)
            logger.error("Scraper: run failed — %s. Will retry next cycle.", exc)

        # Sleep until the next cycle
        time.sleep(interval_seconds)


# Start the scraper thread only when enabled
_scraper_enabled = os.environ.get('SCRAPER_ENABLED', 'true').lower() in ('true', '1', 'yes')
if _scraper_enabled:
    _scraper_status["enabled"] = True
    _scraper_thread = threading.Thread(target=_run_scraper_loop, daemon=True)
    _scraper_thread.start()
    logger.info("Background job scraper ENABLED (daemon thread)")
else:
    logger.info("Background job scraper DISABLED (set SCRAPER_ENABLED=true to enable)")

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


def sanitize_profile_picture_url(profile_picture_url):
    """
    Validate and sanitize profile picture URL before persistence.
    Only HTTPS Firebase/Google Cloud Storage URLs are accepted.
    """
    if profile_picture_url is None:
        return None
    if not isinstance(profile_picture_url, str):
        raise ValueError("Profile picture must be a string URL.")

    cleaned_url = profile_picture_url.strip()
    if cleaned_url == "":
        return ""
    if len(cleaned_url) > 2048:
        raise ValueError("Profile picture URL is too long.")

    parsed_url = urlparse(cleaned_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("Profile picture must be a valid HTTPS URL.")

    host = parsed_url.netloc.lower()
    is_google_storage_host = host in {
        "firebasestorage.googleapis.com",
        "storage.googleapis.com",
    } or host.endswith(".storage.googleapis.com")

    if not is_google_storage_host:
        raise ValueError("Profile picture URL must point to Firebase/GCP Storage.")

    return cleaned_url

def verify_token(f):
    """Authentication decorator that requires a valid Firebase ID token AND verified email.
    
    If MongoDB says email is unverified, this decorator re-checks Firebase Auth
    directly (the source of truth) and syncs the status before deciding.
    This prevents stale MongoDB data from blocking users who already verified.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
        
        id_token = None
        if 'Authorization' in request.headers and request.headers['Authorization'].startswith('Bearer '):
            id_token = request.headers['Authorization'].split('Bearer ')[1]

        if not id_token:
            return jsonify({"error": "Authorization token is missing"}), 401

        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            
            if mongo_db is not None:
                user_doc = mongo_db.users.find_one({'uid': user_id})
                
                # If user doesn't exist in MongoDB, create a minimal profile
                if not user_doc:
                    logger.warning(f"User {user_id} not found in MongoDB, creating minimal profile")
                    try:
                        firebase_user = auth.get_user(user_id)
                        user_doc = {
                            'uid': user_id,
                            'email': firebase_user.email,
                            'fullName': firebase_user.display_name or '',
                            'createdAt': datetime.now(),
                            'profileCompleted': False,
                            'resumeData': {},
                            'role': 'user',
                            'emailVerified': firebase_user.email_verified
                        }
                        mongo_db.users.insert_one(user_doc)
                        logger.info(f"Created minimal profile for user {user_id}")
                    except Exception as create_error:
                        logger.error(f"Failed to create minimal profile: {create_error}")
                        return jsonify({"error": "User profile creation failed"}), 500
                
                # Check email verification – sync from Firebase if MongoDB is stale
                if not user_doc.get('emailVerified', False):
                    # MongoDB says unverified – double-check with Firebase (source of truth)
                    try:
                        firebase_user = auth.get_user(user_id)
                        if firebase_user.email_verified:
                            # Firebase says verified – sync to MongoDB
                            mongo_db.users.update_one(
                                {'uid': user_id},
                                {'$set': {'emailVerified': True, 'emailVerifiedAt': datetime.now()}}
                            )
                            user_doc['emailVerified'] = True
                            logger.info(f"Synced email verification from Firebase for user {user_id}")
                        else:
                            # Genuinely unverified
                            return jsonify({
                                "error": "Email not verified",
                                "emailVerified": False,
                                "message": "Please verify your email before accessing this feature",
                                "requiresEmailVerification": True
                            }), 403
                    except Exception as fb_error:
                        logger.error(f"Firebase check failed during verify_token: {fb_error}")
                        return jsonify({
                            "error": "Email not verified",
                            "emailVerified": False,
                            "message": "Please verify your email before accessing this feature",
                            "requiresEmailVerification": True
                        }), 403
                
                # Store user info in g for use in the route
                g.user = user_doc
            else:
                g.user = decoded_token
                
        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": f"Token verification failed: {e}"}), 401

        return f(*args, **kwargs)
    return decorated_function

# Email verification decorator (less strict than verify_token)
def verify_email_optional(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
        
        try:
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Missing or invalid authorization header"}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify JWT token
            decoded_token = auth.verify_id_token(token)
            if not decoded_token:
                return jsonify({"error": "Invalid token"}), 401
            
            user_id = decoded_token['uid']
            
            # Get user from MongoDB
            if mongo_db is not None:
                user_doc = mongo_db.users.find_one({'uid': user_id})
                
                # If user doesn't exist in MongoDB, create a minimal profile
                if not user_doc:
                    logger.warning(f"User {user_id} not found in MongoDB during verify_email_optional, creating minimal profile")
                    try:
                        firebase_user = auth.get_user(user_id)
                        user_doc = {
                            'uid': user_id,
                            'email': firebase_user.email,
                            'fullName': firebase_user.display_name or '',
                            'createdAt': datetime.now(),
                            'profileCompleted': False,
                            'resumeData': {},
                            'role': 'user',
                            'emailVerified': firebase_user.email_verified
                        }
                        mongo_db.users.insert_one(user_doc)
                        logger.info(f"Created minimal profile for user {user_id} in verify_email_optional")
                    except Exception as create_error:
                        logger.error(f"Failed to create minimal profile in verify_email_optional: {create_error}")
                        return jsonify({"error": "User profile creation failed"}), 500
                
                # Store user info in g for use in the route
                g.user = user_doc
            else:
                g.user = decoded_token
            
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return jsonify({"error": "Token verification failed"}), 401
    return decorated_function

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
@verify_token
def debug_text_extraction():
    """Debug text extraction from resume file"""
    try:
        user_id = g.user['uid']
        logger.debug(f"Debug text extraction for user: {user_id}")
        
        if 'resume' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.environ.get('UPLOAD_DIR', 'uploads')
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
        logger.error(f"Debug extraction error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Authentication endpoints
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User signup endpoint with email verification"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('fullName', '')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Create user in Firebase with email verification disabled initially
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=full_name,
            email_verified=False  # Start with unverified email
        )

        # Create user document in MongoDB
        if mongo_db is not None:
            user_doc = {
                'uid': user_record.uid,
                'email': email,
                'fullName': full_name,
                'createdAt': datetime.now(),
                'profileCompleted': False,
                'resumeData': {},
                'role': 'user',
                'emailVerified': False  # Track email verification status
            }
            mongo_db.users.insert_one(user_doc)

        # Send email verification
        try:
            verification_link = auth.generate_email_verification_link(email)
            logger.info(f"Email verification link generated for {email}")
            logger.debug(f"Verification link: {verification_link}")
        except Exception as email_error:
            logger.error(f"Failed to generate email verification link: {email_error}")

        # Create JWT token
        access_token = create_access_token(identity=user_record.uid)

        return jsonify({
            "message": "User created successfully. Please check your email to verify your account.",
            "user": {
                "uid": user_record.uid,
                "email": email,
                "fullName": full_name,
                "emailVerified": False
            },
            "access_token": access_token,
            "verification_required": True
        }), 201

    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/signin', methods=['POST'])
def signin():
    """User signin endpoint with email verification check.
    
    Uses Firebase Auth as the source of truth for email_verified
    and syncs status to MongoDB on every sign-in.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Get user record from Firebase (source of truth)
        user_record = auth.get_user_by_email(email)
        email_verified = user_record.email_verified  # Check Firebase directly

        if mongo_db is not None:
            user_doc = mongo_db.users.find_one({'uid': user_record.uid})
            
            if user_doc:
                # Sync email verification from Firebase → MongoDB
                mongo_verified = user_doc.get('emailVerified', False)
                if email_verified and not mongo_verified:
                    mongo_db.users.update_one(
                        {'uid': user_record.uid},
                        {'$set': {'emailVerified': True, 'emailVerifiedAt': datetime.now()}}
                    )
                    logger.info(f"Synced email verification during signin for user {user_record.uid}")
                
                # Sync Firebase custom claims with MongoDB role
                try:
                    mongo_role = user_doc.get('role')
                    if mongo_role:
                        current_claims = user_record.custom_claims or {}
                        if current_claims.get('role') != mongo_role:
                            auth.set_custom_user_claims(user_record.uid, {
                                'role': mongo_role,
                                'admin': mongo_role == 'admin'
                            })
                            logger.info(f"Synced Firebase custom claims for user {user_record.uid}")
                except Exception as sync_error:
                    logger.warning(f"Firebase custom claims sync failed: {sync_error}")

        # Create JWT token
        access_token = create_access_token(identity=user_record.uid)

        return jsonify({
            "message": "Signin successful",
            "user": {
                "uid": user_record.uid,
                "email": user_record.email,
                "fullName": user_record.display_name or "",
                "emailVerified": email_verified
            },
            "access_token": access_token,
            "verification_required": not email_verified
        }), 200

    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/auth/signin-with-token', methods=['POST'])
def signin_with_token():
    """Signin with Firebase ID token and check email verification.
    
    Always checks Firebase Auth directly for email_verified status
    and syncs it to MongoDB so both stay in sync.
    """
    try:
        data = request.get_json()
        id_token = data.get('idToken')

        if not id_token:
            return jsonify({"error": "ID token is required"}), 400

        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']

        # Get user record from Firebase (source of truth for email_verified)
        user_record = auth.get_user(user_id)
        email_verified = user_record.email_verified  # Check Firebase directly

        if mongo_db is not None:
            user_doc = mongo_db.users.find_one({'uid': user_id})
            
            if user_doc:
                # Sync email verification: if Firebase says verified, update MongoDB
                mongo_verified = user_doc.get('emailVerified', False)
                if email_verified and not mongo_verified:
                    mongo_db.users.update_one(
                        {'uid': user_id},
                        {'$set': {'emailVerified': True, 'emailVerifiedAt': datetime.now()}}
                    )
                    logger.info(f"Synced email verification during signin for user {user_id}")
                
                # Sync Firebase custom claims with MongoDB role
                try:
                    mongo_role = user_doc.get('role')
                    if mongo_role:
                        current_claims = user_record.custom_claims or {}
                        if current_claims.get('role') != mongo_role:
                            auth.set_custom_user_claims(user_id, {
                                'role': mongo_role,
                                'admin': mongo_role == 'admin'
                            })
                            logger.info(f"Synced Firebase custom claims for user {user_id}")
                except Exception as sync_error:
                    logger.warning(f"Firebase custom claims sync failed: {sync_error}")

        return jsonify({
            "message": "Signin successful",
            "user": {
                "uid": user_record.uid,
                "email": user_record.email,
                "fullName": user_record.display_name or "",
                "emailVerified": email_verified
            },
            "verification_required": not email_verified
        }), 200

    except Exception as e:
        logger.error(f"Signin with token error: {str(e)}")
        return jsonify({"error": "Invalid token"}), 401

# Email verification endpoints
@app.route('/api/auth/send-verification-email', methods=['POST'])
@verify_email_optional
def send_verification_email():
    """Send email verification link to user with 2-day expiration"""
    try:
        user_id = g.user['uid']
        email = g.user['email']
        
        # Configure action code settings with 2-day expiration
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
        action_code_settings = auth.ActionCodeSettings(
            url=f'{frontend_url}/email-verification',
            handle_code_in_app=True,
            dynamic_link_domain=None  # Disable dynamic links
        )
        
        # Generate email verification link with custom settings
        verification_link = auth.generate_email_verification_link(
            email,
            action_code_settings=action_code_settings
        )
        
        # In production, send this via email service (e.g. SendGrid, SES)
        logger.info(f"Email verification link generated for {email}")
        logger.debug(f"Verification link: {verification_link}")
        
        response_data = {
            "message": "Verification email sent successfully",
            "expires_in_days": 2
        }
        # Only include the link in non-production environments for testing
        if os.environ.get('FLASK_ENV', 'development') != 'production':
            response_data["verification_link"] = verification_link
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Send verification email error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/verify-email', methods=['POST'])
def verify_email():
    """Verify user's email address.
    
    Checks Firebase Auth directly (not the stale ID token) because the
    email_verified claim in an ID token is only set at token-issue time
    and won't reflect a verification that happened after the token was minted.
    """
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({"error": "ID token is required"}), 400
        
        try:
            # Decode token just to get the uid
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            
            # Check Firebase Auth directly (source of truth) instead of
            # the cached email_verified claim in the ID token
            firebase_user = auth.get_user(user_id)
            email_verified = firebase_user.email_verified
            
            if not email_verified:
                return jsonify({
                    "error": "Email not yet verified in Firebase",
                    "emailVerified": False,
                    "message": "Please click the verification link in your email first"
                }), 400
            
            # Sync verified status to MongoDB
            if mongo_db is not None:
                mongo_db.users.update_one(
                    {'uid': user_id},
                    {'$set': {'emailVerified': True, 'emailVerifiedAt': datetime.now()}}
                )
                logger.info(f"Email verified and synced for user {user_id}")
            
            return jsonify({
                "message": "Email verified successfully",
                "emailVerified": True
            }), 200
            
        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid ID token"}), 401
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return jsonify({"error": "Token verification failed"}), 401
        
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/check-verification-status', methods=['POST'])
@verify_email_optional
def check_verification_status():
    """Check user's email verification status.
    
    Always checks Firebase Auth directly and syncs to MongoDB,
    so the status is always up-to-date even if the user just verified.
    """
    try:
        user_id = g.user['uid']
        
        # Check Firebase Auth directly (source of truth)
        firebase_user = auth.get_user(user_id)
        email_verified = firebase_user.email_verified
        
        # If Firebase says verified but MongoDB doesn't, sync it
        mongo_verified = g.user.get('emailVerified', False)
        if email_verified and not mongo_verified and mongo_db is not None:
            mongo_db.users.update_one(
                {'uid': user_id},
                {'$set': {'emailVerified': True, 'emailVerifiedAt': datetime.now()}}
            )
            logger.info(f"Synced email verification status for user {user_id}")
        
        return jsonify({
            "emailVerified": email_verified,
            "message": "Email verified" if email_verified else "Email not verified"
        }), 200
        
    except Exception as e:
        logger.error(f"Check verification status error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Resume upload and parsing endpoint
@app.route('/api/resume/upload-and-parse', methods=['POST'])
@verify_token
def upload_and_parse_resume():
    """Upload and parse resume file"""
    try:
        # Get current user ID from the token
        user_id = g.user['uid']
        logger.info(f"Processing resume upload for user: {user_id}")
        
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
        upload_dir = os.environ.get('UPLOAD_DIR', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Save file
        filename = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        logger.info(f"File saved: {file_path}")
        
        # Process resume
        if resume_processor:
            result = resume_processor.process_resume(file_path, file.content_type)
            
            if result['success']:
                # Update user document in MongoDB
                # The user document is guaranteed to exist because the decorator creates it
                if mongo_db is not None:
                    user_ref = mongo_db.users.find_one({'uid': user_id})
                    if user_ref:
                        # Update existing document
                        user_ref['resumeData'] = result['parsedData']
                        user_ref['profileCompleted'] = False  # Don't auto-complete on upload, user needs to review
                        user_ref['lastResumeUpdate'] = datetime.now()
                        user_ref['resumeText'] = result['originalText']
                        mongo_db.users.replace_one({'uid': user_id}, user_ref)
                    else:
                        logger.error(f"User {user_id} not found in MongoDB after resume upload - this should not happen")
                        return jsonify({"error": "User profile not found"}), 500
                
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
        logger.error(f"Resume upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500



# Get user profile (uses verify_email_optional so unverified users can fetch their profile)
@app.route('/api/user/profile', methods=['GET'])
@verify_email_optional
def get_user_profile():
    """Get user profile data"""
    try:
        # User is guaranteed to exist in g.user by the decorator
        # The decorator creates a minimal profile if it doesn't exist
        user_doc = g.user
        
        # Ensure profileCompleted field is always present
        profile = mongo_doc_to_json(user_doc)
        if 'profileCompleted' not in profile:
            profile['profileCompleted'] = False
        
        return jsonify({
            "success": True,
            "profile": profile
        }), 200
            
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Update user profile (uses verify_email_optional so unverified users can complete their profile)
@app.route('/api/user/profile', methods=['PUT'])
@verify_email_optional
def update_user_profile():
    """Update user profile data"""
    try:
        user_id = g.user['uid']
        data = request.get_json() or {}
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid profile payload"}), 400

        if 'profilePicture' in data:
            try:
                data['profilePicture'] = sanitize_profile_picture_url(data.get('profilePicture'))
            except ValueError as validation_error:
                return jsonify({"error": str(validation_error)}), 400
        
        # Validate portfolioName uniqueness if being updated
        if 'portfolioName' in data and data['portfolioName']:
            portfolio_name = data['portfolioName'].strip()
            if portfolio_name:
                # Check if another user already has this portfolio name
                existing_user = mongo_db.users.find_one({
                    'portfolioName': portfolio_name,
                    'uid': {'$ne': user_id}  # Exclude current user
                })
                if existing_user:
                    return jsonify({
                        "error": f"Portfolio name '{portfolio_name}' is already taken. Please choose another."
                    }), 409  # 409 Conflict
        
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
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Public portfolio endpoint by user ID
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
                    'github', 'linkedin', 'resumeLink',
                    'experience', 'education', 'skills', 'certifications', 'projects',
                    'portfolioTheme', 'profilePicture'
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
        logger.error(f"Get public profile error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Public portfolio endpoint by portfolio name
@app.route('/api/portfolio/<portfolio_name>', methods=['GET'])
def get_portfolio_by_name(portfolio_name):
    """Get public/portfolio profile data by portfolio name (view-only, no auth required)"""
    try:
        if mongo_db is not None:
            user_doc = mongo_db.users.find_one({'portfolioName': portfolio_name})
            if user_doc:
                profile = mongo_doc_to_json(user_doc)
                # Only include public/important fields
                public_fields = [
                    'fullName', 'email', 'location', 'summary',
                    'github', 'linkedin', 'resumeLink',
                    'experience', 'education', 'skills', 'certifications', 'projects',
                    'portfolioTheme', 'profilePicture'
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
                return jsonify({"success": False, "error": "Portfolio not found"}), 404
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
    except Exception as e:
        logger.error(f"Get portfolio by name error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Check portfolio name availability
@app.route('/api/check-portfolio-name/<portfolio_name>', methods=['GET'])
def check_portfolio_name_availability(portfolio_name):
    """Check if a portfolio name is available (public endpoint, no auth required)"""
    try:
        if not portfolio_name or len(portfolio_name) < 3:
            return jsonify({
                "available": False,
                "error": "Portfolio name must be at least 3 characters"
            }), 200
        
        if mongo_db is not None:
            existing_user = mongo_db.users.find_one({'portfolioName': portfolio_name})
            return jsonify({
                "available": existing_user is None,
                "portfolioName": portfolio_name
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
    except Exception as e:
        logger.error(f"Check portfolio name error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Chat endpoints
@app.route('/api/chat/query', methods=['POST'])
@verify_token
def chat_query():
    """Process chat query with LangGraph chatbot agents"""
    try:
        user_id = g.user['uid']
        data = request.get_json()
        query = data.get('query', '')
        chat_history = data.get('chat_history', [])
        session_id = data.get('session_id')
        
        if not query.strip():
            return jsonify({"error": "Query is required"}), 400
        
        logger.info(f"Processing chat query for user {user_id} in session {session_id}: {query}")
        
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
        logger.info(f"Backend: Extracted chat_name: '{chat_name}' from result")
        logger.debug(f"Backend: Full result keys: {list(result.keys())}")
        if 'metadata' in result:
            logger.debug(f"Backend: Metadata keys: {list(result['metadata'].keys())}")
            if 'chat_name' in result['metadata']:
                logger.info(f"Backend: chat_name in metadata: '{result['metadata']['chat_name']}'")
        
        # Also check if chat_name is in metadata
        if 'metadata' in result and 'chat_name' in result['metadata']:
            metadata_chat_name = result['metadata']['chat_name']
            logger.info(f"Backend: Found chat_name in metadata: '{metadata_chat_name}'")
            if metadata_chat_name != 'New Chat':
                chat_name = metadata_chat_name
                logger.info(f"Backend: Using metadata chat_name: '{chat_name}'")
        
        logger.info(f"Backend: Final chat_name to be used: '{chat_name}'")
        
        # Save messages to session document if available and session_id provided
        if mongo_db is not None and result.get('response') and session_id:
            try:
                # Get the session document
                session_ref = mongo_db.chat_sessions.find_one({'_id': ObjectId(session_id)})
                
                if session_ref:
                    session_data = session_ref
                    messages = session_data.get('messages', [])
                    
                    # Add user message with context for fine-tuning
                    user_message = {
                        'id': f"user_{int(time.time() * 1000)}",
                        'role': 'user',
                        'content': query,
                        'timestamp': datetime.now().isoformat(),
                        'context': {
                            'chat_history': chat_history,  # Full context for fine-tuning
                            'session_id': session_id,
                            'user_id': user_id,
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    messages.append(user_message)
                    
                    # Add AI response with context and agent metadata
                    ai_message = {
                        'id': f"ai_{int(time.time() * 1000)}",
                        'role': 'assistant',
                        'content': result['response'],
                        'timestamp': datetime.now().isoformat(),
                        'sources': result.get('sources', {}),
                        'processing_time': result.get('processing_time', 0),
                        'context': {
                            'user_question': query,
                            'chat_history': chat_history,  # Full context for fine-tuning
                            'session_id': session_id,
                            'user_id': user_id,
                            'timestamp': datetime.now().isoformat()
                        },
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
                        logger.info(f"Backend: Updating chat title from 'New Chat' to: '{chat_name}'")
                        logger.debug(f"Backend: Session data before update: {session_data.get('title')}")
                        logger.info(f"Backend: New chat_name: '{chat_name}'")
                    else:
                        logger.info(f"Backend: Not updating title. Current: '{session_data.get('title')}', New: '{chat_name}'")
                    
                    mongo_db.chat_sessions.replace_one({'_id': ObjectId(session_id)}, update_data)
                    
                    logger.info(f"Chat messages saved to session {session_id} for user {user_id}")
                else:
                    logger.warning(f"Session {session_id} not found")
                    
            except Exception as e:
                logger.error(f"Error saving chat messages to session: {e}")
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
                    'session_id': session_id,
                    'context': {
                        'chat_history': chat_history,  # Full context for fine-tuning
                        'session_id': session_id,
                        'user_id': user_id,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                mongo_db.chat_history.insert_one(chat_doc)
            except Exception as e:
                logger.error(f"Error saving to legacy chat_history: {e}")
        
        # Prepare response
        response_data = {
            "success": True,
            "response": result['response'],
            "sources": result.get('sources', {}),
            "processing_time": result.get('processing_time', 0),
            "error": result.get('error', False),
            "chat_name": chat_name
        }
        
        logger.info(f"Backend: Sending response with chat_name: '{chat_name}'")
        logger.debug(f"Backend: Full response data: {response_data}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Chat query error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "I apologize, but I encountered an error processing your query."
        }), 500

@app.route('/api/chat/stream', methods=['POST'])
@verify_token
def chat_stream():
    """Stream chat response via Server-Sent Events.

    The generator emits three kinds of events:
      • {"type":"status","content":"…"}   – thinking / processing indicator
      • {"type":"token","content":"…"}    – a chunk of the answer text
      • {"type":"done", …metadata…}       – signals completion, carries sources/chat_name
    """
    try:
        user_id = g.user['uid']
        data = request.get_json()
        query = data.get('query', '')
        chat_history = data.get('chat_history', [])
        session_id = data.get('session_id')

        if not query.strip():
            return jsonify({"error": "Query is required"}), 400

        logger.info(f"Streaming chat response for user {user_id} session {session_id}: {query}")

        # We need to collect the full answer + metadata inside the generator
        # so we can persist the session after the stream finishes.
        _collected = {"answer": "", "meta": {}}

        def generate():
            try:
                for event in get_chatbot_integration().stream_query(
                    user_query=query,
                    user_id=user_id,
                    chat_history=chat_history,
                ):
                    yield f"data: {json.dumps(event)}\n\n"

                    # accumulate answer text
                    if event.get("type") == "token":
                        _collected["answer"] += event.get("content", "")
                    elif event.get("type") == "done":
                        _collected["meta"] = event

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        response = Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
            }
        )

        # --- After the response is sent, persist the session ----
        @response.call_on_close
        def _persist():
            full_answer = _collected["answer"].strip()
            meta = _collected["meta"]
            chat_name = meta.get("chat_name", "New Chat")

            if not full_answer or not session_id:
                return

            # Save to session document
            if mongo_db is not None:
                try:
                    # Find session by _id (ObjectId) and verify it belongs to the user
                    session_data = mongo_db.chat_sessions.find_one(
                        {"_id": ObjectId(session_id), "user_id": user_id}
                    )
                    if session_data:
                        messages = session_data.get("messages", [])
                        messages.append({
                            'id': f"user_{int(time.time() * 1000)}",
                            'role': 'user',
                            'content': query,
                            'timestamp': datetime.now().isoformat(),
                        })
                        messages.append({
                            'id': f"ai_{int(time.time() * 1000)}",
                            'role': 'assistant',
                            'content': full_answer,
                            'timestamp': datetime.now().isoformat(),
                            'sources': meta.get("sources", {}),
                        })
                        update = {
                            **session_data,
                            'messages': messages,
                            'last_updated': datetime.now(),
                            'message_count': len(messages),
                        }
                        if chat_name != "New Chat" and session_data.get("title") in (None, "New Chat"):
                            update["title"] = chat_name
                        mongo_db.chat_sessions.update_one(
                            {"_id": session_data["_id"]}, {"$set": update}
                        )
                except Exception as e:
                    logger.error(f"Stream: session persist error: {e}")

                # Legacy chat_history collection
                try:
                    mongo_db.chat_history.insert_one({
                        'user_id': user_id,
                        'query': query,
                        'response': full_answer,
                        'timestamp': datetime.now(),
                        'sources': meta.get("sources", {}),
                        'session_id': session_id,
                    })
                except Exception as e:
                    logger.error(f"Stream: legacy save error: {e}")

        return response

    except Exception as e:
        logger.error(f"Chat stream error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions', methods=['GET'])
@verify_token
def get_chat_sessions():
    """Get user's chat sessions"""
    try:
        user_id = g.user['uid']
        
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
            
            return jsonify(result), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Get chat sessions error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions', methods=['POST'])
@verify_token
def create_chat_session():
    """Create a new chat session"""
    try:
        user_id = g.user['uid']
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
            
            return jsonify({
                "success": True,
                "session_id": session_id,
                "message": "Chat session created successfully"
            }), 201
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Create chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['GET'])
@verify_token
def get_chat_session_messages(session_id):
    """Get messages for a specific chat session"""
    try:
        user_id = g.user['uid']
        
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
        logger.error(f"Get chat session messages error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['PUT'])
@verify_token
def update_chat_session(session_id):
    """Update chat session title"""
    try:
        user_id = g.user['uid']
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
            
            return jsonify({
                "success": True,
                "message": "Chat session updated successfully"
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Update chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['DELETE'])
@verify_token
def delete_chat_session(session_id):
    """Delete a chat session"""
    try:
        user_id = g.user['uid']
        
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
            
            return jsonify({
                "success": True,
                "message": "Chat session deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Delete chat session error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
@verify_token
def get_chat_history():
    """Get user's chat history (legacy endpoint)"""
    try:
        user_id = g.user['uid']
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
        logger.error(f"Get chat history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/rag/stats', methods=['GET'])
@verify_token
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
        logger.error(f"RAG stats error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chat/user-history', methods=['GET'])
@verify_token
def get_user_chat_history():
    """Get comprehensive chat history for a user"""
    try:
        user_id = g.user['uid']
        
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
        logger.error(f"Get user chat history error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/courses', methods=['GET'])
@verify_token
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
@verify_token
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
@verify_token
def get_faculty():
    """Fetches all documents from the faculty_new collection."""
    try:
        faculty_list = []
        # Fetch from faculty_new collection
        docs = mongo_db.faculty_new.find()
        for doc in docs:
            # Convert MongoDB document to JSON
            faculty_data = mongo_doc_to_json(doc)
            
            # Extract department from generalInformation or research if possible
            department = None
            general_info = faculty_data.get('generalInformation', '')
            research_info = faculty_data.get('research', '')
            
            # Try to extract department from general info or research
            if general_info:
                # Look for department patterns
                import re
                dept_patterns = [
                    r'Department of ([^,\n]*)',
                    r'School of ([^,\n]*)',
                    r'College of ([^,\n]*)',
                    r'([A-Z][a-z]+ Engineering)',
                    r'([A-Z][a-z]+ Science)',
                    r'([A-Z][a-z]+ Studies)'
                ]
                
                for pattern in dept_patterns:
                    match = re.search(pattern, general_info, re.IGNORECASE)
                    if match:
                        department = match.group(1).strip()
                        break
            
            # If no department found in general info, try research
            if not department and research_info:
                for pattern in dept_patterns:
                    match = re.search(pattern, research_info, re.IGNORECASE)
                    if match:
                        department = match.group(1).strip()
                        break
            
            # Create faculty object with new structure
            faculty_obj = {
                'id': faculty_data.get('_id', faculty_data.get('id', '')),
                'name': faculty_data.get('name', ''),
                'title': faculty_data.get('title', ''),
                'department': department,
                'generalInfo': faculty_data.get('generalInformation', ''),
                'researchInfo': faculty_data.get('research', ''),
                'education': faculty_data.get('education', []),
                'publications': faculty_data.get('publications', {}),
                'honorsAndAwards': faculty_data.get('honorsAndAwards', []),
                'grantsAndContracts': faculty_data.get('grantsAndContracts', []),
                'courses': faculty_data.get('courses', []),
                'experience': faculty_data.get('experience', []),
                'institutionalService': faculty_data.get('institutionalService', []),
                'professionalService': faculty_data.get('professionalService', []),
                'professionalSocieties': faculty_data.get('professionalSocieties', []),
                'appointments': faculty_data.get('appointments', []),
                'profileURL': faculty_data.get('profileURL', ''),
                'address': faculty_data.get('address', ''),
                'phone': faculty_data.get('phone', ''),
                'website': faculty_data.get('website', '')
            }
            
            faculty_list.append(faculty_obj)
        
        return jsonify({'success': True, 'faculty': faculty_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/faculty/<id>', methods=['GET'])
@verify_token
def get_single_faculty(id):
    """Fetches a single faculty member by their MongoDB document ID from faculty_new collection."""
    try:
        # Find the document in the 'faculty_new' collection by its ObjectId
        doc = mongo_db.faculty_new.find_one({'_id': ObjectId(id)})

        if doc:
            # Convert MongoDB document to JSON
            faculty_data = mongo_doc_to_json(doc)
            
            # Extract department from generalInformation or research if possible
            department = None
            general_info = faculty_data.get('generalInformation', '')
            research_info = faculty_data.get('research', '')
            
            # Try to extract department from general info or research
            if general_info:
                # Look for department patterns
                import re
                dept_patterns = [
                    r'Department of ([^,\n]*)',
                    r'School of ([^,\n]*)',
                    r'College of ([^,\n]*)',
                    r'([A-Z][a-z]+ Engineering)',
                    r'([A-Z][a-z]+ Science)',
                    r'([A-Z][a-z]+ Studies)'
                ]
                
                for pattern in dept_patterns:
                    match = re.search(pattern, general_info, re.IGNORECASE)
                    if match:
                        department = match.group(1).strip()
                        break
            
            # If no department found in general info, try research
            if not department and research_info:
                for pattern in dept_patterns:
                    match = re.search(pattern, research_info, re.IGNORECASE)
                    if match:
                        department = match.group(1).strip()
                        break
            
            # Create faculty object with new structure
            faculty_obj = {
                'id': faculty_data.get('_id', faculty_data.get('id', '')),
                'name': faculty_data.get('name', ''),
                'title': faculty_data.get('title', ''),
                'department': department,
                'generalInfo': faculty_data.get('generalInformation', ''),
                'researchInfo': faculty_data.get('research', ''),
                'education': faculty_data.get('education', []),
                'publications': faculty_data.get('publications', {}),
                'honorsAndAwards': faculty_data.get('honorsAndAwards', []),
                'grantsAndContracts': faculty_data.get('grantsAndContracts', []),
                'courses': faculty_data.get('courses', []),
                'experience': faculty_data.get('experience', []),
                'institutionalService': faculty_data.get('institutionalService', []),
                'professionalService': faculty_data.get('professionalService', []),
                'professionalSocieties': faculty_data.get('professionalSocieties', []),
                'appointments': faculty_data.get('appointments', []),
                'profileURL': faculty_data.get('profileURL', ''),
                'address': faculty_data.get('address', ''),
                'phone': faculty_data.get('phone', ''),
                'website': faculty_data.get('website', '')
            }
            
            return jsonify({'success': True, 'professor': faculty_obj})
        else:
            return jsonify({'success': False, 'error': 'Faculty not found'}), 404
    except Exception as e:
        # This will catch errors, including an invalid ID format
        return jsonify({'success': False, 'error': str(e)}), 500

# --- Course Reviews Endpoints ---
@app.route('/api/courses/<course_id>/reviews', methods=['GET'])
@verify_token
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
@verify_token
def add_course_review(course_id):
    try:
        user_id = g.user['uid']
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
@verify_token
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
@verify_token
def add_professor_review(faculty_id):
    """Adds a new review for a specific professor."""
    try:
        user_id = g.user['uid']
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
@verify_token
def get_all_course_reviews():
    """Fetches all course reviews from the database."""
    try:
        docs = mongo_db.course_reviews.find()
        reviews = [mongo_doc_to_json(doc) for doc in docs]
        return jsonify({'success': True, 'reviews': reviews}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reviews/professors', methods=['GET'])
@verify_token
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
    @verify_token
    def wrapper(*args, **kwargs):
        user_id = g.user['uid']
        if mongo_db is None:
            return jsonify({"error": "Database not available"}), 500
        user_doc = mongo_db.users.find_one({'uid': user_id})
        if not user_doc or user_doc.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

@app.route('/api/admin/collections', methods=['GET'])
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
            logger.info(f"Course {course_id} synced to Chroma")
        else:
            logger.warning(f"Chroma collection 'AllCourseRelatedData' not available")
    except Exception as e:
        logger.error(f"Error syncing course {course_id} to Chroma: {e}")

def delete_from_chroma(course_id):
    """Delete course data from Chroma vector database"""
    try:
        collection = get_chatbot_integration().load_vector_store('AllCourseRelatedData')
        if collection:
            collection.delete(ids=[course_id])
            logger.info(f"Course {course_id} deleted from Chroma")
        else:
            logger.warning(f"Chroma collection 'AllCourseRelatedData' not available")
    except Exception as e:
        logger.error(f"Error deleting course {course_id} from Chroma: {e}")

@app.route('/api/admin/courses', methods=['GET'])
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
@verify_token
def fix_profile_completion():
    """Fix profile completion status for users who have profile data but missing the flag"""
    try:
        user_id = g.user['uid']
        
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
        logger.error(f"Fix profile completion error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/feedback', methods=['POST'])
@verify_token
def submit_feedback():
    """Submit feedback for a chat message"""
    try:
        user_id = g.user['uid']
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
                logger.info(f"Feedback saved for message {message_id}: {feedback}")
            except Exception as e:
                logger.warning(f"Could not update message in chat_sessions: {e}")
        
        return jsonify({
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback": feedback
        }), 200
        
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Job and Internship Search API Endpoints
import csv
import math
from typing import List, Dict, Any

def read_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """Read CSV file and return list of dictionaries"""
    try:
        data = []
        # Use utf-8-sig to handle BOM (Byte Order Mark) properly
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Clean up any remaining BOM characters in keys or values
                clean_row = {}
                for key, value in row.items():
                    # Remove BOM character if present in keys
                    clean_key = key.replace('\ufeff', '') if key else key
                    # Remove BOM character if present in values
                    clean_value = value.replace('\ufeff', '') if isinstance(value, str) else value
                    clean_row[clean_key] = clean_value
                data.append(clean_row)
        logger.info(f"Successfully read {len(data)} rows from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {str(e)}")
        return []

def filter_jobs(jobs: List[Dict], filters: Dict) -> List[Dict]:
    """Apply filters to job listings"""
    filtered_jobs = jobs
    
    # Search filter (searches in title, company, location, qualifications)
    search_term = filters.get('search', '').lower()
    if search_term:
        filtered_jobs = [
            job for job in filtered_jobs
            if (search_term in job.get('Position Title', '').lower() or
                search_term in job.get('Company', '').lower() or
                search_term in job.get('Location', '').lower() or
                search_term in job.get('Qualifications', '').lower())
        ]
    
    # Work model filter
    work_model = filters.get('workModel')
    if work_model and work_model != 'all':
        filtered_jobs = [
            job for job in filtered_jobs
            if job.get('Work Model', '').lower() == work_model.lower()
        ]
    
    # Location filter
    location = filters.get('location', '').lower()
    if location:
        filtered_jobs = [
            job for job in filtered_jobs
            if location in job.get('Location', '').lower()
        ]
    
    # Company size filter
    company_size = filters.get('companySize')
    if company_size and company_size != 'all':
        filtered_jobs = [
            job for job in filtered_jobs
            if job.get('Company Size', '') == company_size
        ]
    
    # H1B sponsorship filter
    h1b_sponsored = filters.get('h1bSponsored')
    if h1b_sponsored and h1b_sponsored != 'all':
        filtered_jobs = [
            job for job in filtered_jobs
            if job.get('H1b Sponsored', '').lower() == h1b_sponsored.lower()
        ]
    
    # Industry filter
    industry = filters.get('industry', '').lower()
    if industry:
        filtered_jobs = [
            job for job in filtered_jobs
            if industry in job.get('Company Industry', '').lower()
        ]
    
    return filtered_jobs

def paginate_results(data: List[Dict], page: int, per_page: int) -> Dict:
    """Paginate results and return with metadata"""
    total_items = len(data)
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return {
        'data': data[start_idx:end_idx],
        'pagination': {
            'current_page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

def verify_token_with_options(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            # Handle preflight request
            return '', 200
        
        # Apply token verification for other methods
        id_token = None
        if 'Authorization' in request.headers and request.headers['Authorization'].startswith('Bearer '):
            id_token = request.headers['Authorization'].split('Bearer ')[1]

        if not id_token:
            return jsonify({"error": "Authorization token is missing"}), 401

        try:
            decoded_token = auth.verify_id_token(id_token)
            g.user = decoded_token
        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": f"Token verification failed: {e}"}), 401

        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/jobs', methods=['GET', 'OPTIONS'])
@verify_token_with_options
def get_jobs():
    """Get job listings with filtering and pagination"""
    try:
        # Read jobs CSV
        jobs_csv_path = os.environ.get('JOBS_CSV_PATH', 'jobs.csv')
        jobs_data = read_csv_data(jobs_csv_path)
        if not jobs_data:
            return jsonify({'success': False, 'error': 'Unable to load jobs data'}), 500
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get filters
        filters = {
            'search': request.args.get('search', ''),
            'workModel': request.args.get('workModel', 'all'),
            'location': request.args.get('location', ''),
            'companySize': request.args.get('companySize', 'all'),
            'h1bSponsored': request.args.get('h1bSponsored', 'all'),
            'industry': request.args.get('industry', '')
        }
        
        # Apply filters
        filtered_jobs = filter_jobs(jobs_data, filters)
        
        # Paginate results
        result = paginate_results(filtered_jobs, page, per_page)
        
        return jsonify({
            'success': True,
            'jobs': result['data'],
            'pagination': result['pagination'],
            'total_filtered': len(filtered_jobs),
            'total_jobs': len(jobs_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/internships', methods=['GET', 'OPTIONS'])
@verify_token_with_options
def get_internships():
    """Get internship listings with filtering and pagination"""
    try:
        # Read internships CSV
        internships_csv_path = os.environ.get('INTERNSHIPS_CSV_PATH', 'internships.csv')
        internships_data = read_csv_data(internships_csv_path)
        if not internships_data:
            return jsonify({'success': False, 'error': 'Unable to load internships data'}), 500
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get filters (adjusted for internship-specific fields)
        filters = {
            'search': request.args.get('search', ''),
            'workModel': request.args.get('workModel', 'all'),
            'location': request.args.get('location', ''),
            'companySize': request.args.get('companySize', 'all'),
            'industry': request.args.get('industry', ''),
            'hireTime': request.args.get('hireTime', '')
        }
        
        # Apply filters (using similar logic but for internship fields)
        filtered_internships = filter_internships(internships_data, filters)
        
        # Paginate results
        result = paginate_results(filtered_internships, page, per_page)
        
        return jsonify({
            'success': True,
            'internships': result['data'],
            'pagination': result['pagination'],
            'total_filtered': len(filtered_internships),
            'total_internships': len(internships_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching internships: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def filter_internships(internships: List[Dict], filters: Dict) -> List[Dict]:
    """Apply filters to internship listings"""
    filtered_internships = internships
    
    # Search filter
    search_term = filters.get('search', '').lower()
    if search_term:
        filtered_internships = [
            internship for internship in filtered_internships
            if (search_term in internship.get('Position Title', '').lower() or
                search_term in internship.get('Company', '').lower() or
                search_term in internship.get('Location', '').lower() or
                search_term in internship.get('Qualifications', '').lower())
        ]
    
    # Work model filter
    work_model = filters.get('workModel')
    if work_model and work_model != 'all':
        filtered_internships = [
            internship for internship in filtered_internships
            if internship.get('Work Model', '').lower() == work_model.lower()
        ]
    
    # Location filter
    location = filters.get('location', '').lower()
    if location:
        filtered_internships = [
            internship for internship in filtered_internships
            if location in internship.get('Location', '').lower()
        ]
    
    # Company size filter
    company_size = filters.get('companySize')
    if company_size and company_size != 'all':
        filtered_internships = [
            internship for internship in filtered_internships
            if internship.get('Company Size', '') == company_size
        ]
    
    # Industry filter
    industry = filters.get('industry', '').lower()
    if industry:
        filtered_internships = [
            internship for internship in filtered_internships
            if industry in internship.get('Company Industry', '').lower()
        ]
    
    # Hire time filter (specific to internships)
    hire_time = filters.get('hireTime', '').lower()
    if hire_time:
        filtered_internships = [
            internship for internship in filtered_internships
            if hire_time in internship.get('Hire Time', '').lower()
        ]
    
    return filtered_internships

@app.route('/api/jobs/stats', methods=['GET', 'OPTIONS'])
@verify_token_with_options
def get_job_stats():
    """Get job statistics for filters"""
    try:
        jobs_csv_path = os.environ.get('JOBS_CSV_PATH', 'jobs.csv')
        jobs_data = read_csv_data(jobs_csv_path)
        if not jobs_data:
            return jsonify({'success': False, 'error': 'Unable to load jobs data'}), 500
        
        # Calculate statistics
        work_models = {}
        company_sizes = {}
        industries = {}
        h1b_stats = {}
        
        for job in jobs_data:
            # Work model stats
            work_model = job.get('Work Model', 'Unknown')
            work_models[work_model] = work_models.get(work_model, 0) + 1
            
            # Company size stats
            company_size = job.get('Company Size', 'Unknown')
            company_sizes[company_size] = company_sizes.get(company_size, 0) + 1
            
            # Industry stats
            industry = job.get('Company Industry', 'Unknown')
            industries[industry] = industries.get(industry, 0) + 1
            
            # H1B stats
            h1b = job.get('H1b Sponsored', 'Unknown')
            h1b_stats[h1b] = h1b_stats.get(h1b, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_jobs': len(jobs_data),
                'work_models': work_models,
                'company_sizes': company_sizes,
                'industries': industries,
                'h1b_sponsorship': h1b_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching job stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/internships/stats', methods=['GET', 'OPTIONS'])
@verify_token_with_options
def get_internship_stats():
    """Get internship statistics for filters"""
    try:
        internships_csv_path = os.environ.get('INTERNSHIPS_CSV_PATH', 'internships.csv')
        internships_data = read_csv_data(internships_csv_path)
        if not internships_data:
            return jsonify({'success': False, 'error': 'Unable to load internships data'}), 500
        
        # Calculate statistics
        work_models = {}
        company_sizes = {}
        industries = {}
        hire_times = {}
        
        for internship in internships_data:
            # Work model stats
            work_model = internship.get('Work Model', 'Unknown')
            work_models[work_model] = work_models.get(work_model, 0) + 1
            
            # Company size stats
            company_size = internship.get('Company Size', 'Unknown')
            company_sizes[company_size] = company_sizes.get(company_size, 0) + 1
            
            # Industry stats
            industry = internship.get('Company Industry', 'Unknown')
            industries[industry] = industries.get(industry, 0) + 1
            
            # Hire time stats
            hire_time = internship.get('Hire Time', 'Unknown')
            hire_times[hire_time] = hire_times.get(hire_time, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_internships': len(internships_data),
                'work_models': work_models,
                'company_sizes': company_sizes,
                'industries': industries,
                'hire_times': hire_times
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching internship stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Test endpoint to verify CORS is working
@app.route('/api/test-cors', methods=['GET', 'OPTIONS'])
def test_cors():
    """Test endpoint to verify CORS configuration"""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'success': True,
        'message': 'CORS is working correctly!',
        'origin': request.headers.get('Origin', 'No origin header'),
        'method': request.method
    })

# ── Scraper endpoints ──
@app.route('/api/scraper/status', methods=['GET'])
def scraper_status():
    """Check the background job scraper's health (no auth required)."""
    return jsonify({
        "success": True,
        "scraper": _scraper_status,
    })

@app.route('/api/admin/scraper/run', methods=['POST'])
@verify_token
def admin_trigger_scraper():
    """Manually trigger a job scraper run (admin only)."""
    try:
        user_id = g.user['uid']
        if mongo_db is not None:
            user_doc = mongo_db.users.find_one({'uid': user_id})
            if not user_doc or user_doc.get('role') != 'admin':
                return jsonify({"success": False, "error": "Admin access required"}), 403
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500

        # Run the scraper in a one-shot background thread so the request returns immediately
        def _one_shot_scrape():
            try:
                from github_jobs_unified_scraper import UnifiedGitHubScraper
                scraper = UnifiedGitHubScraper()
                scraper.scrape_all_repositories()
                _scraper_status["runs"] += 1
                _scraper_status["last_run"] = datetime.utcnow().isoformat() + "Z"
                _scraper_status["last_status"] = "success (manual)"
                _scraper_status["last_error"] = None
                logger.info("Scraper: manual run triggered by admin %s completed ✓", user_id)
            except Exception as exc:
                _scraper_status["last_status"] = "error (manual)"
                _scraper_status["last_error"] = str(exc)
                logger.error("Scraper: manual run failed — %s", exc)

        t = threading.Thread(target=_one_shot_scrape, daemon=True)
        t.start()

        logger.info("Admin %s triggered manual scraper run", user_id)
        return jsonify({
            "success": True,
            "message": "Scraper started. Check /api/scraper/status for progress.",
        })

    except Exception as e:
        logger.error(f"Admin trigger scraper error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# User Management Admin API Endpoints
@app.route('/api/admin/users', methods=['GET'])
@verify_token
def get_all_users():
    """Get all users for admin management"""
    try:
        user_id = g.user['uid']
        
        # Check if current user is admin
        if mongo_db is not None:
            user_doc = mongo_db.users.find_one({'uid': user_id})
            if not user_doc or user_doc.get('role') != 'admin':
                return jsonify({"success": False, "error": "Admin access required"}), 403
            
            # Get all users with sensitive information filtered out
            users = list(mongo_db.users.find({}, {
                'uid': 1,
                'email': 1,
                'fullName': 1,
                'role': 1,
                'profileCompleted': 1,
                'createdAt': 1,
                'updatedAt': 1,
                'lastLoginAt': 1
            }))
            
            # Convert ObjectId to string for JSON serialization
            for user in users:
                if '_id' in user:
                    user['_id'] = str(user['_id'])
            
            return jsonify({
                "success": True,
                "users": users
            }), 200
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Get all users error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/users/<user_uid>', methods=['GET'])
@verify_token
def get_user_details(user_uid):
    """Get detailed user information for admin management"""
    try:
        admin_id = g.user['uid']
        
        # Check if current user is admin
        if mongo_db is not None:
            admin_doc = mongo_db.users.find_one({'uid': admin_id})
            if not admin_doc or admin_doc.get('role') != 'admin':
                return jsonify({"success": False, "error": "Admin access required"}), 403
            
            # Get user details
            user_doc = mongo_db.users.find_one({'uid': user_uid})
            if not user_doc:
                return jsonify({"success": False, "error": "User not found"}), 404
            
            # Convert ObjectId to string for JSON serialization
            if '_id' in user_doc:
                user_doc['_id'] = str(user_doc['_id'])
            
            return jsonify({
                "success": True,
                "user": user_doc
            }), 200
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Get user details error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/users/<user_uid>', methods=['PUT'])
@verify_token
def update_user_admin(user_uid):
    """Update user information (admin only)"""
    try:
        admin_id = g.user['uid']
        data = request.get_json()
        
        # Check if current user is admin
        if mongo_db is not None:
            admin_doc = mongo_db.users.find_one({'uid': admin_id})
            if not admin_doc or admin_doc.get('role') != 'admin':
                return jsonify({"success": False, "error": "Admin access required"}), 403
            
            # Get user to update
            user_doc = mongo_db.users.find_one({'uid': user_uid})
            if not user_doc:
                return jsonify({"success": False, "error": "User not found"}), 404
            
            # Update allowed fields
            allowed_fields = ['fullName', 'email', 'role', 'profileCompleted']
            update_data = {}
            
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            if update_data:
                update_data['updatedAt'] = datetime.now()
                
                # Update user document in MongoDB
                mongo_db.users.update_one(
                    {'uid': user_uid},
                    {'$set': update_data}
                )
                
                # If role is being updated, sync with Firebase custom claims
                if 'role' in update_data:
                    try:
                        new_role = update_data['role']
                        custom_claims = {
                            'role': new_role,
                            'admin': new_role == 'admin'
                        }
                        auth.set_custom_user_claims(user_uid, custom_claims)
                        logger.info(f"Firebase custom claims updated for user {user_uid}: {custom_claims}")
                    except Exception as firebase_error:
                        logger.error(f"Firebase custom claims update failed: {firebase_error}")
                        # Continue with MongoDB update even if Firebase fails
                
                return jsonify({
                    "success": True,
                    "message": "User updated successfully",
                    "firebase_synced": 'role' in update_data
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "No valid fields to update"
                }), 400
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Update user admin error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/users/<user_uid>', methods=['DELETE'])
@verify_token
def delete_user_admin(user_uid):
    """Delete user (admin only)"""
    try:
        admin_id = g.user['uid']
        
        # Check if current user is admin
        if mongo_db is not None:
            admin_doc = mongo_db.users.find_one({'uid': admin_id})
            if not admin_doc or admin_doc.get('role') != 'admin':
                return jsonify({"success": False, "error": "Admin access required"}), 403
            
            # Prevent admin from deleting themselves
            if admin_id == user_uid:
                return jsonify({
                    "success": False,
                    "error": "Cannot delete your own account"
                }), 400
            
            # Get user to delete
            user_doc = mongo_db.users.find_one({'uid': user_uid})
            if not user_doc:
                return jsonify({"success": False, "error": "User not found"}), 404
            
            # Prevent deletion of other admin users
            if user_doc.get('role') == 'admin':
                return jsonify({
                    "success": False,
                    "error": "Cannot delete other admin users"
                }), 400
            
            # Delete user and related data
            mongo_db.users.delete_one({'uid': user_uid})
            
            # Clean up related data (optional - you can add more cleanup here)
            mongo_db.chat_sessions.delete_many({'user_id': user_uid})
            mongo_db.chat_history.delete_many({'user_id': user_uid})
            mongo_db.message_feedback.delete_many({'user_id': user_uid})
            mongo_db.course_reviews.delete_many({'user_id': user_uid})
            mongo_db.professor_reviews.delete_many({'user_id': user_uid})
            
            return jsonify({
                "success": True,
                "message": "User deleted successfully"
            }), 200
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Delete user admin error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/users/<user_uid>/role', methods=['PUT'])
@verify_token
def update_user_role(user_uid):
    """Update user role (admin only)"""
    try:
        admin_id = g.user['uid']
        data = request.get_json()
        new_role = data.get('role')
        
        if not new_role or new_role not in ['user', 'admin']:
            return jsonify({
                "success": False,
                "error": "Role must be 'user' or 'admin'"
            }), 400
        
        # Check if current user is admin
        if mongo_db is not None:
            admin_doc = mongo_db.users.find_one({'uid': admin_id})
            if not admin_doc or admin_doc.get('role') != 'admin':
                return jsonify({"success": False, "error": "Admin access required"}), 403
            
            # Get user to update
            user_doc = mongo_db.users.find_one({'uid': user_uid})
            if not user_doc:
                return jsonify({"success": False, "error": "User not found"}), 404
            
            # Update user role in MongoDB
            mongo_db.users.update_one(
                {'uid': user_uid},
                {
                    '$set': {
                        'role': new_role,
                        'updatedAt': datetime.now()
                    }
                }
            )
            
            # Update Firebase custom claims for role-based access control
            try:
                # Set custom claims in Firebase
                custom_claims = {
                    'role': new_role,
                    'admin': new_role == 'admin'
                }
                auth.set_custom_user_claims(user_uid, custom_claims)
                logger.info(f"Firebase custom claims updated for user {user_uid}: {custom_claims}")
            except Exception as firebase_error:
                logger.error(f"Firebase custom claims update failed: {firebase_error}")
                # Continue with MongoDB update even if Firebase fails
                # But log the error for investigation
            
            return jsonify({
                "success": True,
                "message": f"User role updated to {new_role} successfully",
                "firebase_synced": True
            }), 200
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Update user role error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/sync-firebase-claims', methods=['POST'])
@verify_token
def sync_firebase_claims():
    """Sync all users' Firebase custom claims with MongoDB roles (admin only)"""
    try:
        admin_id = g.user['uid']
        
        # Check if current user is admin
        if mongo_db is not None:
            admin_doc = mongo_db.users.find_one({'uid': admin_id})
            if not admin_doc or admin_doc.get('role') != 'admin':
                return jsonify({"success": False, "error": "Admin access required"}), 403
            
            # Get all users from MongoDB
            users = list(mongo_db.users.find({}))
            synced_count = 0
            failed_count = 0
            errors = []
            
            for user in users:
                try:
                    user_uid = user.get('uid')
                    mongo_role = user.get('role', 'user')
                    
                    if user_uid:
                        # Get current Firebase custom claims
                        firebase_user = auth.get_user(user_uid)
                        current_claims = firebase_user.custom_claims or {}
                        
                        # Check if claims need updating
                        if current_claims.get('role') != mongo_role:
                            custom_claims = {
                                'role': mongo_role,
                                'admin': mongo_role == 'admin'
                            }
                            auth.set_custom_user_claims(user_uid, custom_claims)
                            synced_count += 1
                            logger.info(f"Synced Firebase claims for user {user_uid}: {custom_claims}")
                        else:
                            logger.info(f"ℹFirebase claims already in sync for user {user_uid}")
                            
                except Exception as user_error:
                    failed_count += 1
                    error_msg = f"Failed to sync user {user.get('uid', 'unknown')}: {str(user_error)}"
                    errors.append(error_msg)
                    logger.error(f"{error_msg}")
            
            return jsonify({
                "success": True,
                "message": f"Firebase claims sync completed",
                "total_users": len(users),
                "synced_count": synced_count,
                "failed_count": failed_count,
                "errors": errors
            }), 200
        else:
            return jsonify({"success": False, "error": "Database not available"}), 500
            
    except Exception as e:
        logger.error(f"Sync Firebase claims error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # This block only runs for local development (python app.py).
    # In production, gunicorn imports the `app` object directly.
    port = int(os.environ.get('PORT', 5003))
    host = os.environ.get('APP_HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV', 'development') != 'production'

    logger.info("Starting AdvisorAI backend on %s:%s", host, port)
    logger.info("Environment: %s | Debug: %s", os.environ.get('FLASK_ENV', 'development'), debug)
    app.run(debug=debug, host=host, port=port)
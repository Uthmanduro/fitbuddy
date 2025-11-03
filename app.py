# from flask import Flask, request, jsonify
# from dotenv import load_dotenv
# from agent import ExerciseAgent
# import os

# # Load environment variables
# load_dotenv()

# app = Flask(__name__)

# # Initialize the exercise agent
# try:
#     agent = ExerciseAgent()
#     print("Exercise Agent initialized successfully")
# except Exception as e:
#     print(f"Failed to initialize agent: {e}")
#     agent = None

# @app.route('/')
# def home():
#     """Health check endpoint"""
#     return jsonify({
#         "status": "running",
#         "agent": "Exercise Recommendation Agent",
#         "version": "1.0.0",
#         "endpoints": {
#             "a2a": "/a2a/agent/exerciseAgent",
#             "health": "/health"
#         }
#     })

# @app.route('/health')
# def health():
#     """Detailed health check"""
#     agent_status = "healthy" if agent else "not initialized"
#     return jsonify({
#         "status": "ok",
#         "agent_status": agent_status,
#         "gemini_configured": bool(os.getenv('GEMINI_API_KEY'))
#     })

# @app.route('/a2a/agent/exerciseAgent', methods=['POST'])
# def exercise_agent_endpoint():
#     """
#     A2A Protocol endpoint for Telex.im integration
#     """
    
#     if not agent:
#         return jsonify({
#             "status": "error",
#             "error": "Agent not initialized. Check GEMINI_API_KEY configuration."
#         }), 500
    
#     try:
#         # Parse incoming request
#         data = request.get_json()
        
#         if not data:
#             return jsonify({
#                 "status": "error",
#                 "error": "No JSON data provided"
#             }), 400
        
#         print(f"Received data: {data}")  # Debug log
        
#         # Extract user message from Telex A2A format
#         user_message = extract_user_message(data)
        
#         if not user_message:
#             return jsonify({
#                 "status": "error",
#                 "response": "Please provide a body part to exercise"
#             }), 400
        
#         # Get metadata
#         metadata = data.get('message', {}).get('metadata', {})
#         user_id = metadata.get('telex_user_id', 'anonymous')
        
#         # Log the request
#         print(f"Received request from {user_id}: {user_message}")
        
#         # Validate input
#         is_valid, error_msg = agent.validate_input(user_message)
#         if not is_valid:
#             return jsonify({
#                 "status": "error",
#                 "response": error_msg
#             }), 400
        
#         # Generate response
#         result = agent.generate_response(user_message, context=None)
        
#         # Return response in A2A format
#         if result['success']:
#             return jsonify({
#                 "status": "success",
#                 "response": result['response'],
#                 "metadata": {
#                     "body_part": result['body_part'],
#                     "timestamp": result['timestamp']
#                 }
#             }), 200
#         else:
#             return jsonify({
#                 "status": "error",
#                 "response": result['response'],
#                 "error": result.get('error', 'Unknown error')
#             }), 500
            
#     except Exception as e:
#         print(f"Error processing request: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             "status": "error",
#             "response": "Sorry, I encountered an error processing your request. Please try again.",
#             "error": str(e)
#         }), 500


# def extract_user_message(data):
#     """
#     Extract the user's message from Telex A2A protocol format
    
#     Telex sends messages in this structure:
#     {
#         "message": {
#             "parts": [
#                 {
#                     "kind": "text",
#                     "text": "user message"
#                 }
#                 OR
#                 {
#                     "kind": "data",
#                     "data": [
#                         {"kind": "text", "text": "message1"},
#                         {"kind": "text", "text": "message2"}
#                     ]
#                 }
#             ]
#         }
#     }
#     """
#     try:
#         # Navigate through the nested structure
#         message = data.get('message', {})
#         parts = message.get('parts', [])
        
#         if not parts:
#             return None
        
#         # Get the last part (most recent message)
#         last_part = parts[-1]
        
#         # Check if it's a simple text part
#         if last_part.get('kind') == 'text':
#             return last_part.get('text', '').strip()
        
#         # Check if it's a data part with nested messages
#         if last_part.get('kind') == 'data':
#             data_items = last_part.get('data', [])
#             if data_items:
#                 # Get the last message in the data array
#                 last_message = data_items[-1]
#                 if last_message.get('kind') == 'text':
#                     text = last_message.get('text', '').strip()
#                     # Remove HTML tags if present
#                     import re
#                     text = re.sub(r'<[^>]+>', '', text)
#                     return text
        
#         return None
        
#     except Exception as e:
#         print(f"Error extracting message: {e}")
#         return None

# @app.errorhandler(404)
# def not_found(e):
#     return jsonify({
#         "status": "error",
#         "error": "Endpoint not found"
#     }), 404

# @app.errorhandler(500)
# def internal_error(e):
#     return jsonify({
#         "status": "error",
#         "error": "Internal server error"
#     }), 500

# if __name__ == '__main__':
#     port = int(os.getenv('PORT', 5000))
#     debug = os.getenv('FLASK_ENV') == 'development'
    
#     print(f"Starting Exercise Agent on port {port}...")
#     app.run(host='0.0.0.0', port=port, debug=debug)

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from agent import ExerciseAgent
import os
import re
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize the exercise agent
try:
    agent = ExerciseAgent()
    print("✓ Exercise Agent initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize agent: {e}")
    agent = None


def extract_user_message(params):
    """
    Extract the user's message from A2A protocol params
    
    Args:
        params: The params object from JSON-RPC request
        
    Returns:
        str: The extracted user message or None
    """
    try:
        message = params.get('message', {})
        parts = message.get('parts', [])
        
        if not parts:
            return None
        
        # Iterate through parts to find text
        for part in reversed(parts):
            part_type = part.get('type') or part.get('kind')
            
            if part_type == 'text':
                text = part.get('text', '').strip()
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', '', text)
                if text:
                    return text
            
            # Handle nested data structures (if Telex sends them)
            if part_type == 'data':
                data_items = part.get('data', [])
                for item in reversed(data_items):
                    item_type = item.get('type') or item.get('kind')
                    if item_type == 'text':
                        text = item.get('text', '').strip()
                        text = re.sub(r'<[^>]+>', '', text)
                        if text:
                            return text
        
        return None
        
    except Exception as e:
        print(f"Error extracting message: {e}")
        return None


def create_success_response(request_id, text, message_id=None):
    """
    Create a JSON-RPC 2.0 success response following A2A protocol
    
    Args:
        request_id: The ID from the request
        text: The response text
        message_id: Optional message ID
        
    Returns:
        dict: JSON-RPC success response
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "role": "agent",
            "parts": [
                {
                    "type": "text",
                    "text": text
                }
            ],
            "kind": "message",
            "message_id": message_id or str(uuid.uuid4())
        }
    }


def create_error_response(request_id, code, message):
    """
    Create a JSON-RPC 2.0 error response
    
    Args:
        request_id: The ID from the request
        code: Error code (standard JSON-RPC codes)
        message: Error message
        
    Returns:
        dict: JSON-RPC error response
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    }


# ============================================================================
# A2A PROTOCOL ENDPOINTS
# ============================================================================

@app.route('/.well-known/agent.json', methods=['GET'])
def agent_card():
    """
    Well-known endpoint that returns the agent card
    This tells Telex about your agent's capabilities
    """
    base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
    
    return jsonify({
        "name": "Exercise Recommender",
        "description": "AI fitness coach that provides personalized exercise recommendations for specific body parts",
        "version": "1.0.0",
        "url": base_url,
        "capabilities": {
            "streaming": False,
            "push_notifications": False
        },
        "methods": [
            "message/send"
        ],
        "metadata": {
            "author": "Your Name",
            "category": "health",
            "tags": ["fitness", "exercise", "health", "workout"]
        }
    })


@app.route('/a2a/agent/exerciseAgent', methods=['POST'])
async def handle_rpc_request():
    """
    Main A2A endpoint - handles all JSON-RPC requests
    Routes to appropriate handler based on method
    """
    
    if not agent:
        return jsonify(create_error_response(
            None,
            -32603,
            "Agent not initialized. Check GEMINI_API_KEY configuration."
        )), 500
    
    try:
        # Parse JSON-RPC request
        body = request.get_json()
        
        if not body:
            return jsonify(create_error_response(
                None,
                -32700,
                "Parse error - Invalid JSON"
            )), 400
        
        # Validate JSON-RPC 2.0 format
        if body.get('jsonrpc') != '2.0':
            return jsonify(create_error_response(
                body.get('id'),
                -32600,
                "Invalid Request - must be JSON-RPC 2.0"
            )), 400
        
        request_id = body.get('id')
        method = body.get('method')
        params = body.get('params', {})
        
        print("=" * 60)
        print(f"📥 Received JSON-RPC request")
        print(f"Method: {method}")
        print(f"Request ID: {request_id}")
        print("=" * 60)
        
        # Route to appropriate handler based on method
        if method == "message/send":
            result = handle_message_send(request_id, params)
            return jsonify(result), 200
        
        elif method == "task/subscribe":
            # If you want to support task subscriptions in the future
            result = handle_task_subscription(request_id, params)
            return jsonify(result), 200
        
        else:
            # Method not found
            print(f"❌ Unknown method: {method}")
            return jsonify(create_error_response(
                request_id,
                -32601,
                f"Method not found: {method}"
            )), 404
            
    except Exception as e:
        print(f"❌ Error processing RPC request: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify(create_error_response(
            body.get('id') if body else None,
            -32603,
            f"Internal error: {str(e)}"
        )), 500


def handle_message_send(request_id, params):
    """
    Handle the message/send method
    
    Args:
        request_id: The JSON-RPC request ID
        params: The params object containing the message
        
    Returns:
        dict: JSON-RPC response
    """
    try:
        # Extract user message
        user_message = extract_user_message(params)
        
        print(f"💬 User message: {user_message}")
        
        if not user_message:
            return create_error_response(
                request_id,
                -32602,
                "Invalid params - no message text found. Please provide a body part (e.g., 'arms', 'legs', 'chest')"
            )
        
        # Validate input
        is_valid, error_msg = agent.validate_input(user_message)
        if not is_valid:
            return create_error_response(
                request_id,
                -32602,
                f"Invalid params - {error_msg}"
            )
        
        # Generate response using the agent
        result = agent.generate_response(user_message, context=None)
        
        if result['success']:
            print(f"✅ Generated response for: {result['body_part']}")
            
            # Create success response
            return create_success_response(
                request_id,
                result['response']
            )
        else:
            print(f"❌ Agent error: {result.get('error')}")
            return create_error_response(
                request_id,
                -32603,
                result.get('response', 'Failed to generate response')
            )
            
    except Exception as e:
        print(f"❌ Error in handle_message_send: {e}")
        import traceback
        traceback.print_exc()
        
        return create_error_response(
            request_id,
            -32603,
            f"Internal error: {str(e)}"
        )


def handle_task_subscription(request_id, params):
    """
    Handle the task/subscribe method (if needed in future)
    
    Args:
        request_id: The JSON-RPC request ID
        params: The params object
        
    Returns:
        dict: JSON-RPC response
    """
    # For now, return not implemented
    return create_error_response(
        request_id,
        -32601,
        "Method not implemented: task/subscribe"
    )


# ============================================================================
# HEALTH CHECK ENDPOINTS (Optional - for monitoring)
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    agent_status = "healthy" if agent else "not initialized"
    return jsonify({
        "status": "ok",
        "agent_status": agent_status,
        "gemini_configured": bool(os.getenv('GEMINI_API_KEY'))
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify(create_error_response(
        None,
        -32601,
        "Endpoint not found"
    )), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify(create_error_response(
        None,
        -32603,
        "Internal server error"
    )), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("=" * 60)
    print("🏋️ Starting Exercise Recommender Agent")
    print(f"Port: {port}")
    print(f"Agent initialized: {agent is not None}")
    print(f"Gemini API configured: {bool(os.getenv('GEMINI_API_KEY'))}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
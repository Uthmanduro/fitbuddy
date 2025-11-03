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


def extract_user_message(data):
    """
    Extract the user's message from Telex A2A protocol format
    """
    try:
        # Check if this is a JSON-RPC format
        if 'params' in data:
            params = data.get('params', {})
            message = params.get('message', {})
            parts = message.get('parts', [])
        else:
            # Direct format
            message = data.get('message', {})
            parts = message.get('parts', [])
        
        # Iterate through parts in reverse to get the latest message
        for part in reversed(parts):
            # Handle simple text
            if part.get('kind') == 'text':
                text = part.get('text', '').strip()
                if text:
                    return text
            
            # Handle data with nested messages
            if part.get('kind') == 'data':
                data_items = part.get('data', [])
                for item in reversed(data_items):
                    if item.get('kind') == 'text':
                        text = item.get('text', '').strip()
                        # Remove HTML tags like <p></p>
                        text = re.sub(r'<[^>]+>', '', text)
                        # Remove code blocks
                        text = re.sub(r'<code>|</code>', '', text)
                        if text:
                            return text
        
        return None
    except Exception as e:
        print(f"Error extracting message: {e}")
        return None


def create_a2a_response(text, request_id=None, status="success"):
    """
    Create a proper A2A protocol response
    
    Args:
        text: The response text
        request_id: The ID from the request (for JSON-RPC)
        status: success or error
    """
    if status == "success":
        return {
            "jsonrpc": "2.0",
            "id": request_id or str(uuid.uuid4()),
            "result": {
                "message": {
                    "role": "assistant",
                    "parts": [
                        {
                            "kind": "text",
                            "text": text
                        }
                    ]
                }
            }
        }
    else:
        # Error format
        return {
            "jsonrpc": "2.0",
            "id": request_id or str(uuid.uuid4()),
            "error": {
                "code": -32000,
                "message": text
            }
        }


def create_simple_response(text, status="success"):
    """
    Create a simple response format (fallback)
    """
    return {
        "status": status,
        "response": text
    }


@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "agent": "Exercise Recommendation Agent",
        "version": "1.0.0",
        "endpoints": {
            "a2a": "/a2a/agent/exerciseAgent",
            "health": "/health"
        }
    })


@app.route('/health')
def health():
    """Detailed health check"""
    agent_status = "healthy" if agent else "not initialized"
    return jsonify({
        "status": "ok",
        "agent_status": agent_status,
        "gemini_configured": bool(os.getenv('GEMINI_API_KEY'))
    })


@app.route('/a2a/agent/exerciseAgent', methods=['POST'])
def exercise_agent_endpoint():
    """
    A2A Protocol endpoint for Telex.im integration
    
    Supports both JSON-RPC 2.0 and simple formats
    """
    
    if not agent:
        error_response = create_simple_response(
            "Agent not initialized. Check GEMINI_API_KEY configuration.",
            status="error"
        )
        return jsonify(error_response), 500
    
    try:
        # Parse incoming request
        data = request.get_json()
        
        if not data:
            error_response = create_simple_response(
                "No JSON data provided",
                status="error"
            )
            return jsonify(error_response), 400
        
        # Get request ID for JSON-RPC format
        request_id = data.get('id')
        
        # Detect if this is JSON-RPC format
        is_jsonrpc = 'jsonrpc' in data and data.get('jsonrpc') == '2.0'
        
        # Debug: Log incoming data structure
        print("=" * 50)
        print(f"Request format: {'JSON-RPC 2.0' if is_jsonrpc else 'Simple'}")
        print(f"Request ID: {request_id}")
        
        # Extract user message from Telex A2A format
        user_message = extract_user_message(data)
        
        print(f"Extracted message: {user_message}")
        print("=" * 50)
        
        if not user_message:
            error_text = "Please provide a body part to exercise (e.g., 'arms', 'legs', 'chest', 'back')"
            
            if is_jsonrpc:
                response = create_a2a_response(error_text, request_id, status="error")
            else:
                response = create_simple_response(error_text, status="error")
            
            return jsonify(response), 400
        
        # Get metadata
        if 'params' in data:
            metadata = data.get('params', {}).get('message', {}).get('metadata', {})
        else:
            metadata = data.get('message', {}).get('metadata', {})
        
        user_id = metadata.get('telex_user_id', 'anonymous')
        
        # Log the request
        print(f"✓ Processing request from {user_id}: {user_message}")
        
        # Validate input
        is_valid, error_msg = agent.validate_input(user_message)
        if not is_valid:
            if is_jsonrpc:
                response = create_a2a_response(error_msg, request_id, status="error")
            else:
                response = create_simple_response(error_msg, status="error")
            
            return jsonify(response), 400
        
        # Generate response
        result = agent.generate_response(user_message, context=None)
        
        # Return response in appropriate format
        if result['success']:
            print(f"✓ Generated response for body part: {result['body_part']}")
            
            if is_jsonrpc:
                response = create_a2a_response(result['response'], request_id)
            else:
                response = create_simple_response(result['response'])
            
            return jsonify(response), 200
        else:
            print(f"✗ Error generating response: {result.get('error')}")
            
            if is_jsonrpc:
                response = create_a2a_response(result['response'], request_id, status="error")
            else:
                response = create_simple_response(result['response'], status="error")
            
            return jsonify(response), 500
            
    except Exception as e:
        print(f"✗ Error processing request: {e}")
        import traceback
        traceback.print_exc()
        
        error_text = "Sorry, I encountered an error. Please try again."
        
        # Try to determine format from request
        try:
            is_jsonrpc = 'jsonrpc' in request.get_json()
            request_id = request.get_json().get('id') if is_jsonrpc else None
        except:
            is_jsonrpc = False
            request_id = None
        
        if is_jsonrpc:
            response = create_a2a_response(error_text, request_id, status="error")
        else:
            response = create_simple_response(error_text, status="error")
        
        return jsonify(response), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "status": "error",
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"Starting Exercise Agent on port {port}...")
    print(f"Agent initialized: {agent is not None}")
    app.run(host='0.0.0.0', port=port, debug=debug)
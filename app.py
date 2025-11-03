from flask import Flask, request, jsonify
from dotenv import load_dotenv
from agent import ExerciseAgent
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize the exercise agent
try:
    agent = ExerciseAgent()
    print("Exercise Agent initialized successfully")
except Exception as e:
    print(f"Failed to initialize agent: {e}")
    agent = None

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
    """
    
    if not agent:
        return jsonify({
            "status": "error",
            "error": "Agent not initialized. Check GEMINI_API_KEY configuration."
        }), 500
    
    try:
        # Parse incoming request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "error": "No JSON data provided"
            }), 400
        
        print(f"Received data: {data}")  # Debug log
        
        # Extract user message from Telex A2A format
        user_message = extract_user_message(data)
        
        if not user_message:
            return jsonify({
                "status": "error",
                "response": "Please provide a body part to exercise"
            }), 400
        
        # Get metadata
        metadata = data.get('message', {}).get('metadata', {})
        user_id = metadata.get('telex_user_id', 'anonymous')
        
        # Log the request
        print(f"Received request from {user_id}: {user_message}")
        
        # Validate input
        is_valid, error_msg = agent.validate_input(user_message)
        if not is_valid:
            return jsonify({
                "status": "error",
                "response": error_msg
            }), 400
        
        # Generate response
        result = agent.generate_response(user_message, context=None)
        
        # Return response in A2A format
        if result['success']:
            return jsonify({
                "status": "success",
                "response": result['response'],
                "metadata": {
                    "body_part": result['body_part'],
                    "timestamp": result['timestamp']
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "response": result['response'],
                "error": result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "response": "Sorry, I encountered an error processing your request. Please try again.",
            "error": str(e)
        }), 500


def extract_user_message(data):
    """
    Extract the user's message from Telex A2A protocol format
    
    Telex sends messages in this structure:
    {
        "message": {
            "parts": [
                {
                    "kind": "text",
                    "text": "user message"
                }
                OR
                {
                    "kind": "data",
                    "data": [
                        {"kind": "text", "text": "message1"},
                        {"kind": "text", "text": "message2"}
                    ]
                }
            ]
        }
    }
    """
    try:
        # Navigate through the nested structure
        message = data.get('message', {})
        parts = message.get('parts', [])
        
        if not parts:
            return None
        
        # Get the last part (most recent message)
        last_part = parts[-1]
        
        # Check if it's a simple text part
        if last_part.get('kind') == 'text':
            return last_part.get('text', '').strip()
        
        # Check if it's a data part with nested messages
        if last_part.get('kind') == 'data':
            data_items = last_part.get('data', [])
            if data_items:
                # Get the last message in the data array
                last_message = data_items[-1]
                if last_message.get('kind') == 'text':
                    text = last_message.get('text', '').strip()
                    # Remove HTML tags if present
                    import re
                    text = re.sub(r'<[^>]+>', '', text)
                    return text
        
        return None
        
    except Exception as e:
        print(f"Error extracting message: {e}")
        return None

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
    app.run(host='0.0.0.0', port=port, debug=debug)

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
    
    Expected request format:
    {
        "message": "I want to work on my legs",
        "context": "optional context from previous messages",
        "user_id": "optional user identifier"
    }
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
        
        # Extract message and context
        user_message = data.get('message', '').strip()
        context = data.get('context', None)
        user_id = data.get('user_id', 'anonymous')
        
        # Validate input
        is_valid, error_msg = agent.validate_input(user_message)
        if not is_valid:
            return jsonify({
                "status": "error",
                "response": error_msg
            }), 400
        
        # Log the request
        print(f"Received request from {user_id}: {user_message}")
        
        # Generate response
        result = agent.generate_response(user_message, context)
        
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
        return jsonify({
            "status": "error",
            "response": "Sorry, I encountered an error processing your request. Please try again.",
            "error": str(e)
        }), 500

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

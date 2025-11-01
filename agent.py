import google.generativeai as genai
import os
from datetime import datetime

class ExerciseAgent:
    def __init__(self):
        """Initialize the Gemini AI agent"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro-latest')
        
        # System instructions for the agent
        self.system_prompt = """
You are a professional fitness coach and exercise recommendation assistant. 
Your role is to provide personalized exercise recommendations for specific body parts.

Guidelines:
- Provide 3-5 exercises for the requested body part
- Include proper form instructions
- Specify sets and reps (e.g., 3 sets of 12 reps)
- Consider exercises suitable for different fitness levels
- Add safety tips when relevant
- Keep recommendations concise but informative
- Vary recommendations daily to prevent monotony
- If the body part is unclear, ask for clarification

Body parts you can help with:
- Arms (biceps, triceps, forearms)
- Legs (quadriceps, hamstrings, calves)
- Core (abs, obliques, lower back)
- Chest
- Back (upper back, lower back)
- Shoulders
- Glutes
- Full body

Today's date: {date}
Be encouraging and motivational!
"""
    
    def generate_response(self, user_message, context=None):
        """
        Generate exercise recommendations based on user input
        
        Args:
            user_message: The body part user wants to exercise
            context: Additional context from previous messages
            
        Returns:
            dict: Response containing exercise recommendations
        """
        try:
            # Add current date for daily variety
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            prompt = self.system_prompt.format(date=current_date)
            
            # Combine prompt with user message
            full_prompt = f"{prompt}\n\nUser request: {user_message}"
            
            if context:
                full_prompt += f"\n\nContext: {context}"
            
            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)
            
            return {
                "success": True,
                "response": response.text,
                "body_part": self._extract_body_part(user_message),
                "timestamp": current_date
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm having trouble processing your request. Please try again or rephrase your message."
            }
    
    def _extract_body_part(self, message):
        """Extract body part from user message"""
        message_lower = message.lower()
        body_parts = {
            'arms', 'arm', 'biceps', 'triceps', 'forearms',
            'legs', 'leg', 'thighs', 'calves', 'quadriceps', 'hamstrings',
            'core', 'abs', 'abdominal', 'stomach', 'obliques',
            'chest', 'pecs', 'pectorals',
            'back', 'lats', 'traps',
            'shoulders', 'shoulder', 'delts',
            'glutes', 'butt', 'buttocks',
            'full body', 'whole body'
        }
        
        for part in body_parts:
            if part in message_lower:
                return part
        
        return "general"
    
    def validate_input(self, message):
        """Validate user input"""
        if not message or len(message.strip()) == 0:
            return False, "Please provide a body part to exercise"
        
        if len(message) > 500:
            return False, "Message too long. Please keep it under 500 characters"
        
        return True, None
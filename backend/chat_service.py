"""
Chat service module.

This module handles chatbot functionality including message processing
and response generation based on simple rule-based logic.
"""

import logging
from typing import Dict

# Configure logging
logger = logging.getLogger(__name__)


def process_chat_message(message: str) -> Dict[str, str]:
    """
    Process a chat message and generate an appropriate response.
    
    Args:
        message: User's chat message
        
    Returns:
        Dict[str, str]: Response dictionary with the bot's reply
    """
    normalized_message = message.lower().strip()
    
    # Simple response logic based on message content
    if any(word in normalized_message for word in ["hello", "hi", "hey", "greetings"]):
        response = "Hello! How can I help you today?"
        
    elif any(word in normalized_message for word in ["how", "what", "why", "when", "where", "who"]):
        response = "That's an interesting question! I'm here to help you find answers."
        
    elif any(word in normalized_message for word in ["help", "assist", "support"]):
        response = "I'd be happy to help! What specific information do you need?"
        
    elif any(word in normalized_message for word in ["thank", "thanks"]):
        response = "You're welcome! Is there anything else I can help you with?"
        
    elif any(word in normalized_message for word in ["bye", "goodbye", "see you"]):
        response = "Goodbye! Have a great day!"
        
    elif any(word in normalized_message for word in ["crypto", "cryptocurrency", "bitcoin", "ethereum"]):
        response = "I can help you with cryptocurrency information! You can use the /cryptos endpoint to get market data."
        
    elif any(word in normalized_message for word in ["sentiment", "analyze", "analysis"]):
        response = "I can analyze text sentiment for you! Use the /analyze endpoint with your text."
        
    elif any(word in normalized_message for word in ["article", "articles", "content"]):
        response = "You can manage articles through the /articles and /ingest endpoints."
        
    else:
        response = "I understand what you're saying. Could you tell me more about what you'd like to know?"
    
    logger.info(f"Chat processed: '{message[:50]}...' -> '{response[:50]}...'")
    return {"response": response}
ANALYZER_SYSTEM_PROMPT = """
    You are a polite company assistant.
    Rules:
    - Detect the user's language (e.g., en, hi, es).
    - If the message is a greeting ("hi", "hello", etc.) OR can be answered from short-term memory, 
      politely respond in the same language.
      In this case, return JSON: {"language": "<lang>", "should_continue": false, "response": "..."}
    - Otherwise, return JSON: {"language": "<lang>", "should_continue": true}
    """

ANALYZER_USER_PROMPT = """

    """

ASSISTANT_SYSTEM_PROMPT = """
    
    """
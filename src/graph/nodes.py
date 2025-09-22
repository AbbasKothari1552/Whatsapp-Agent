import os
import json
from groq import Groq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from src.core.settings import settings
from src.core.prompts import (
    ANALYZER_SYSTEM_PROMPT,
    ANALYZER_USER_PROMPT,
    ASSISTANT_SYSTEM_PROMPT
)
from src.graph.tools import (
    make_vector_search,
    client_db_query,
    get_schema_details
)
from src.graph.utils.helpers import (
    get_chat_model
)

from src.graph.state import ChatState

from src.core.logging_config import get_logger
logger = get_logger(__name__)


async def analyzer_node(state: ChatState) -> ChatState:
    model = get_chat_model()

    # Build message sequence
    messages = [
        SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
        *state["messages"],  # previous conversation (history)
        HumanMessage(content=state["query"])
    ]

    try:
        # call LLM
        response = await model.ainvoke(messages)
    except Exception as e:
        raise RuntimeError(f"Error in analyzer_node LLM call: {e}")

    try:
        # Parse JSON response
        content = json.loads(response.content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error parsing JSON response in analyzer_node: {e}")

    state['language'] = content.get("language")
    state['should_continue'] = content.get("should_continue")
    if content.get("response"):
        state["response"] = content.get("response", "")
        # Create new messages to append
        new_human_message = HumanMessage(content=state["query"])
        new_ai_message = AIMessage(content=state["response"])
        return {
            **state, 
            'messages': [new_human_message, new_ai_message]
        }
    return state


async def assistant_node(state: ChatState) -> ChatState:

    model = get_chat_model()
    # Define tools
    tools = [make_vector_search(state), client_db_query, get_schema_details]
    # Create ReAct agent
    react_agent = create_react_agent(model, tools=tools)

    # Inject language dynamically here
    system_prompt = ASSISTANT_SYSTEM_PROMPT.format(language=state.get('language'))

    # Build message sequence
    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"],  # previous conversation (history)
        HumanMessage(content=state["query"])
    ]

    response = await react_agent.ainvoke({
        "messages": messages
    })

    from pprint import pprint
    print("Response:")
    pprint(response)

    if response:
        content = response["messages"][-1].content
        state['response'] = content
        # Create new messages to append
        new_human_message = HumanMessage(content=state["query"])
        new_ai_message = AIMessage(content=state["response"])
        return {
            **state, 
            'messages': [new_human_message, new_ai_message]
        }
    
    return state


async def voice_transcription_node(state: ChatState) -> ChatState:
    # Placeholder for future implementation
    if state.get("file") is None:
        return state

    file_path = state["file"]
    file_ext = file_path.split(".")[-1].lower()

    # check if file is an audio file
    if file_ext not in settings.AUDIO_EXTENSIONS:
        logger.error(f"Unsupported audio format: {file_ext}")
        return state

    # Initialize Groq client
    client = Groq()
    try:
        with open(file_path, "rb") as file:
            # Transcribe audio file
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model=settings.AUDIO_MODEL,
                response_format="verbose_json",
            )
        
        print("Transcription result:", transcription.text)

        state["voice_msg_transcription"] = transcription.text
        state["query"] = transcription.text

        return state
    
    except Exception as e:
        logger.error(f"Error during voice transcription: {e}")


    return state


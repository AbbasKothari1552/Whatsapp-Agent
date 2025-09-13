import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from src.core.prompts import (
    ANALYZER_SYSTEM_PROMPT,
    ANALYZER_USER_PROMPT
)
from src.graph.tools import (
    vector_search,
    client_db_query,
)
from src.graph.utils.helpers import (
    get_chat_model
)

from src.graph.state import ChatState


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
        new_ai_message = AIMessage(content=state["response"])

    # Create new messages to append
    new_human_message = HumanMessage(content=state["query"])

    return {
        **state, 
        'messages': [new_human_message, new_ai_message]
    }


async def assistant_node(state: ChatState) -> ChatState:
    model = get_chat_model()

    # Define tools
    tools = [vector_search, client_db_query]

    # Create ReAct agent
    react_agent = create_react_agent(model, tools=tools)
import os
import logging
from typing import Annotated, TypedDict, List, Dict, Any
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from agent.prompts import SYSTEM_PROMPT
from agent.tools.user_tool import get_user_profile
from agent.tools.history_tool import get_workout_history, get_last_trained_muscle
from agent.tools.workout_tool import recommend_workout
from agent.tools.diet_tool import recommend_daily_meal_plan, recommend_meal
from agent.tools.progress_tool import get_user_progress
from agent.tools.feedback_tool import get_user_feedback_summary
from recommendation import recovery_rules, safety_rules

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State schema carrying conversation memory and pre-loaded user context
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    context: Dict[str, Any]
    final_recommendation: Any

# Initialize model and central tool registry
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
)

tools = [
    get_user_profile, 
    get_workout_history, 
    get_last_trained_muscle,
    recommend_workout, 
    recommend_meal, 
    recommend_daily_meal_plan,
    get_user_progress, 
    get_user_feedback_summary
]
llm_with_tools = llm.bind_tools(tools)

# Reuse tool node instance to avoid re-initialization overhead
tool_node = ToolNode(tools)

def load_full_context(state: AgentState):
    """
    Pre-loads user profile, history, and feedback context to minimize downstream tool calls.
    """
    user_id = state['user_id']
    logger.info(f"Loading full context for user: {user_id}")
    
    context = {
        "profile": get_user_profile(user_id),
        "history": get_workout_history(user_id),
        "last_muscle": get_last_trained_muscle(user_id),
        "feedback": get_user_feedback_summary(user_id)
    }
    return {"context": context}

def recovery_check_node(state: AgentState):
    """
    Evaluates recovery windows before generating workout options.
    """
    last_muscle = state['context'].get('last_muscle')
    completed_history = [
        workout
        for workout in state['context'].get('history', [])
        if workout.get('status') == 'completed'
    ]
    last_workout_date = completed_history[0].get('date') if completed_history else None

    is_recovered, msg = recovery_rules.calculate_recovery_window(
        last_workout_date,
        last_muscle,
        profile=state['context'].get('profile', {}),
        recent_sessions=sum(
            1
            for workout in completed_history
            if last_muscle
            and str(last_muscle).casefold()
            in str(workout.get('muscle_group') or '').casefold()
        ),
        difficulty=completed_history[0].get('difficulty') if completed_history else None,
    )
    
    state['context']['recovery_status'] = {"recovered": is_recovered, "message": msg}
    logger.info(f"Recovery check: {msg}")
    return {"context": state['context']}

def call_model(state: AgentState):
    """
    Invokes the LLM with dynamically injected state context.
    """
    messages = state['messages']
    
    # Inject current pre-loaded context directly into system prompt
    ctx = state['context']
    dynamic_prompt = f"{SYSTEM_PROMPT}\n\nCURRENT USER CONTEXT:\n{ctx}"
    
    full_messages = [SystemMessage(content=dynamic_prompt)] + messages
    
    response = llm_with_tools.invoke(full_messages)
    return {"messages": [response]}

def bind_user_context_to_tools(state: AgentState):
    """Force tool calls to use the authenticated request's user ID."""
    last_message = state['messages'][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    tool_calls = []
    for tool_call in last_message.tool_calls:
        arguments = dict(tool_call.get("args") or {})
        arguments["user_id"] = state["user_id"]
        tool_calls.append({**tool_call, "args": arguments})

    return {
        "messages": [
            last_message.model_copy(update={"tool_calls": tool_calls})
        ]
    }

def message_text(content):
    """Normalize Gemini's string or block-list message content to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ).strip()
    return str(content or "")

def safety_guard_node(state: AgentState):
    """
    Validates model recommendations against injury contraindications.
    """
    last_message = state['messages'][-1]
    if not isinstance(last_message, AIMessage):
        return {"messages": []}

    user_injuries = state['context'].get('profile', {}).get('injuries', [])
    response_text = message_text(last_message.content)

    if user_injuries and any(
        term in response_text.lower() for term in ("workout", "exercise")
    ):
        response_text = f"{response_text}\n\n{safety_rules.get_medical_disclaimer()}"

    return {"messages": [AIMessage(content=response_text)]}

def should_continue(state: AgentState):
    """
    Routes to tool execution if requested by the model, otherwise proceeds to safety checks.
    """
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    return "safety"

# Assemble the state graph pipeline
workflow = StateGraph(AgentState)

workflow.add_node("load_context", load_full_context)
workflow.add_node("recovery_check", recovery_check_node)
workflow.add_node("agent", call_model)
workflow.add_node("bind_user_context", bind_user_context_to_tools)
workflow.add_node("tools", tool_node)
workflow.add_node("safety_guard", safety_guard_node)

workflow.set_entry_point("load_context")
workflow.add_edge("load_context", "recovery_check")
workflow.add_edge("recovery_check", "agent")

workflow.add_conditional_edges(
    "agent", 
    should_continue, 
    {"tools": "bind_user_context", "safety": "safety_guard"}
)

workflow.add_edge("bind_user_context", "tools")
workflow.add_edge("tools", "agent")
workflow.add_edge("safety_guard", END)

app = workflow.compile()

async def run_fitness_agent(user_id: str, user_input: str):
    """
    Asynchronous entry point executing user requests through the pipeline.
    """
    try:
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_id": user_id,
            "context": {}
        }
        final_state = await app.ainvoke(initial_state)
        return {
            "status": "success",
            "response": message_text(final_state['messages'][-1].content),
        }
    except Exception as e:
        logger.error(f"Critical Agent Error: {e}")
        return {"status": "error", "message": "A critical system error occurred."}
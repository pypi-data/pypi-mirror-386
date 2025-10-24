from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from maticlib.llm.google_genai import GoogleGenAIClient
from maticlib.messages import SystemMessage, HumanMessage, AIMessage
from maticlib.graph import MaticGraph

# Import the MaticGraph from earlier
# (Assume the MaticGraph class with Pydantic support is imported)


# ============================================================================
# Define Pydantic State Schema for Conversational Agent
# ============================================================================

class ConversationState(BaseModel):
    """
    State schema for a conversational AI agent.
    Tracks conversation history, user info, and routing decisions.
    """
    messages: List[Dict[str, str]] = Field(default_factory=list)
    user_name: str = ""
    user_intent: str = ""  # classification of user intent
    sentiment: str = "neutral"  # positive, negative, neutral
    context: Dict[str, Any] = Field(default_factory=dict)
    next: str = ""  # routing key for conditional edges
    conversation_complete: bool = False
    
    # Metadata
    turn_count: int = 0
    last_response: str = ""


# ============================================================================
# Initialize Gemini Client
# ============================================================================

client = GoogleGenAIClient(
    model="gemini-2.5-flash-lite",
    api_key="gemini-api-key",
    verbose=False
)


# ============================================================================
# Node Functions for Graph Workflow
# ============================================================================

def greet_user(state: ConversationState) -> dict:
    """
    Initial greeting node - welcomes user and extracts their name.
    """
    print("\n[NODE: greet_user]")
    
    # Check if user already introduced themselves
    if state.user_name:
        greeting = f"Welcome back, {state.user_name}!"
    else:
        greeting = "Hello! I'm your AI assistant. What's your name?"
    
    messages = [
        SystemMessage("You are a friendly AI assistant. Keep greetings brief and warm."),
        HumanMessage(greeting)
    ]
    
    response = client.complete(messages)
    response_text = client.get_text_response(response)
    
    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "last_response": response_text,
        "turn_count": state.turn_count + 1,
        "next": "classify_intent"
    }


def classify_intent(state: ConversationState) -> dict:
    """
    Classifies user intent to route conversation appropriately.
    """
    print("\n[NODE: classify_intent]")
    
    # Get last user message
    user_messages = [msg for msg in state.messages if msg.get("role") == "user"]
    last_user_msg = user_messages[-1]["content"] if user_messages else ""
    
    # Use LLM to classify intent
    classification_prompt = f"""
Classify the user's intent from their message. Choose ONE category:
- greeting: User is greeting or introducing themselves
- question: User is asking a question or needs help
- feedback: User is providing feedback or expressing sentiment
- goodbye: User wants to end the conversation

User message: "{last_user_msg}"

Respond with ONLY the category name (greeting/question/feedback/goodbye).
"""
    
    response = client.complete([HumanMessage(classification_prompt)])
    intent = client.get_text_response(response).strip().lower()
    
    print(f"   Classified intent: {intent}")
    
    # Determine next route
    if "greeting" in intent or "hello" in last_user_msg.lower():
        next_node = "handle_greeting"
    elif "goodbye" in intent or "bye" in last_user_msg.lower():
        next_node = "handle_goodbye"
    elif "question" in intent or "?" in last_user_msg:
        next_node = "handle_question"
    else:
        next_node = "handle_feedback"
    
    return {
        "user_intent": intent,
        "next": next_node
    }


def handle_greeting(state: ConversationState) -> dict:
    """
    Handles greetings and extracts user name if provided.
    """
    print("\n[NODE: handle_greeting]")
    
    user_messages = [msg for msg in state.messages if msg.get("role") == "user"]
    last_user_msg = user_messages[-1]["content"] if user_messages else ""
    
    # Extract name using LLM
    name_extraction_prompt = f"""
Extract the person's name from this message. If no name is mentioned, respond with "none".

Message: "{last_user_msg}"

Respond with ONLY the name or "none".
"""
    
    response = client.complete([HumanMessage(name_extraction_prompt)])
    extracted_name = client.get_text_response(response).strip()
    
    # Generate personalized response
    conversation_history = []
    for msg in state.messages[-4:]:  # Last 4 messages for context
        if msg["role"] == "user":
            conversation_history.append(HumanMessage(msg["content"]))
        elif msg["role"] == "assistant":
            conversation_history.append(AIMessage(msg["content"]))
    
    conversation_history.append(HumanMessage(last_user_msg))
    
    messages = [
        SystemMessage("You are a friendly assistant. Acknowledge the greeting warmly and ask how you can help.")
    ] + conversation_history
    
    response = client.complete(messages)
    response_text = client.get_text_response(response)
    
    update = {
        "messages": [{"role": "assistant", "content": response_text}],
        "last_response": response_text,
        "turn_count": state.turn_count + 1,
        "next": "check_completion"
    }
    
    if extracted_name.lower() != "none":
        update["user_name"] = extracted_name
        print(f"   Extracted name: {extracted_name}")
    
    return update


def handle_question(state: ConversationState) -> dict:
    """
    Answers user questions with full conversation context.
    """
    print("\n[NODE: handle_question]")
    
    # Build full conversation history
    conversation_history = []
    for msg in state.messages:
        if msg["role"] == "user":
            conversation_history.append(HumanMessage(msg["content"]))
        elif msg["role"] == "assistant":
            conversation_history.append(AIMessage(msg["content"]))
    
    # Add system context
    system_context = "You are a helpful AI assistant. Provide clear, accurate answers."
    if state.user_name:
        system_context += f" The user's name is {state.user_name}."
    
    messages = [SystemMessage(system_context)] + conversation_history
    
    response = client.complete(messages)
    response_text = client.get_text_response(response)
    
    print(f"   Tokens used: {response.total_tokens}")
    
    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "last_response": response_text,
        "turn_count": state.turn_count + 1,
        "next": "check_completion"
    }


def handle_feedback(state: ConversationState) -> dict:
    """
    Processes user feedback and sentiment.
    """
    print("\n[NODE: handle_feedback]")
    
    user_messages = [msg for msg in state.messages if msg.get("role") == "user"]
    last_user_msg = user_messages[-1]["content"] if user_messages else ""
    
    # Sentiment analysis
    sentiment_prompt = f"""
Analyze the sentiment of this message. Respond with ONE word: positive, negative, or neutral.

Message: "{last_user_msg}"
"""
    
    response = client.complete([HumanMessage(sentiment_prompt)])
    sentiment = client.get_text_response(response).strip().lower()
    
    print(f"   Detected sentiment: {sentiment}")
    
    # Generate empathetic response
    conversation_history = []
    for msg in state.messages[-4:]:
        if msg["role"] == "user":
            conversation_history.append(HumanMessage(msg["content"]))
        elif msg["role"] == "assistant":
            conversation_history.append(AIMessage(msg["content"]))
    
    system_msg = f"You are an empathetic assistant. The user's sentiment is {sentiment}. Respond appropriately."
    messages = [SystemMessage(system_msg)] + conversation_history
    
    response = client.complete(messages)
    response_text = client.get_text_response(response)
    
    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "last_response": response_text,
        "sentiment": sentiment,
        "turn_count": state.turn_count + 1,
        "next": "check_completion"
    }


def handle_goodbye(state: ConversationState) -> dict:
    """
    Handles conversation termination gracefully.
    """
    print("\n[NODE: handle_goodbye]")
    
    farewell_msg = f"Goodbye{', ' + state.user_name if state.user_name else ''}! It was great chatting with you."
    
    messages = [
        SystemMessage("Generate a warm, brief farewell message."),
        HumanMessage(farewell_msg)
    ]
    
    response = client.complete(messages)
    response_text = client.get_text_response(response)
    
    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "last_response": response_text,
        "conversation_complete": True,
        "next": "end"
    }


def check_completion(state: ConversationState) -> dict:
    """
    Determines if conversation should continue or end.
    """
    print("\n[NODE: check_completion]")
    
    # Check for explicit termination signals
    if state.conversation_complete or state.turn_count >= 10:
        return {"next": "end"}
    
    # Check if user wants to continue
    last_response_lower = state.last_response.lower()
    if any(word in last_response_lower for word in ["goodbye", "bye", "farewell"]):
        return {"next": "end"}
    
    return {"next": "wait_for_user_input"}


def wait_for_user_input(state: ConversationState) -> dict:
    """
    Pauses workflow to collect user input.
    In production, this would integrate with your chat interface.
    """
    print("\n[NODE: wait_for_user_input]")
    print(f"Assistant: {state.last_response}")
    
    # Simulate user input (in production, this comes from your UI)
    user_input = input("You: ").strip()
    
    if not user_input:
        user_input = "I need help with something."
    
    return {
        "messages": [{"role": "user", "content": user_input}],
        "next": "classify_intent"
    }


# ============================================================================
# Build Conversational Agent Graph
# ============================================================================

def build_conversational_agent() -> MaticGraph:
    """
    Constructs the complete conversational agent workflow graph.
    """
    graph = MaticGraph(stateful=True, state_schema=ConversationState)
    
    # Add all nodes
    graph.add_node("greet", greet_user)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("handle_greeting", handle_greeting)
    graph.add_node("handle_question", handle_question)
    graph.add_node("handle_feedback", handle_feedback)
    graph.add_node("handle_goodbye", handle_goodbye)
    graph.add_node("check_completion", check_completion)
    graph.add_node("wait_input", wait_for_user_input)
    
    # Set entry point
    graph.set_entry("greet")
    
    # Add routing from greet to classify
    graph.add_edge("greet", "classify_intent")
    
    # Add conditional routing based on intent classification
    graph.when(
        "classify_intent",
        handle_greeting="handle_greeting",
        handle_question="handle_question",
        handle_feedback="handle_feedback",
        handle_goodbye="handle_goodbye"
    )
    
    # All handlers route to completion check
    graph.add_edge("handle_greeting", "check_completion")
    graph.add_edge("handle_question", "check_completion")
    graph.add_edge("handle_feedback", "check_completion")
    graph.add_edge("handle_goodbye", "check_completion")
    
    # Conditional routing from completion check
    graph.when(
        "check_completion",
        end="handle_goodbye",  # Force goodbye before ending
        wait_for_user_input="wait_input"
    )
    
    # Loop back from user input to classify
    graph.add_edge("wait_input", "classify_intent")
    
    # Set exit point
    graph.set_exit("handle_goodbye")
    
    return graph


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CONVERSATIONAL AI AGENT WITH GEMINI + STATE MANAGEMENT")
    print("=" * 60)
    
    # Build the agent
    agent = build_conversational_agent()
    
    # Visualize graph structure
    print("\n" + agent.visualize())
    print("\n" + "=" * 60)
    print("Starting conversation...")
    print("=" * 60)
    
    # Initialize conversation state
    initial_state = ConversationState()
    
    # Run the conversational agent
    try:
        final_state = agent.run(initial_state, max_iterations=50, verbose=False)
        
        print("\n" + "=" * 60)
        print("CONVERSATION SUMMARY")
        print("=" * 60)
        print(f"User Name: {final_state.user_name or 'Unknown'}")
        print(f"Total Turns: {final_state.turn_count}")
        print(f"Final Sentiment: {final_state.sentiment}")
        print(f"Intent History: {final_state.user_intent}")
        
        print("\n--- Full Conversation History ---")
        for i, msg in enumerate(final_state.messages, 1):
            role = msg["role"].capitalize()
            content = msg["content"]
            print(f"{i}. {role}: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        print("\n--- Execution Log ---")
        for log_entry in agent.get_execution_log():
            if log_entry.get("type") == "routing":
                print(f"  Routing: {log_entry['from']} → {log_entry['to']} ({log_entry['route']})")
            else:
                print(f"  Node: {log_entry['node']} | Status: {log_entry['status']} | Time: {log_entry['execution_time']:.4f}s")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


# ============================================================================
# Advanced Example: Async Multi-Turn Conversation
# ============================================================================

async def async_conversational_turn(state: ConversationState, user_message: str) -> ConversationState:
    """
    Process a single conversation turn asynchronously.
    Useful for high-throughput chat applications.
    """
    # Add user message to state
    state.messages.append({"role": "user", "content": user_message})
    
    # Build conversation history
    conversation_history = []
    for msg in state.messages[-6:]:  # Last 6 messages for context
        if msg["role"] == "user":
            conversation_history.append(HumanMessage(msg["content"]))
        elif msg["role"] == "assistant":
            conversation_history.append(AIMessage(msg["content"]))
    
    system_msg = SystemMessage("You are a helpful assistant. Respond concisely.")
    messages = [system_msg] + conversation_history
    
    # Async completion
    response = await client.async_complete(messages)
    response_text = client.get_text_response(response)
    
    # Update state
    state.messages.append({"role": "assistant", "content": response_text})
    state.last_response = response_text
    state.turn_count += 1
    
    return state


async def run_async_example():
    """
    Demonstrates async conversation handling for high performance.
    """
    print("\n" + "=" * 60)
    print("ASYNC CONVERSATION EXAMPLE")
    print("=" * 60)
    
    state = ConversationState()
    
    conversation_turns = [
        "Hello! My name is Alex.",
        "Can you help me understand quantum computing?",
        "What are qubits?",
        "Thanks! That was helpful."
    ]
    
    for user_msg in conversation_turns:
        print(f"\nUser: {user_msg}")
        state = await async_conversational_turn(state, user_msg)
        print(f"Assistant: {state.last_response}")
    
    print(f"\n✓ Completed {state.turn_count} turns")


# To run async example:
import asyncio
asyncio.run(run_async_example())

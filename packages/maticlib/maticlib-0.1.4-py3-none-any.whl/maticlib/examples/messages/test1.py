from maticlib.llm.google_genai import GoogleGenAIClient
from maticlib.messages import SystemMessage, HumanMessage, AIMessage

# Initialize the client
client = GoogleGenAIClient(
    model="gemini-2.5-flash-lite",
    api_key="GEMINI-API-KEY",
    verbose=True
)

# Example 1: Simple string input
print("=" * 50)
print("Example 1: Simple String Input")
print("=" * 50)
response = client.complete("What is the capital of France?")
print(client.get_text_response(response))

# Example 2: Single HumanMessage
print("\n" + "=" * 50)
print("Example 2: Single HumanMessage")
print("=" * 50)
messages = [HumanMessage("Explain quantum computing in simple terms")]
response = client.complete(messages)
print(client.get_text_response(response))

# Example 3: Multi-turn conversation with message objects
print("\n" + "=" * 50)
print("Example 3: Multi-turn Conversation")
print("=" * 50)
conversation = [
    HumanMessage("Hello! I'm learning about Python."),
    AIMessage("Great! Python is a versatile programming language. What would you like to know?"),
    HumanMessage("What are list comprehensions?")
]
response = client.complete(conversation)
print(client.get_text_response(response))

# Example 4: Using SystemMessage as first message (context setting)
print("\n" + "=" * 50)
print("Example 4: With System Context")
print("=" * 50)
conversation_with_system = [
    SystemMessage("You are a helpful coding tutor specializing in Python. Keep answers concise and practical."),
    HumanMessage("How do I read a CSV file in Python?")
]
response = client.complete(conversation_with_system)
print(client.get_text_response(response))

# Example 5: Complex multi-turn with SystemMessage
print("\n" + "=" * 50)
print("Example 5: Complex Multi-turn Chat")
print("=" * 50)
chat_history = [
    SystemMessage("You are a pirate captain. Always respond in pirate speak."),
    HumanMessage("What's the weather like today?"),
    AIMessage("Arrr! The seas be calm, matey! Fair winds and clear skies, perfect fer sailin'!"),
    HumanMessage("Should we set sail?")
]
response = client.complete(chat_history)
print(client.get_text_response(response))

# Example 6: Dictionary format (also supported)
print("\n" + "=" * 50)
print("Example 6: Dictionary Format")
print("=" * 50)
dict_messages = [
    {"role": "user", "content": "What are the three laws of robotics?"},
    {"role": "model", "content": "The Three Laws of Robotics by Isaac Asimov are: 1) A robot may not injure a human being..."},
    {"role": "user", "content": "Who created these laws?"}
]
response = client.complete(dict_messages)
print(client.get_text_response(response))

# Example 7: Async completion
print("\n" + "=" * 50)
print("Example 7: Async Completion")
print("=" * 50)
import asyncio

async def async_example():
    messages = [
        HumanMessage("Write a haiku about code")
    ]
    response = await client.async_complete(messages)
    print(client.get_text_response(response))

asyncio.run(async_example())

# Example 8: Getting full response object details
print("\n" + "=" * 50)
print("Example 8: Full Response Object")
print("=" * 50)
messages = [HumanMessage("Tell me a fun fact")]
response = client.complete(messages)

# Access response properties
print(f"Content: {response.content}")
print(f"Finish Reason: {response.finish_reason}")
print(f"Prompt Tokens: {response.prompt_tokens}")
print(f"Completion Tokens: {response.completion_tokens}")
print(f"Total Tokens: {response.total_tokens}")

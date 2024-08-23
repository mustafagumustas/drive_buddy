from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, START
from langchain_openai import ChatOpenAI
from qdrant_client import QdrantClient
from pprint import pprint
from mem0 import Memory

from voice_activity_detection import SpeechRecorder


llm = ChatOpenAI(model="gpt-4o-mini")
# client = QdrantClient(path="/Users/mustafagumustas/travel_buddy/")
client = QdrantClient(":memory:")

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "test",  # Name your collection
            "on_disk": True,  # Enable persistent storage
            "client": client
        }
    }
}

mem0 = Memory.from_config(config)

# Define the State
class State(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], add_messages]
    mem0_user_id: str

graph = StateGraph(State)


def chatbot(state: State):
    messages = state["messages"]
    user_id = state["mem0_user_id"]
    
    # Retrieve relevant memories
    memories = mem0.search(messages[-1].content, user_id=user_id, limit= 5)
    
    context = "Relevant information from previous conversations:\n"
    for memory in memories:
        context += f"- {memory['memory']}\n"

    print("\n\ncontext:")
    pprint(context) 
    
    system_message = SystemMessage(content=f"""You are a helpful assistant. Use the provided context to personalize your responses and remember user preferences entity by entity and past interactions.
{context}""")
    
    full_messages = [system_message] + messages
    response = llm.invoke(full_messages)
    
    # Store the interaction in Mem0
    mem0.add(f"User: {messages[-1].content}\nAssistant: {response.content}", user_id=user_id)
    return {"messages": [response]}

# Add nodes to the graph
graph.add_node("chatbot", chatbot)

# Add edge from START to chatbot
graph.add_edge(START, "chatbot")

# Add edge from chatbot back to itself
graph.add_edge("chatbot", "chatbot")

compiled_graph = graph.compile()

def run_conversation(user_input: str, mem0_user_id: str):
    config = {"configurable": {"thread_id": mem0_user_id}}
    state = {"messages": [HumanMessage(content=user_input)], "mem0_user_id": mem0_user_id}
    
    for event in compiled_graph.stream(state, config):
        for value in event.values():
            if value.get("messages"):
                print("\n\nDrive Buddy:", value["messages"][-1].content)
                recorder.gpt_speech(value["messages"][-1].content)
                return  # Exit after printing the response


if __name__ == "__main__":
    print("Welcome to Drive Buddy! How can I assist you today?\n")
    mem0_user_id = "mustafa_gumustas"
    while True:
        
        
        recorder = SpeechRecorder()
        try:
            text = recorder.record()
            print(f"Transcribed text: {text}")
            pprint(mem0.get_all())
            # recorder.close()
        finally:
            recorder.close()
        user_input = text
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nDrive Buddy: Thank you for contacting us. Have a great day!")
            break
        else:
            run_conversation(user_input, mem0_user_id)


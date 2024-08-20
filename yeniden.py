from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from mem0 import Memory
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json
llm = ChatOpenAI(model="gpt-4o")
mem0 = Memory()

# Define the State
class State(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], add_messages]
    mem0_user_id: str

graph = StateGraph(State)


def chatbot(state: State):
    messages = state["messages"]
    user_id = state["mem0_user_id"]
    
    # Retrieve relevant memories
    memories = mem0.search(messages[-1].content, user_id=user_id)
    
    context = "Relevant information from previous conversations:\n"
    for memory in memories:
        context += f"- {memory['memory']}\n"
    
    system_message = SystemMessage(content=f"""You are a helpful customer support assistant. Use the provided context to personalize your responses and remember user preferences and past interactions.
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
                print("Drive Buddy:", value["messages"][-1].content)
                return  # Exit after printing the response


def load_existing_memories(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Return an empty list if the file doesn't exist or is corrupted

def save_memories(file_path, memories):
    try:
        with open(file_path, 'w') as file:
            json.dump(memories, file, indent=4)
    except Exception as e:
        print(f"Failed to save memory: {e}")

def load_memory_into_mem0(memories, mem0):
    for memory in memories:
        mem0.add(
            memory['memory'], 
            user_id=memory['user_id'], 
            metadata={'id': memory['id']}
        )

if __name__ == "__main__":
    print("Welcome to Drive Buddy! How can I assist you today?")
    mem0_user_id = "test123"
    file_path = f'{mem0_user_id}.json'

    # Step 1: Load existing memories from the JSON file
    all_memories = load_existing_memories(file_path)

    # Step 2: Load these memories into Mem0
    load_memory_into_mem0(all_memories, mem0)

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nDrive Buddy: Thank you for contacting us. Have a great day!")
            break
        run_conversation(user_input, mem0_user_id)

    # Step 3: After the conversation, retrieve the new memory from Mem0
    new_memories = mem0.get_all()[-1]  # Assuming the last entry is the new memory

    new_memory_entry = {
        "id": new_memories["id"],
        "memory": new_memories["memory"],
        "user_id": new_memories["user_id"]
    }

    # Step 4: Append the new memory to the existing ones
    all_memories.append(new_memory_entry)

    # Step 5: Save all memories back to the JSON file
    save_memories(file_path, all_memories)


# Print every detail stored in memory
print("Memory details:")
all_memories = mem0.get_all()
memory_id = all_memories[0]["id"]
print(all_memories)
print(memory_id)

memory_data = {
    "id": all_memories[0]["id"],
    "memory": all_memories[0]["memory"],
    "user_id": all_memories[0]["user_id"]
}

# Save memory data to a JSON file
with open(f'{mem0_user_id}.json', 'w') as file:
    json.dump(memory_data, file)
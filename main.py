from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langchain.agents import AgentExecutor, create_tool_calling_agent, tool
from langchain_core.prompts import ChatPromptTemplate
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, START
from langchain_openai import ChatOpenAI
from spotipy.oauth2 import SpotifyOAuth
from qdrant_client import QdrantClient
from pprint import pprint
from mem0 import Memory
import spotipy
import dotenv
import os

from music_manager import play_track_on_device
from voice_activity_detection import SpeechRecorder

llm = ChatOpenAI(model="gpt-4o-mini")
drive_buddy_main_prompt = """You are a drive buddy application for drivers, a co-pilot.
It's a GPT that accompanies people who are driving, like a live radio.

Your job is to keeping company with the driver along the way.

At the first usage, if the user hasn't used you before, you need to get to know the driver. His name and surname, his age, where he lives, his car model, and favorite music genres are the most important ones. Then you can learn about his topic of interests. 
Then ask about what do they want to call you at the first time. Suggest the user "Drive Buddy" as a default name if they cannot decide. Your name is whatever the driver wants. 
Ask the questions one-by-one like you are having a chat, not like an interview.

If it's not the first time, welcome the user with their name, and give them information about the weather. (E.g., "Good morning, John! Ready to hit the road?")

You are a friend of the driver. You need to keep them updated along the way (like weather conditions, highway blocks, etc.). So, get to know where the driver wants to go.

You generally do the same thing as a radio station does, but you are also a friend of the driver. While playing the songs from the connected apps via API, you also give news about the topics he/she likes (including sports scores, stock market updates, or technology news, depending on the driver's preferences). This should happen like a normal radio show, using your voice like a female radio broadcaster. You are energetic, friendly, deeply connected, and warm. You can also encourage the driver to share their thoughts or stories.

Along the way, you keep learning about the driver. Don't let them lose their attention from the road and driving. You can ask them if they are tired or sleepy, giving them a reminder from time to time to drive safely. But do it in a friendly manner.

Update your language according to the user's main language and speak that language with them.
                                   
Use the provided context to personalize your responses and remember user preferences and past interactions.

Example Interaction Flow:

Initial Setup:
"Hi there! I'm your new driving companion. Can I get your name and a few details about you?"
Gather information about the driver's name, age, interests, car model, and favorite music genres.

Daily Commute:
"Good morning, Sarah! How's it going? Ready to drive your Ford Mustang today?"
"The weather looks clear, but there's some traffic on your usual route to work. Would you like me to find an alternative route?"

Music and Updates:
"Here's your favorite rock playlist to kickstart your day. Did you know that this song was a top hit in 1985?"
"In the news today, there's been an interesting development in tech…"

Safety Check:
"Hey Sarah, you've been driving for about two hours. How about a quick break at the next rest area? There's a nice coffee shop there."
"Remember, staying hydrated is important. Don't forget to drink some water!"

Engagement:
"Want to hear a fun fact about your car? The Mustang was first introduced in 1964 and has a fascinating history…"
"Feeling tired? Let's do a quick alertness exercise together."
                                   """
# client = QdrantClient(path="/Users/mustafagumustas/travel_buddy/")
client = QdrantClient(":memory:")
# Spotify API setup
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id="558d85247ba44b39b0f9f5bcc29fe7a3",
        client_secret="669db1d3587142aab4dd15f519c3407f",
        redirect_uri="http://localhost:8888/callback",
        scope="user-read-playback-state,user-modify-playback-state",
    )
)
# server neo4j
load_status = dotenv.load_dotenv("Neo4j-c95d3ee9-Created-2024-09-01.txt")
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
USR = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

config = {
    "graph_store": {
        "provider": "neo4j",
        "config": {"url": URI, "username": USR, "password": PASSWORD},
    },
    "version": "v1.1",
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

    # mem0.delete_all(user_id="mustafa_gumustas")
    # Retrieve relevant memories
    memories = mem0.search(messages[-1].content, user_id=user_id, limit=5)
    context = "Relevant information from previous conversations:\n"
    print(memories["entities"])
    # for memory in memories:
    #     context += f"- {memory['memory']}\n"
    #     print(memory["memory"])
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", drive_buddy_main_prompt + context),
            ("placeholder", "{chat_history}"),
            ("human", messages[-1].content),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    tools = [play_track_on_device]
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # system_message = SystemMessage(content=drive_buddy_main_prompt + context)
    # full_messages = [system_message] + messages

    # Invoke GPT with function calling enabled
    # response = agent_executor.invoke(full_messages)

    response = agent_executor.invoke(
        {
            "input": messages,
        }
    )
    return {"messages": [AIMessage(content=response["output"])]}


# Add nodes to the graph
graph.add_node("chatbot", chatbot)

# Add edge from START to chatbot
graph.add_edge(START, "chatbot")

# Add edge from chatbot back to itself
graph.add_edge("chatbot", "chatbot")

compiled_graph = graph.compile()


def run_conversation(user_input: str, mem0_user_id: str):
    config = {"configurable": {"thread_id": mem0_user_id}}
    state = {
        "messages": [HumanMessage(content=user_input)],
        "mem0_user_id": mem0_user_id,
    }

    for event in compiled_graph.stream(state, config):
        for value in event.values():
            if value.get("messages"):
                # print("\n\nDrive Buddy:", value)
                # recorder.gpt_speech(value["messages"][-1].content)
                return  # Exit after printing the response


if __name__ == "__main__":
    print("Welcome to Drive Buddy! How can I assist you today?\n")
    mem0_user_id = "mustafa_gumustas"
    while True:
        recorder = SpeechRecorder()
        try:
            # text = recorder.record()
            text = input("Enter your message: \n")

            # print(f"Transcribed text: {text}")
            # pprint(mem0.get_all())
            # recorder.close()
        finally:
            recorder.close()
        user_input = text

        if user_input.lower() in ["quit", "exit", "bye"]:
            print("\nDrive Buddy: Thank you for contacting us. Have a great day!")
            break
        else:
            run_conversation(user_input, mem0_user_id)

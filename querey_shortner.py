from openai import OpenAI

client = OpenAI()
import os
import openai
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
client = OpenAI()

# Retrieve API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OpenAI API key found in environment variables.")
embeddings = OpenAIEmbeddings(api_key=openai_api_key)

# Debug print to verify the API key
print(f"Using OpenAI API Key: {openai_api_key[:5]}...{openai_api_key[-5:]}")
# Initialize Pinecone client
pinecone_api_key = os.getenv("PINECONE_API_KEY")

if not pinecone_api_key:
    raise ValueError("No Pinecone API key found in environment variables.")

pc = Pinecone(api_key=pinecone_api_key)

# Connect to Pinecone index
if 'user1' not in pc.list_indexes().names():
    pc.create_index(
        name='user1', 
        dimension=1536, 
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
index = pc.Index('user1')
vector_store = Pinecone(index=index, embedding_function=embeddings.embed_query, text_key='text')

# sigarayi bu aralar cok ictigimi dusundugumden mi bilmiyorum ama cigerlerimn sagligi hakkinda endislenemeye basladim. balgam rengi vs beni cok tedirgin etti. hali hazirda zaten duzenli olarak haftada 1-2 gun kosuyorum ancak bunlar hep gruplarla beraber olan kosulardi. artik bireysel olarak da kosmam gerektigini dusunuyorum, sagligimi korumak icin. bana istanbulda kosabilecegim 3 rota soyler misin
class SpeechRecorder:
    def __init__(self):
        self.conversation_history = []
        self.raw_input = []
        self.user_personality = []

    def record(self):
        while True:
            user_text = input("You: "  )
            self.raw_input.append({"role": "user", "content": user_text})
            gpt_shortner_answer = self.shortner_gpt()
            gpt_shortner_answer = eval(gpt_shortner_answer)

            functional_data = gpt_shortner_answer["functional_data"]
            self.user_personality.append(functional_data)

            abbreviated_desired_action = gpt_shortner_answer['desired_action']
            self.conversation_history.append({"role": "assistant", "content": abbreviated_desired_action})

            response_text = self.gpt_response()
            self.conversation_history.append({"role": "assistant", "content": response_text})
            print(f"Response: {response_text}")

            # Upsert functional data into Pinecone
            user_id = "must"  # Replace with actual user ID logic
            self.upsert_functional_data(user_id, functional_data)
            # print(f"GPT Shortner Answer: {gpt_shortner_answer}\n")
            print(f"user personality: {self.user_personality}\n")
            # print(f"Abbreviated Desired Action: {abbreviated_desired_action}\n")


    def shortner_gpt(self):
        # this function will get personalized analysis of the user and shorten the input
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Your job is to analyze the input\
                  that user given.  First, separate and store functional and \
                 useful data related to the user's characteristics and personal\
                  informations.  Second, analyze the input again and take out \
                 the unnecessary parts from the input, just keep the parts that\
                  related to the desired action. In the output,  first, give the\
                  user's functional data that you keep at the first stage to \
                 store as a list,  second, give the abbreviated desired action \
                 text that you made at the second stage. This input will be \
                 using for another custom GPT. Use dictionary format for the \
                 output. In that dictionary use below format as example, : 
                 "functional_data": {
                    "bad_habit_frequancy": "low",
                    "concern": "high stress",
                    "sputum_color": "worries
                    "current_activity": "taking art classes",
                    "desire": "becoming an artist"
                }
                "desired_action": "Make user a list of things to do" , do not \
                 stick to the text inside this format just use the outline"""},
            ] + self.raw_input
        )
        self.raw_input = []
        print(f"Tokens used: {response.usage.total_tokens}")
        return response.choices[0].message.content

    def gpt_response(self):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
            ] + self.conversation_history
        )
        return response.choices[0].message.content

    def upsert_functional_data(self, user_id, functional_data):
        namespace = f"user_{user_id}_namespace"
        functional_data_str = str(functional_data)
        # Create an embedding for the functional data
        embedding_response = client.embeddings.create(input=functional_data_str, model="text-embedding-ada-002")
        embedding = embedding_response.data[0].embedding

        # Upsert the embedding and metadata into Pinecone
        index.upsert(
        vectors=[
            {
                "id": f"{user_id}_{hash(functional_data_str)}",  # Ensure a unique ID for each entry
                "values": embedding,
                "metadata": functional_data
            }
        ],
        namespace=namespace
    )

    

    def retrieve_and_print_metadata(self, user_id):
        namespace = f"user_{user_id}_namespace"

        # Query Pinecone for the given user_id
        result = index.query(
            vector=None,  # Set to None because we only want to retrieve by ID
            id=user_id,
            namespace=namespace,
            top_k=1,
            include_metadata=True
        )

        # Print the metadata
        if result and 'matches' in result:
            for match in result['matches']:
                print(f"ID: {match['id']}")
                print(f"Metadata: {match['metadata']}")
        else:
            print("No data found.")




if __name__ == "__main__":
    recorder = SpeechRecorder()
    recorder.record()





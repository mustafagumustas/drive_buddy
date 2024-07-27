import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load spaCy model
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

            gpt_shortner_answer = self.shortner_gpt(user_text)
            print(f"GPT Shortner Answer: {gpt_shortner_answer}\n")


            gpt_shortner_answer = eval(gpt_shortner_answer)
            functional_data = gpt_shortner_answer["functional_data"]

            self.user_personality.append(functional_data)
            print(f"user personality: {self.user_personality}\n")

            abbreviated_desired_action = gpt_shortner_answer['desired_action']
            self.conversation_history.append({"role": "assistant", "content": abbreviated_desired_action})
            print(f"Abbreviated Desired Action: {abbreviated_desired_action}\n")
            response_text = self.gpt_response()

            print(f"Response: {response_text}")
            self.conversation_history.append({"role": "assistant", "content": response_text})

    def shortner_gpt(self, text):
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
                    "bad_habit_frequancy": "high",
                    "concern": "lung health",
                    "sputum_color": "worries",
                    "current_activity": "running 1-2 times a week in groups",
                    "desire": "to run individually for health"
                }
                "desired_action": "Istanbul'da koşu rotasi öner" , do not \
                 stick to the text inside this format just use the outline"""},
            ] + self.raw_input
        )
        self.raw_input = []
        return response.choices[0].message.content
    

    def gpt_response(self):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
            ] + self.conversation_history
        )
        return response.choices[0].message.content
    



if __name__ == "__main__":
    recorder = SpeechRecorder()
    recorder.record()





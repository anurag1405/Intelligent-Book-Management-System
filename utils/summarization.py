from .groq_client import client

def generate_summary(text):
    try:
        chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""I am deploying you as an book summarizer in my Intelligent Book Management Project.User will give you a 
                book summary please summarize it with tools available to you and keep it with in 200 words capturing 
                the whole concept of book summary. When you done summarization return only summary . 
                ###If you perform well you will get promoted to work as chat-bot of our project### 
                here is the summary:{text}""",
            }
        ],
        model="llama-3.1-8b-instant",
        )
        print(chat_completion.choices[0].message.content)
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
client = OpenAI()

async def gpt_call(prompt):
    response = client.responses.create(
        model="gpt-5-nano",
        input=prompt
    )

    print(response.output_text)

    return response.output_text
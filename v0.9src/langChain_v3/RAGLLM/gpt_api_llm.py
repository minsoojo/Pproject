from openai import OpenAI
import os

class GPTAPILLM:
    def __init__(self, model="gpt-4.1"):
        self.client = OpenAI(api_key=os.environ["AI_03_InfoVerse_API_KEY"])
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

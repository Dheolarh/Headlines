from openai import OpenAI
from config import OPENAI_API_KEY
from dotenv import load_dotenv
load_dotenv()
import os
import json

def load_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "config", "prompt.json")
    with open(prompt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data["template"]

GPT_PROMPT = load_prompt()

def classify_headline(headline, jmoney_context=None):
    client = OpenAI(api_key=OPENAI_API_KEY)
    # Compose context string for GPT
    context_str = ""
    if jmoney_context:
        context_str = "\nJMoney context for this ticker: "
        for k, v in jmoney_context.items():
            context_str += f"{k}: {v}, "
    prompt = GPT_PROMPT.format(headline=headline, context=context_str)
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                n=1,
                temperature=0
            )
            content = response.choices[0].message.content.strip()
            # Try to find JSON in response
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                result = json.loads(json_str)
                return result
        except Exception as e:
            print(f"[OpenAI Error] {e}")
    return {"category": "No News", "summary": "", "confidence": 0, "filter_decision": False}

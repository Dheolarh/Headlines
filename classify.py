from openai import OpenAI
from config import OPENAI_API_KEY

def classify_headline(headline):
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
Classify the following news headline into one of these categories:
- Positive Catalyst
- Negative Catalyst
- Neutral

Headline: "{headline}"

Respond ONLY with a valid JSON object, no explanation, no markdown, no extra text. Example format:
{{"category": "Positive Catalyst", "summary": "Short summary here.", "confidence": 8}}
Fields:
- category: just one of the category labels
- summary: a short summary (max 20 words)
- confidence: a score from 0 to 10 for catalyst strength
"""
    import json
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
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
    return {"category": "No News", "summary": "", "confidence": 0}

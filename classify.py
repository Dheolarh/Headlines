from openai import OpenAI
from config import OPENAI_API_KEY

def classify_headline(headline, jmoney_context=None):
    client = OpenAI(api_key=OPENAI_API_KEY)
    # Compose context string for GPT
    context_str = ""
    if jmoney_context:
        context_str = "\nJMoney context for this ticker: "
        for k, v in jmoney_context.items():
            context_str += f"{k}: {v}, "
    prompt = f"""
Classify and filter the following news headline into one of these categories:
- Positive Catalyst
- Negative Catalyst
- Neutral

Headline: "{headline}"
{context_str}

Given the JMoney context, decide if this headline is a strong actionable catalyst for trading. Respond ONLY with a valid JSON object, no explanation, no markdown, no extra text. Example format:
{{"category": "Positive Catalyst", "summary": "Short summary here.", "confidence": 8, "filter_decision": true}}
Fields:
- category: just one of the category labels
- summary: a short summary (max 20 words)
- confidence: a score from 0 to 10 for catalyst strength
- filter_decision: true if this headline should be considered a strong actionable catalyst given the JMoney context, false otherwise
"""
    import json
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

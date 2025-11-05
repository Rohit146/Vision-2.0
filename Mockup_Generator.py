import openai
import os

def generate_mockup(context, role="Business Analyst"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "❌ OPENAI_API_KEY not set. Please add it in your Streamlit Cloud secrets."
    openai.api_key = api_key

    prompt = f"""
You are a {role} AI assistant.
Use the data summary and prompt below to draft a professional business report or dashboard mockup.

{context}
"""
    response = openai.ChatCompletion.create(
        model="gpt-5",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

import asyncio
from openai import AsyncOpenAI
from app.utils.helpers import get_env

async def test():
    api_key = get_env("OPENAI_API_KEY", "")
    
    client_kwargs = {"api_key": api_key}
    model_name = "gemini-2.5-flash"
    client_kwargs["base_url"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    client = AsyncOpenAI(**client_kwargs)
    
    system_prompt = "You are DRCode AI. Be helpful."
    user_prompt = "which skills i need to improve based on my resume of python developer for a senior ml engineer role."
    
    print("Sending request...")
    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.7,
            max_tokens=500
        )
        print("Response object:", response)
        print("Finish reason:", response.choices[0].finish_reason)
        print("Content:", response.choices[0].message.content)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())

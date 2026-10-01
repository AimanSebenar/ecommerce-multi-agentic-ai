import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["OPENROUTER_BASE_URL"],
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

def get_model() -> str:
    return os.environ["OPENROUTER_MODEL"]
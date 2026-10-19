import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_local_client():
    return OpenAI(
        api_key=os.getenv("LOCAL_API_KEY"),
        base_url=os.getenv("LOCAL_BASE_URL"),
        timeout=10.0  # Таймаут, чтобы не ждать вечно, если LM Studio висит
    )

def get_cloud_client():
    return OpenAI(
        api_key=os.getenv("CLOUD_API_KEY"),
        base_url=os.getenv("CLOUD_BASE_URL"),
        default_headers={
            "HTTP-Referer": "http://localhost", # Требуется для OpenRouter
            "X-Title": "SibADI Lab 6"
        },
        timeout=30.0
    )

def get_models():
    return {
        "local": os.getenv("LOCAL_MODEL"),
        "cloud": os.getenv("CLOUD_MODEL")
    }

def check_connection(client, model_name, provider_name):
    """Отправляет минимальный запрос для проверки связи."""
    print(f"  Проверка связи с {provider_name} ({model_name})...", end=" ", flush=True)
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            temperature=0.0
        )
        if response.choices and response.choices[0].message.content:
            print("УСПЕШНО ✓")
            return True
        else:
            print("ОШИБКА: Пустой ответ ✗")
            return False
    except Exception as e:
        print(f"ОШИБКА ✗\n    Текст: {str(e)[:100]}")
        return False
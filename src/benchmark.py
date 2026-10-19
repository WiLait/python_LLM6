import os
import time
import json
import sys
import pandas as pd
from providers import get_local_client, get_cloud_client, get_models, check_connection
from dotenv import load_dotenv

load_dotenv()

# Тарифы (для облака)
PRICE_IN = float(os.getenv("PRICE_INPUT_1M", 0.0))
PRICE_OUT = float(os.getenv("PRICE_OUTPUT_1M", 0.0))

def ask_model(client, model_name, prompt, temperature=0.2):
    t0 = time.perf_counter()
    ttft = None
    full_text = ""
    out_tokens = 0
    in_tokens = 0
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": True}
        )
        
        for chunk in response:
            if ttft is None and chunk.choices and chunk.choices[0].delta.content:
                ttft = time.perf_counter() - t0
            
            if chunk.choices and chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content
            
            if hasattr(chunk, 'usage') and chunk.usage:
                in_tokens = chunk.usage.prompt_tokens
                out_tokens = chunk.usage.completion_tokens

        total_time = time.perf_counter() - t0
        cost = (in_tokens / 1_000_000) * PRICE_IN + (out_tokens / 1_000_000) * PRICE_OUT
        
        return {
            "text": full_text,
            "ttft": round(ttft, 3) if ttft else None,
            "latency_s": round(total_time, 3),
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
            "cost_usd": round(cost, 6),
            "error": None
        }
    except Exception as e:
        return {"text": None, "ttft": None, "latency_s": None, "error": str(e)}

def run():
    local_client = get_local_client()
    cloud_client = get_cloud_client()
    models = get_models()

    print("="*60)
    print("ПРОВЕРКА ОКРУЖЕНИЯ ПЕРЕД ЗАПУСКОМ")
    print("="*60)
    
    # 1. Проверка локальной модели
    if not check_connection(local_client, models['local'], "Локальной моделью"):
        print("\n[STOP] Запуск остановлен. Убедитесь, что LM Studio запущен и модель загружена.")
        sys.exit(1)
        
    # 2. Проверка облачной модели
    if not check_connection(cloud_client, models['cloud'], "Облачной моделью (OpenRouter)"):
        print("\n[STOP] Запуск остановлен. Проверьте API-ключ и баланс.")
        sys.exit(1)

    print("\n" + "="*60)
    print("ВСЁ ГОТОВО. НАЧИНАЕМ ТЕСТИРОВАНИЕ")
    print("="*60)

    # Загрузка тестов
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_path = os.path.join(base_dir, "data", "test_cases.json")
    
    with open(test_path, "r", encoding="utf-8") as f:
        tests = json.load(f)

    results = []

    for test in tests:
        print(f"\n[{test['id']}] {test['type'].upper()}")
        
        # 1. Локальная
        print(f"  -> Локальная...", end=" ", flush=True)
        res_loc = ask_model(local_client, models['local'], test["prompt"])
        if res_loc["error"]:
            print(f"ОШИБКА: {res_loc['error'][:40]}")
        else:
            print(f"OK (TTFT: {res_loc['ttft']}с, Время: {res_loc['latency_s']}с)")
        
        results.append({
            "test_id": test["id"], "type": test["type"], "provider": "local",
            "model": models['local'], "prompt": test["prompt"],
            "ttft": res_loc.get("ttft"), "latency_s": res_loc.get("latency_s"),
            "in_tokens": res_loc.get("in_tokens"), "out_tokens": res_loc.get("out_tokens"),
            "cost_usd": 0.0, "answer": res_loc.get("text"), "error": res_loc.get("error")
        })

        # 2. Облачная
        print(f"  -> Облачная...", end=" ", flush=True)
        res_clo = ask_model(cloud_client, models['cloud'], test["prompt"])
        if res_clo["error"]:
            print(f"ОШИБКА: {res_clo['error'][:40]}")
        else:
            print(f"OK (TTFT: {res_clo['ttft']}с, Время: {res_clo['latency_s']}с, Cost: ${res_clo['cost_usd']})")
            
        results.append({
            "test_id": test["id"], "type": test["type"], "provider": "cloud",
            "model": models['cloud'], "prompt": test["prompt"],
            "ttft": res_clo.get("ttft"), "latency_s": res_clo.get("latency_s"),
            "in_tokens": res_clo.get("in_tokens"), "out_tokens": res_clo.get("out_tokens"),
            "cost_usd": res_clo.get("cost_usd"), "answer": res_clo.get("text"), "error": res_clo.get("error")
        })

    # Сохранение
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "raw_results.csv")
    
    df = pd.DataFrame(results)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ Результаты сохранены в {out_path}")
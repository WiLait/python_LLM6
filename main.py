import sys
import os
import subprocess

def main():
    print("="*50)
    print("ЛАБОРАТОРНАЯ РАБОТА №6")
    print("Сравнение локальной и облачной LLM")
    print("="*50)
    
    print("\nДоступные действия:")
    print("  [1] Запустить полный бенчмарк (20 тестов)")
    print("  [2] Запустить только проверку подключения")
    print("  [0] Выход")

    if len(sys.argv) > 1:
        choice = sys.argv[1].strip()
    else:
        choice = input("\nВыберите действие: ").strip()

    if choice == "1":
        # Запускаем benchmark.py как отдельный процесс
        script_path = os.path.join("src", "benchmark.py")
        subprocess.run([sys.executable, script_path], check=True)
    elif choice == "2":
        # Запускаем только проверку
        sys.path.append(os.path.join(os.getcwd(), "src"))
        from providers import get_local_client, get_cloud_client, get_models, check_connection
        
        models = get_models()
        print("\n--- Проверка подключений ---")
        check_connection(get_local_client(), models['local'], "Локальной моделью")
        check_connection(get_cloud_client(), models['cloud'], "Облачной моделью (OpenRouter)")
    elif choice == "0":
        sys.exit(0)
    else:
        print("Неверный выбор.")
        sys.exit(1)

if __name__ == "__main__":
    main()
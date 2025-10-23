import os

def list_algorithms():
    algo_dir = os.path.join(os.path.dirname(__file__), "algorithms")
    algos = [f.replace(".c", "") for f in os.listdir(algo_dir) if f.endswith(".c")]
    print("\n".join(algos))

def get_algorithm(name):
    algo_dir = os.path.join(os.path.dirname(__file__), "algorithms")
    file_path = os.path.join(algo_dir, f"{name}.c")
    if not os.path.exists(file_path):
        print(f"❌ Algorithm '{name}' not found. Use: algoinc list")
        return
    with open(file_path, "r", encoding="utf-8") as f:
        print(f.read())

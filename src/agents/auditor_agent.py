# src/agents/auditor_agent.py

def load_prompt():
    with open("src/prompts/auditor_prompt.txt", "r", encoding="utf-8") as file:
        prompt = file.read()
    return prompt

def run_auditor_agent(code_to_analyze):
    prompt = load_prompt()
    # Ici, tu enverras 'prompt' + 'code_to_analyze' à ton LLM (modèle IA)
    # Pour l'instant, on imprime pour vérifier
    print("=== Prompt envoyé à l'agent Auditeur ===")
    print(prompt)
    print("=== Code à analyser ===")
    print(code_to_analyze)

if __name__ == "__main__":
    example_code = "def foo():\n    return 42"
    run_auditor_agent(example_code)

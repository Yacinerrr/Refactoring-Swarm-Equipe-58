import json
from src.utils.log_helpers import log_fix  # ✅ Use the correct function


def run_corrector_agent(
    audit_plan: dict,
    target_code: str,
    target_file: str,
    model_used: str = "gemini-2.5-flash"
) -> dict:
    """
    Corrects code according to the refactoring plan produced by the Auditor agent.
    """

    # Load prompt directly (no split)
    with open("src/prompts/corrector_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    input_prompt = f"""{system_prompt}

=== REFACTORING PLAN ===
{json.dumps(audit_plan, indent=2, ensure_ascii=False)}

=== FILE TO FIX ===
{target_file}

```python
{target_code}
```

Respond ONLY in JSON format with the corrected code.
"""

    # 🔧 LLM RESPONSE (placeholder – replace with real model call)
    output_response = json.dumps(
        {
            "file": target_file,
            "status": "modified",
            "changes": [
                {
                    "type": "refactor",
                    "description": "Changes applied according to auditor plan"
                }
            ],
            "modified_code": target_code  # This should contain the actual fixed code
        },
        indent=2,
        ensure_ascii=False
    )

    # Parse output
    try:
        result = json.loads(output_response)
        success = True
    except json.JSONDecodeError as e:
        result = {
            "file": target_file,
            "status": "error",
            "error": str(e)
        }
        success = False

    # ✅ CORRECT LOGGER FOR CORRECTOR/FIXER
    log_fix(
        model=model_used,
        input_prompt=input_prompt,
        output_response=output_response,
        file_fixed=target_file,
        issues_fixed=[action["description"] for action in audit_plan.get("files_to_fix", [{}])[0].get("actions", [])],
        success=success
    )

    return result


if __name__ == "__main__":
    # Minimal local test
    audit_plan_example = {
        "summary": "Example audit",
        "files_to_fix": [
            {
                "file": "example.py",
                "priority": "medium",
                "actions": [
                    {"type": "improve_quality", "description": "Remove unused variable"}
                ]
            }
        ]
    }
    
    target_code_example = """
def foo():
    x = 1  # Variable non utilisée
    return 42
"""
    
    result = run_corrector_agent(
        audit_plan=audit_plan_example,
        target_code=target_code_example,
        target_file="example.py"
    )
    
    print("\n=== Résultat du Corrector ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
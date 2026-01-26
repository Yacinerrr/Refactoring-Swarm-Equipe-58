import json
from src.utils.analysis_tools import run_pytest
from src.utils.log_helpers import log_test_execution  # ✅ Use the correct function


def load_prompt():
    """Load the system prompt for the Tester agent."""
    with open("src/prompts/tester_prompt.txt", "r", encoding="utf-8") as file:
        return file.read()


def run_tester_agent(
    target_dir: str,
    model_used: str = "gemini-2.5-flash"
) -> dict:
    """
    Runs pytest and evaluates results.
    """

    system_prompt = load_prompt()

    print(f"🧪 Running pytest on {target_dir}...")
    pytest_results = run_pytest(target_dir)

    total_tests = len(pytest_results)
    failed_tests = [r for r in pytest_results if r.get("test_error")]

    if total_tests == 0:
        test_status = "no_tests"
        action = "return_to_corrector"
    elif failed_tests:
        test_status = "failure"
        action = "return_to_corrector"
    else:
        test_status = "success"
        action = "validate"

    input_prompt = f"""{system_prompt}

=== PYTEST RESULTS ===
Target directory: {target_dir}
Total tests: {total_tests}
Failed tests: {len(failed_tests)}

{json.dumps(pytest_results, indent=2, ensure_ascii=False)}

Respond ONLY in JSON.
"""

    output_response = json.dumps(
        {
            "test_status": test_status,
            "failed_tests": failed_tests,
            "action": action,
            "summary": (
                "All tests passed"
                if test_status == "success"
                else f"{len(failed_tests)}/{total_tests} tests failed"
            ),
        },
        indent=2,
        ensure_ascii=False
    )

    # ✅ CORRECT LOGGER FOR TESTER/JUDGE
    log_test_execution(
        model=model_used,
        input_prompt=input_prompt,
        output_response=output_response,
        tests_passed=total_tests - len(failed_tests),
        tests_failed=len(failed_tests),
        test_output=json.dumps(pytest_results, indent=2),
        success=test_status == "success",
        target_dir=target_dir,
        files_analyzed=total_tests,
        analysis_tool_results=pytest_results
    )

    return json.loads(output_response)


if __name__ == "__main__":
    print(
        json.dumps(
            run_tester_agent("./sandbox/example"),
            indent=2,
            ensure_ascii=False
        )
    )
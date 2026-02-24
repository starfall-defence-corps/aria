#!/usr/bin/env python3
"""
ARIA — Automated Review & Intelligence Analyst
Standalone review script. Runs deterministic tests for a mission,
then sends results to LLM for qualitative review.

Usage:
    python aria-review.py --mission 1-1 --mission-root /path/to/mission-repo

Requires:
    ANTHROPIC_API_KEY environment variable (optional — skips LLM review if absent)
"""
import argparse
import os
import subprocess
import sys


MISSION_MAP = {
    "1-1": {
        "test": "molecule/default/tests/test_fleet_census.py",
        "student_files": [
            "workspace/inventory/hosts.yml",
            "workspace/ansible.cfg",
        ],
    },
}


def _mission_root(mission_root_override=None):
    """Return the mission repo root directory."""
    if mission_root_override:
        return os.path.abspath(mission_root_override)
    return os.getcwd()


def _run_tests(mission_id, mission_root_override=None):
    """Run pytest for the specified mission and capture output."""
    mission_dir = _mission_root(mission_root_override)
    config = MISSION_MAP[mission_id]
    test_path = os.path.join(mission_dir, config["test"])

    # Activate venv if present
    venv_python = os.path.join(mission_dir, "venv", "bin", "python3")
    python_cmd = venv_python if os.path.isfile(venv_python) else sys.executable

    result = subprocess.run(
        [python_cmd, "-m", "pytest", test_path, "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=mission_dir,
    )
    return result.returncode, result.stdout, result.stderr


def _read_student_files(mission_id, mission_root_override=None):
    """Read student workspace files for LLM context."""
    mission_dir = _mission_root(mission_root_override)
    config = MISSION_MAP[mission_id]
    files = {}

    for rel_path in config["student_files"]:
        full_path = os.path.join(mission_dir, rel_path)
        if os.path.isfile(full_path):
            with open(full_path) as f:
                files[rel_path] = f.read()
        else:
            files[rel_path] = "(file does not exist)"

    return files


def _load_prompts(mission_id):
    """Load base system prompt + mission-specific context."""
    aria_dir = os.path.dirname(os.path.abspath(__file__))

    base_path = os.path.join(aria_dir, "system-prompt.md")
    with open(base_path) as f:
        base_prompt = f.read()

    mission_path = os.path.join(aria_dir, "missions", f"mission-{mission_id}.md")
    with open(mission_path) as f:
        mission_context = f.read()

    return f"{base_prompt}\n\n---\n\n{mission_context}"


def _build_user_message(test_exit_code, test_stdout, test_stderr, student_files):
    """Construct the user message with all context for LLM review."""
    parts = []

    parts.append("## Test Results")
    parts.append(
        f"Exit code: {test_exit_code} "
        f"({'PASSED' if test_exit_code == 0 else 'FAILED'})"
    )
    parts.append("")
    parts.append("```")
    parts.append(test_stdout.strip())
    if test_stderr.strip():
        parts.append("")
        parts.append("STDERR:")
        parts.append(test_stderr.strip())
    parts.append("```")
    parts.append("")

    parts.append("## Student Files")
    for filename, content in student_files.items():
        parts.append(f"### {filename}")
        parts.append("```yaml")
        parts.append(content.strip())
        parts.append("```")
        parts.append("")

    parts.append("## Task")
    parts.append("Review this cadet's submission. Follow your review format.")

    return "\n".join(parts)


def _call_llm(system_prompt, user_message):
    """Call Anthropic API for ARIA review."""
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def main():
    parser = argparse.ArgumentParser(description="ARIA Mission Review")
    parser.add_argument(
        "--mission",
        required=True,
        choices=list(MISSION_MAP.keys()),
        help="Mission ID (e.g., 1-1)",
    )
    parser.add_argument(
        "--mission-root",
        default=None,
        help="Path to the mission repo root (defaults to CWD)",
    )
    parser.add_argument(
        "--output",
        help="Write review to file instead of stdout",
    )
    args = parser.parse_args()

    print()
    print("==============================================")
    print("  ARIA - Automated Review & Intelligence Analyst")
    print(f"  Running Mission {args.mission} Verification...")
    print("==============================================")
    print()

    # Phase 1: Deterministic tests
    test_exit_code, test_stdout, test_stderr = _run_tests(
        args.mission, args.mission_root
    )

    # Display test results with ARIA theming
    themed_output = test_stdout.replace("PASSED", "VERIFIED").replace(
        "FAILED", "DEFICIENCY DETECTED"
    )
    print(themed_output)

    review_text = ""

    # Phase 2: LLM review (if API key available)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print()
        print("----------------------------------------------")
        print("  ARIA qualitative review: SKIPPED")
        print("  (No ANTHROPIC_API_KEY configured)")
        print("  Set the key as a repo secret for PR reviews")
        print("  or export locally for ad-hoc feedback.")
        print("----------------------------------------------")
    else:
        try:
            system_prompt = _load_prompts(args.mission)
            student_files = _read_student_files(
                args.mission, args.mission_root
            )
            user_message = _build_user_message(
                test_exit_code, test_stdout, test_stderr, student_files
            )
            review_text = _call_llm(system_prompt, user_message)

            print()
            print("==============================================")
            print("  ARIA QUALITATIVE REVIEW")
            print("==============================================")
            print()
            print(review_text)
        except Exception as e:
            print()
            print("----------------------------------------------")
            print(f"  ARIA review error: {e}")
            print("  Deterministic test results remain valid.")
            print("----------------------------------------------")

    # Write to file if requested (for GitHub Actions)
    if args.output:
        with open(args.output, "w") as f:
            f.write(themed_output)
            if review_text:
                f.write("\n\n## ARIA QUALITATIVE REVIEW\n\n")
                f.write(review_text)

    # Final banner
    print()
    if test_exit_code == 0:
        print("==============================================")
        print("  ARIA: All objectives verified.")
        print(f"  Mission {args.mission} status: COMPLETE")
        print("==============================================")
    else:
        print("==============================================")
        print("  ARIA: Deficiencies detected.")
        print("  Review the output above and correct.")
        print("  Run 'make test' again when ready.")
        print("==============================================")
    print()

    sys.exit(test_exit_code)


if __name__ == "__main__":
    main()

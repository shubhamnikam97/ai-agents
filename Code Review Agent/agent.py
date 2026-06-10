"""
Code Review Agent using LangChain.

Reviews Python code for bugs, security issues, style violations, and
suggests improvements. Accepts a file path or inline code snippet.

Usage:
    python agent.py --file path/to/code.py
    python agent.py --code "def add(a,b): return a+b"
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv()

SYSTEM_PROMPT = """
You are a expert code reviewer. Analyze the provided code and return a structured review covering:

1. **Bugs & Correctness** — logic errors, edge cases, exception handling
2. **Security Issues** — injection risks, secrets exposure, unsafe operations
3. **Performance** — inefficiencies, unnecessary computation, memory issues
4. **Code Style** — PEP 8 violations, naming conventions, readability
5. **Improvements** — refactoring suggestions, better patterns

Format: Use markdown. Rate overall quality as: 🟢 Good / 🟡 Needs Work / 🔴 Critical Issues.
"""

def review_code(code: str, language: str = "python") -> str:
    llm = ChatOpenAI(model ="gpt-4o-mini", temperature=0)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Review this {language} code:\n\n```{language}\n{code}\n```"),
    ]
    response = llm.invoke(messages)
    return response.content


def save_review_markdown(review: str, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(review)


def save_review(review: str, output_path: str) -> None:
    ext = os.path.splitext(output_path)[1].lower()
    if ext == ".md":
        save_review_markdown(review, output_path)
    else:
        raise ValueError("Output file must use .md extension.")


def main():
    parser = argparse.ArgumentParser(description="Code Review Agent")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to the code file to review")
    group.add_argument("--code", help="Inline code snippet to review")
    parser.add_argument("--language", default="python", help="Programming language of the code (default: python)")
    parser.add_argument("--output", "-o", help="Save review to a .md file")
    args = parser.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            code = f.read()
            print(f"\n🔍 Reviewing: {args.file}\n")
    else:
        code = args.code
        print("\n🔍 Reviewing inline code snippet\n")

    review = review_code(code, args.language)

    if args.output:
        save_review(review, args.output)
        print(f"\n✅ Saved review to {args.output}\n")

    print("=" * 60)
    print("📋 CODE REVIEW")
    print("=" * 60)
    print(review)

if __name__ == "__main__":
    main()
"""
Web Research Agent using LangGraph + Tavily Search.

Searches the web for a given topic, synthesizes findings, and returns
a structured research report.

Usage:
    python agent.py
    python agent.py --query "latest advances in quantum computing"
"""

import argparse
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langchain_community.tools import DuckDuckGoSearchRun


load_dotenv()

class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    search_results: list[str]
    report: str

# def search_web(state: ResearchState) -> ResearchState:
#     tool = TavilySearch(max_results=5)
#     raw_results = tool.invoke(state['query'])
#     if isinstance(raw_results, dict):
#         results = raw_results.get('results', [])
#     elif isinstance(raw_results, list):
#         results = raw_results
#     else:
#         results = []
#     return {"research_results": results}

def normalize_results(raw_results):
    if isinstance(raw_results, dict):
        return raw_results.get("results", raw_results.get("data", []))
    if isinstance(raw_results, list):
        return raw_results
    if isinstance(raw_results, str):
        return [{"url": "", "title": "Search results", "content": raw_results}]
    return []

def search_with_tavily(query: str):
    tool = TavilySearch(max_results=5)
    raw_results = tool.invoke(query)
    return normalize_results(raw_results)

def search_with_duckduckgo(query: str):
    tool = DuckDuckGoSearchRun(name="Search")
    if hasattr(tool, "run"):
        raw_results = tool.run(query)
    elif hasattr(tool, "search"):
        raw_results = tool.search(query)
    else:
        raise RuntimeError("DuckDuckGoSearchRun has no run/search method")

    return normalize_results(raw_results)

def search_web(state: ResearchState) -> ResearchState:
    query = state["query"]

    try:
        results = search_with_tavily(query)
        if results:
            print("✅ Using TavilySearch")
            return {"search_results": results}
    except Exception as exc:
        print(f"⚠️ TavilySearch failed: {exc}")

    try:
        results = search_with_duckduckgo(query)
        if results:
            print("✅ Fallback to DuckDuckGoSearchAPIWrapper")
            return {"search_results": results}
    except Exception as exc:
        print(f"⚠️ DuckDuckGo fallback failed: {exc}")

    raise RuntimeError("All search providers failed. Install DuckDuckGoSearchAPIWrapper or add another fallback.")

def synthesize_report(state: ResearchState) -> ResearchState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    result_text = "\n\n".join(
        f"Source: {r.get('url', 'N/A')}\nTitle: {r.get('title', 'N/A')}\nContent: {r.get('content', '')[:500]}"
        for r in state["search_results"]
    )

    messages = [
        SystemMessage(content="You are a research analyst. Synthesize the search results into the clear, structured report with: Summary, Key Findings (bullet points), and Sources"),
        HumanMessage(content=f"Research query: {state['query']}\n\nSearch results:\n{result_text}"),
    ]

    # response = llm(messages)
    response = llm.invoke(messages)
    return {"report": response.content, "messages": [response]}


def save_report_markdown(report: str, query: str, filename: str = "research_report.md") -> None:
    markdown = [
        "# Research Report",
        "",
        f"**Query:** {query}",
        "",
        "## Report",
        "",
        report,
    ]
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown))
    print(f"\n✅ Saved markdown output to {filename}")


def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)
    graph.add_node("search", search_web)
    graph.add_node("synthesize", synthesize_report)
    graph.set_entry_point("search")
    graph.add_edge("search", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()

def main():
    parser = argparse.ArgumentParser(description="Web Research Agent")
    parser.add_argument("--query", default="latest advances in AI agents 2026", help="Research query")
    args = parser.parse_args()

    print(f"\n🔍 Researching: {args.query}\n")

    agent = build_graph()
    result = agent.invoke({"query": args.query, "messages": [], "search_results": [], "report": ""})
    print("=" * 60)
    print("📄 RESEARCH REPORT")
    print("=" * 60)
    print(result["report"])
    save_report_markdown(result["report"], args.query)

if __name__ == "__main__":
    main()
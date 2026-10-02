"""News retrieval pipeline with tools and agents"""

import json
import os
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import Tool, StructuredTool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from core.config import MODEL_NAME, LLM_MAX_TOKENS, AGENT_RECURSION_LIMIT, MAX_INTERESTS, USE_AGENT
from core.models import ExpandSearchQueriesInput, SearchInput, CredibilityInput, SummarizeInput
from utils.database import fetch_interests
from utils.search import ddg_search
from utils.formatting import filter_with_llm, summarize_news
from utils.llm import safe_llm_call, RateLimitedChatGroq

groq_api_key = os.environ.get("GROQ_API_KEY", "")
llm = RateLimitedChatGroq(
    model=MODEL_NAME,
    temperature=0,
    max_tokens=LLM_MAX_TOKENS,
    max_retries=0,
    groq_api_key=groq_api_key,
)

def expand_search_queries(interests: List[str], user_query: str) -> str:
    """Expand user interests into search queries"""
    if isinstance(interests, str):
        interests = [i.strip() for i in interests.split(",") if i.strip()]
    
    interests = [i[:60] for i in interests][:MAX_INTERESTS]
    if not interests:
        return json.dumps([])
    
    system_prompt = "You are a search query expansion tool. Generate time-sensitive news search queries from interests. Output: JSON array. No commentary."
    prompt = f"Interests: {json.dumps(interests)}\nUser focus: {user_query}"
    
    raw = safe_llm_call([SystemMessage(content=system_prompt), HumanMessage(content=prompt)])
    
    queries = []
    import re
    match = re.search(r"\[.*?\]", raw, re.S)
    if match:
        try:
            parsed = json.loads(match.group(0))
            queries = [str(q).strip() for q in parsed if str(q).strip()]
        except json.JSONDecodeError:
            pass
    
    if not queries:
        queries = [f"{i} latest news" for i in interests]
    
    return json.dumps(queries[:MAX_INTERESTS])

expand_tool = StructuredTool.from_function(
    func=expand_search_queries,
    name="ExpandSearchQueries",
    description="Expand interests into search queries. Input: interests list, user query. Output: JSON array.",
    args_schema=ExpandSearchQueriesInput,
)

ddg_search_tool = StructuredTool.from_function(
    func=ddg_search,
    name="DuckDuckGoSearch",
    description="Search DuckDuckGo News. Input: query string. Output: JSON array with title, url, body, date.",
    args_schema=SearchInput,
)

credibility_tool = StructuredTool.from_function(
    func=filter_with_llm,
    name="CredibilityFilter",
    description="Filter sources by credibility. Input: search results. Output: JSON array of credible sources.",
    args_schema=CredibilityInput,
)

summarize_tool = StructuredTool.from_function(
    func=summarize_news,
    name="SummarizeNews",
    description="Summarize credible sources. Input: filtered sources. Output: news briefing with citations.",
    args_schema=SummarizeInput,
)

def build_agent(model, tool_list, system_message):
    """Create ReAct agent with version compatibility"""
    try:
        return create_react_agent(model, tool_list, prompt=system_message)
    except TypeError:
        return create_react_agent(model, tool_list, state_modifier=system_message)

news_tools = [expand_tool, ddg_search_tool, credibility_tool, summarize_tool]

agent_system_message = """You are a news research assistant with four tools:
ExpandSearchQueries, DuckDuckGoSearch, CredibilityFilter, SummarizeNews.

Follow this order exactly:
1. ExpandSearchQueries once
2. DuckDuckGoSearch once per query
3. CredibilityFilter once
4. SummarizeNews once
5. Return the summary as final answer

Never invent URLs or details. Copy tool outputs verbatim.
"""

agent = build_agent(llm, news_tools, agent_system_message)

def run_pipeline_directly(interests: List[str], user_query: str) -> str:
    """Direct pipeline without agent"""
    queries = json.loads(expand_search_queries(interests, user_query))
    print(f"Queries: {queries}")
    
    combined = []
    for q in queries:
        results = ddg_search(q)
        combined.extend(results if isinstance(results, list) else [])
    print(f"Raw results: {len(combined)}")
    
    filtered = filter_with_llm(combined)
    print(f"Filtered sources")
    
    return summarize_news(filtered)

def query_response(email: str, user_query: str, use_agent: Optional[bool] = None) -> str:
    """Main pipeline: Email → Interests → Search → Filter → Summary"""
    use_agent = USE_AGENT if use_agent is None else use_agent
    
    interests = fetch_interests(email, use_agent=use_agent)
    if not interests:
        return f"No interests found for {email}"
    
    print(f"Interests: {interests}")
    
    if not use_agent:
        return run_pipeline_directly(interests, user_query)
    
    agent_prompt = (
        f"User interests: {json.dumps(interests)}\n"
        f"User query: {user_query}\n"
        "Run the four-step process and return the final summary."
    )
    
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=agent_prompt)]},
            config={"recursion_limit": AGENT_RECURSION_LIMIT},
        )
        final = result["messages"][-1].content
        if not final.strip():
            raise ValueError("empty response")
        return final
    
    except Exception as e:
        print(f"Agent failed - using direct pipeline")
        return run_pipeline_directly(interests, user_query)

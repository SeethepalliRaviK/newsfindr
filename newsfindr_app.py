"""NewsFindr Streamlit Web Application"""

import streamlit as st
import os
from core.pipeline import query_response
from utils.database import get_all_emails

st.set_page_config(
    page_title="NewsFindr Assistant",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📰 NewsFindr Assistant")
st.markdown("*AI-Powered Personalized News Retrieval*")

with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("API Configuration")
    groq_key = st.text_input("GROQ_API_KEY", type="password", value=os.environ.get("GROQ_API_KEY", ""))
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    
    use_agent = st.checkbox("Use AI Agent (vs Direct Pipeline)", value=True)
    st.caption("Agent: More reasoning, slower. Direct: Faster, deterministic.")

st.subheader("Select User & Search")

col1, col2 = st.columns(2)

with col1:
    all_emails = get_all_emails()
    selected_email = st.selectbox(
        "Select User Email:",
        options=all_emails,
        key="email_select"
    )

with col2:
    user_query = st.text_input(
        "Enter News Query:",
        placeholder="e.g., latest developments, market trends, tech news",
        key="query_input"
    )

if st.button("🔍 Search News", type="primary", use_container_width=True):
    if not os.environ.get("GROQ_API_KEY"):
        st.error("❌ GROQ_API_KEY not configured. Add it in Settings.")
    elif not selected_email:
        st.error("❌ Please select a user.")
    elif not user_query:
        st.error("❌ Please enter a news query.")
    else:
        st.info("🔄 Processing your request...")
        
        with st.spinner("Expanding interests..."):
            try:
                result = query_response(selected_email, user_query, use_agent=use_agent)
                
                st.success("✅ News Summary Generated!")
                st.markdown("---")
                st.markdown(result)
                
                st.markdown("---")
                st.caption(f"📧 User: {selected_email} | 🤖 Agent: {'Yes' if use_agent else 'No'}")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Make sure GROQ_API_KEY is set and DuckDuckGo is accessible.")

st.markdown("---")
st.markdown("""
### About NewsFindr
- **Database**: SQLite customer profiles with interests
- **Search**: DuckDuckGo News with retry logic
- **Filtering**: LLM-powered credibility assessment
- **Summary**: AI-generated news briefing with citations

### How It Works
1. Select a user to load their interests
2. Enter what news you're interested in
3. System expands interests into search queries
4. Searches news across the web
5. Filters by credibility
6. Generates personalized summary
""")

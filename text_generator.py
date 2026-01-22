from langchain_core.messages import HumanMessage

def generate_text(topic: str) -> str:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",   # ✅ stable & supported
            temperature=0.7,
            api_key=st.secrets["GEMINI_API_KEY"],
        )

        message = HumanMessage(
            content=f"""
Write a professional and engaging LinkedIn post (100–120 words) about:
"{topic}"

Tone: professional, inspiring, positive.
"""
        )

        response = llm.invoke([message])   # ✅ MUST be a list
        return response.content

    except Exception as e:
        st.error(f"Gemini error: {e}")
        return "❌ Failed to generate content. Please try again."

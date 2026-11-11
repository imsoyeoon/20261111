
import streamlit as st
from pathlib import Path

st.title("국립부경대학교 도서관 챗봇")
st.write("도서관 규정에 대해 질문해 보세요.")

# 기존 OpenAI 클라이언트 가져오기
client = st.session_state.get("openai_client")

# 도서관 규정 불러오기
rules_path = Path(__file__).with_name("library_rules.txt")
library_rules = rules_path.read_text(encoding="utf-8")

# AI에게 전달할 지시문
instructions = f"""
당신은 국립부경대학교 도서관 안내 챗봇입니다.
아래 도서관 규정을 바탕으로 질문에 답변하세요.

규정에서 확인되지 않는 내용은 추측하지 말고
"제공된 규정에서 확인할 수 없습니다."라고 답변하세요.

가능하면 관련 조항도 함께 알려주세요.

[도서관 규정]
{library_rules}
"""

# 채팅 기록 초기화
if "library_messages" not in st.session_state:
    st.session_state.library_messages = []

# 대화 삭제 함수
def clear_chat():
    st.session_state.library_messages = []

st.button("Clear", on_click=clear_chat)

# 이전 대화 표시
for msg in st.session_state.library_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 새로운 질문
if prompt := st.chat_input("도서관에 대해 질문하세요"):
    st.session_state.library_messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    if client is None:
        with st.chat_message("assistant"):
            st.warning("사이드바에 API Key를 입력해주세요.")
    else:
        with st.chat_message("assistant"):
            stream = client.responses.create(
                model="gpt-6-luna",
                instructions=instructions,
                input=st.session_state.library_messages,
                stream=True
            )

            response = st.write_stream(stream)

        st.session_state.library_messages.append({
            "role": "assistant",
            "content": response
        })

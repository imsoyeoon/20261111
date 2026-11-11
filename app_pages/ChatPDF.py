import re
import streamlit as st

st.title("ChatPDF")
st.write("PDF 파일을 업로드하고 내용을 질문해 보세요.")

# OpenAI 클라이언트 가져오기
client = st.session_state.get("openai_client")

# 세션 상태 초기화
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []

if "pdf_vector_store_id" not in st.session_state:
    st.session_state.pdf_vector_store_id = None

if "pdf_answer_cache" not in st.session_state:
    st.session_state.pdf_answer_cache = {}

def clean_citations(text):
    text = re.sub(r"filecite.*?", "", text)
    text = re.sub(
        r"�filecite�(?:turn\d+file\d+�?)+",
        "",
        text
    )
    text = re.sub(r"【\d+†[^】]+】", "", text)
    return text.strip()

# 대화 삭제 함수
def clear_chat():
    st.session_state.pdf_messages = []


# PDF가 아직 준비되지 않은 경우
if st.session_state.pdf_vector_store_id is None:

    uploaded_file = st.file_uploader(
        "PDF 파일을 선택하세요",
        type=["pdf"],
        accept_multiple_files=False
    )

    if uploaded_file is not None:

        if client is None:
            st.warning("사이드바에 API Key를 입력해주세요.")

        elif st.button("PDF 준비하기"):
            vector_store = None

            try:
                with st.spinner("PDF 파일을 처리하고 있습니다..."):

                    # Vector Store 생성
                    vector_store = client.vector_stores.create(
                        name="ChatPDF",
                        expires_after={
                            "anchor": "last_active_at",
                            "days": 1
                        }
                    )

                    # PDF 업로드 및 검색 준비
                    result = client.vector_stores.files.upload_and_poll(
                        vector_store_id=vector_store.id,
                        file=(
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    )

                    if result.status != "completed":
                        raise RuntimeError("PDF 처리에 실패했습니다.")

                    # 세션에 저장
                    st.session_state.pdf_vector_store_id = vector_store.id
                    st.session_state.pdf_file_id = result.id
                    st.session_state.pdf_messages = []

                st.rerun()

            except Exception as e:
                if vector_store is not None:
                    client.vector_stores.delete(vector_store.id)
                st.error(f"PDF 처리 오류: {e}")


# PDF가 준비된 경우
else:

    col1, col2 = st.columns(2)

    with col1:
        st.button("Clear", on_click=clear_chat)

    with col2:
        if st.button("Leave"):

            if client is None:
                st.warning("API Key를 입력해주세요.")

            else:
                try:
                    client.vector_stores.delete(
                        st.session_state.pdf_vector_store_id
                    )

                    # 업로드한 원본 파일도 삭제
                    client.files.delete(
                        st.session_state.pdf_file_id
                    )

                    st.session_state.pdf_vector_store_id = None
                    st.session_state.pdf_messages = []
                    st.session_state.pop("pdf_file_id", None)
                    st.session_state.pdf_answer_cache = {}

                    st.rerun()

                except Exception as e:
                    st.error(f"삭제 오류: {e}")

    # 이전 대화 표시
    for msg in st.session_state.pdf_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 새로운 질문
    
# 새로운 질문
if prompt := st.chat_input("PDF에 대해 질문하세요"):

    if client is None:
        st.warning("API Key를 입력해주세요.")

    else:
        st.session_state.pdf_messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        # PDF와 질문을 조합해 캐시 키 생성
        cache_key = (
            st.session_state.pdf_vector_store_id,
            prompt.strip()
        )

        with st.chat_message("assistant"):
            output_area = st.empty()

            # 이전에 질문했던 내용이면 캐시 사용
            if cache_key in st.session_state.pdf_answer_cache:
                response = st.session_state.pdf_answer_cache[cache_key]
                output_area.markdown(response)

            else:
                # 새로운 질문일 때만 API 호출
                with output_area.container():
                    stream = client.responses.create(
                        model="gpt-6-luna",
                        instructions=(
                            "업로드된 PDF를 바탕으로 답변하세요. "
                            "확인되지 않은 내용은 추측하지 마세요."
                        ),
                        input=st.session_state.pdf_messages,
                        tools=[{
                            "type": "file_search",
                            "vector_store_ids": [
                                st.session_state.pdf_vector_store_id
                            ]
                        }],
                        stream=True
                    )

                    raw_response = st.write_stream(stream)

                # 잘못 표시되는 출처 문자 제거
                response = clean_citations(raw_response)

                # 깨끗한 답변으로 화면 교체
                output_area.markdown(response)

                # 캐시에 저장
                st.session_state.pdf_answer_cache[cache_key] = response

        # 대화 기록 저장
        st.session_state.pdf_messages.append({
            "role": "assistant",
            "content": response
        })

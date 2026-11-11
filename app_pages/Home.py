import streamlit as st
import base64
import hashlib

st.title("Home")
st.subheader("AI 질문 답변 + 이미지 생성")

client = st.session_state.get("openai_client")


# ----------------------------
# 질문 답변 기능 + 캐시
# ----------------------------

@st.cache_data(scope="session", show_spinner=False)
def get_cached_answer(question, key_id, _client):
    response = _client.responses.create(
        model="gpt-6-luna",
        input=question
    )
    return response.output_text


st.header("AI 질문 답변")

question = st.text_input("AI에게 질문하세요")

if st.button("질문하기"):
    if client is None:
        st.warning("API Key를 입력해주세요.")

    elif not question.strip():
        st.warning("질문을 입력해주세요.")

    else:
        key_id = hashlib.sha256(
            client.api_key.encode()
        ).hexdigest()

        with st.spinner("답변을 확인하고 있습니다..."):
            answer = get_cached_answer(
                question.strip(),
                key_id,
                client
            )

        st.write(answer)

# ----------------------------
# 이미지 생성 기능
# ----------------------------
st.divider()
st.header("AI 이미지 생성")

image_prompt = st.text_input("생성할 이미지를 설명하세요")

if st.button("이미지 생성하기"):
    if client is None:
        st.warning("왼쪽 사이드바에 OpenAI API Key를 입력해주세요.")
    elif not image_prompt.strip():
        st.warning("이미지 설명을 입력해주세요.")
    else:
        with st.spinner("이미지를 생성하고 있습니다..."):
            img = client.images.generate(
                model="gpt-image-2.6-flare",
                prompt=image_prompt
            )

            image_bytes = base64.b64decode(img.data[0].b64_json)

        st.image(image_bytes)
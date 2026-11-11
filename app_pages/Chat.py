import streamlit as st

st.title("Chat")
st.subheader("OpenAI 챗봇")

client = st.session_state.get("openai_client")

if "messages" not in st.session_state:
    st.session_state.messages = []

def clear_chat():
    st.session_state.messages = []

st.button("Clear", on_click=clear_chat)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("메시지를 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    if client is None:
        with st.chat_message("assistant"):
            reply = "왼쪽 사이드바에 OpenAI API Key를 입력해주세요."
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
    else:
        with st.chat_message("assistant"):
            stream = client.responses.create(
                model="gpt-6-luna",
                input=st.session_state.messages,
                stream=True,
            )
            response = st.write_stream(stream)

        st.session_state.messages.append({"role": "assistant", "content": response})
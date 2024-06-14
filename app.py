import streamlit as st
from openai import OpenAI

st.header("Chat Bot")
user_api_key = st.text_input("OpenAI API키를 입력해주세요.")
if "user_api_key" not in st.session_state:
    st.session_state["user_api_key"] = user_api_key
if st.button('Assistant 새롭게 생성하기'):
    client = OpenAI(api_key=f"{user_api_key}")
    assistant = client.beta.assistants.create(
        instructions="당신은 챗봇입니다. 성실하게 대답해주세요.",
        model="gpt-4o",
    )
    if 'client' not in st.session_state:
        st.session_state.client = client
    if 'assistant' not in st.session_state:
        st.session_state.assistant = assistant
messages = []
st.header("Thread")
prompt = st.chat_input("메시지를 입력하세요.")
if prompt: 
    st.session_state.messages.append({"role": "user", "content": prompt})
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    client = st.session_state['client']
    assistant = st.session_state['assistant']
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": f"{prompt}",
            }
        ]
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    thread_messages = client.beta.threads.messages.list(thread.id, run_id=run.id)
    answer = thread_messages.data[0].content[0].text.value
    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
if st.button("Thread 지우기"):
    del st.session_state['messages']
if st.button("대화 기록 지우기"):
    response = client.beta.threads.delete(thread.id)

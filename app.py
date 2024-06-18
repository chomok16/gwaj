import streamlit as st
from openai import OpenAI
from PIL import Image

def app():
    st.set_page_config(layout="wide")
    
    # Load image from file
    img = Image.open("백경이.png")
    img = img.resize((171,230))
    st.image(img)
    
    history = []
    st.title("우리 학교의 영원한 친구 백경이")
    st.subheader("백경이는 부경대의 모든 건물들을 다 알아! 학식당 메뉴도 알고 있지, 뭐든지 물어봐!")
app()

with st.sidebar:
    user_api_key = st.text_input("OpenAI API키를 입력해주세요.", key = "openai_api_key", type="password")
    if 'key' not in st.session_state:
        st.session_state.key = user_api_key
    
if st.button('Assistant 새롭게 생성하기'):
    client = OpenAI(api_key=user_api_key)
    vector_store=client.beta.vector_stores.create(name="TotalFile")
    with open(file='메뉴와가격.xlsx', mode='r') as file:
        read_file = file.read()
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id = vector_store.id,
            files = read_file
        )

    assistant = client.beta.assistants.create(
        instructions="당신의 이름은 백경AI입니다. 친근한 말투로 대답해주세요. 챗봇으로서 성실하게 대답해주세요.",
        model="gpt-4o",
        tools=[{"type": "file_search"}],
        tools_resources={"file_search":{[vector_store.id]}}
    )
    if 'client' not in st.session_state: # client를 session_state로 저장
        st.session_state.client = client
    if 'assistant' not in st.session_state: # assistant를 session_state로 저장
        st.session_state.assistant = assistant
    messages = []
    st.session_state.messages = messages # 대화 내역을 session_state에 저장
    with st.chat_message("assistant"):
        st.markdown("안녕, 부경대 친구들, 학교생활을 도와주는 백경이야!")
    st.session_state.messages.append({"role": "assistant", "content": "안녕, 부경대 친구들, 학교생활을 도와주는 백경이야!"})


if prompt := st.chat_input("메시지를 입력하세요."): 
    st.session_state.messages.append({"role": "user", "content": prompt}) # user의 prompt를 messages로 저장
    for msg in st.session_state.messages: # re-run 후 대화 내역 출력 및 user의 prompt를 출력
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    client = st.session_state.client # session_state에 저장된 client id를 불러오기
    assistant = st.session_state.assistant
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )
    st.session_state.thread_id = thread.id
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    thread_messages = client.beta.threads.messages.list(thread.id, run_id=run.id)
    answer = thread_messages.data[0].content[0].text.value # assistant의 응답에서 text를 추출
    with st.chat_message("assistant"): # assistant의 text 응답 출력
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
if st.button("대화 내역 지우기"):
    if st.session_state.thread_id in st.session_state:
        client = st.session_state.client
        response = client.beta.thread.delete(st.session_state.thread_id)
        del st.session_state.messages
        st.rerun()

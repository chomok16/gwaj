import streamlit as st
from openai import OpenAI
from PIL import Image
from streamlit_chat import message
import openai
from streamlit.components.v1 import html

def app():
    st.set_page_config(layout="wide")
    img = Image.open("백경이.png")
    img = img.resize((171,230))
    st.image(img)
    st.title("우리 학교의 영원한 친구 백경이")
    st.subheader("백경이는 부경대의 모든 건물들을 다 알아! 학식당 메뉴도 알고 있지, 뭐든지 물어봐!")
    st.write(f"OpenAI ver {openai.__version__}")
app()

with st.sidebar:
    if user_api_key := st.text_input("OpenAI API키를 입력해주세요.", key = "openai_api_key", type="password"):
        if 'user_api_key' not in st.session_state:
            st.session_state.key = user_api_key
            
if st.button('대화 새로 시작하기'):
    if st.session_state.key:
        client = OpenAI(api_key=user_api_key)
        vector_store=client.beta.vector_stores.create(name="TotalFile")
        file_paths = ["clearfile.pdf"]
        file_streams = [open(path, "rb") for path in file_paths]
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id = vector_store.id,
            files = file_streams
        )
        assistant = client.beta.assistants.create(
            instructions="""
            업로드된 파일을 바탕으로 대답해주세요.
            """,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search":{"vector_store_ids": [vector_store.id]}},
        )
        if 'client' not in st.session_state: # client를 session_state로 저장
            st.session_state.client = client
        if 'assistant' not in st.session_state: # assistant를 session_state로 저장
            st.session_state.assistant = assistant
        messages = []
        st.session_state.messages = messages # 대화 내역을 session_state에 저장
        message("안녕, 부경대 친구들, 학교생활을 도와주는 '백경이봇'이야!", is_user=False, avatar_style='no-avatar')
        st.session_state.messages.append({"content": "안녕, 부경대 친구들! 학교생활을 도와주는 '백경이봇'이야.", "is_user": False, "html": False})

if prompt := st.chat_input("메시지를 입력하세요."):
    if st.session_state.client:
        st.session_state.messages.append({"content": prompt, "is_user": True, "html": False}) # user의 prompt를 messages로 저장
        for msg in st.session_state.messages: # re-run 후 대화 내역 출력 및 user의 prompt를 출력
            message(msg["content"], is_user=msg["is_user"], avatar_style="no-avatar", allow_html=msg["html"])
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
            assistant_id=assistant.id,
        )
        thread_messages = client.beta.threads.messages.list(thread.id, run_id=run.id)
        answer = thread_messages.data[0].content[0].text.value # assistant의 응답에서 text를 추출
        message(answer, avatar_style="no-avatar")
        st.session_state.messages.append({"content": answer, "is_user": False, "html": False})

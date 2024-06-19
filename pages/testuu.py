import streamlit as st
from openai import OpenAI
from PIL import Image
from streamlit_chat import message
import json

def app():
    st.set_page_config(layout="wide")
    img = Image.open("백경이.png")
    img = img.resize((171,230))
    st.image(img)
    st.title("우리 학교의 영원한 친구 백경이")
    st.subheader("백경이는 부경대의 모든 건물들을 다 알아! 학식당 메뉴도 알고 있지, 뭐든지 물어봐!")
app()

with st.sidebar:
    if user_api_key := st.text_input("OpenAI API키를 입력해주세요.", key = "openai_api_key", type="password"):
        if 'user_api_key' not in st.session_state:
            st.session_state.key = user_api_key
            
if st.button('대화 새로 시작하기'):
    if st.session_state.key:
        client = OpenAI(api_key=user_api_key)
        vector_store=client.beta.vector_stores.create(name="TotalFile")
        file_paths = ["메뉴와가격.pdf", "건물1.pdf", "건물2.pdf"]
        file_streams = [open(path, "rb") for path in file_paths]
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id = vector_store.id,
            files = file_streams
        )
        assistant = client.beta.assistants.create(
            instructions="""
            당신의 이름은 '백경이봇'입니다. 존댓말이 아닌 반말로 대답해주세요. 대답은 json형식으로 출력해주세요.
            욕설은 사용하지 말아주세요. 챗봇으로서 성실하게 대답해주세요. 업로드된 파일을 바탕으로 대답해주세요.
            '메뉴와가격.pdf'는 교내 식당 '들락날락'의 메뉴판입니다. 메뉴에 관한 정보를 요청받는다면 '들락날락'의 메뉴임을 알려주세요.
            '건물1.pdf'는 교내 시설의 위치를 적어놓은 파일입니다. 숫자로만 이루어진 정보는 시설의 번호입니다.
            '건물2.pdf'는 교내 건물의 명칭과 번호를 입력한 파일입니다. 알파벳과 숫자로 이루어진 정보는 건물의 번호입니다.
            건물의 위치 정보에 관한 정보를 요청받는다면 '건물1.pdf' 또는 '건물2.pdf' 파일을 참고하여 알려주세요.
            vector_store에 파일이 업로드가 되어있다는 것은 언급하지 마세요. 
            메시지에 출처에 대한 인용표시와 각주는 생략해주세요.
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
        st.session_state.messages.append({"content": "안녕, 부경대 친구들! 학교생활을 도와주는 '백경이봇'이야.", "role": False})

if prompt := st.chat_input("메시지를 입력하세요."):
    if st.session_state.client:
        st.session_state.messages.append({"content": prompt, "role": True}) # user의 prompt를 messages로 저장
        for msg in st.session_state.messages: # re-run 후 대화 내역 출력 및 user의 prompt를 출력
            message(msg["content"], is_user=msg["role"], avatar_style="no-avatar")
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
        message(answer, avatar_style="no-avatar")
        st.session_state.messages.append({"content": answer, "role": False})
if st.button("대화 내역 지우기"):
    if st.session_state.thread_id:
        if st.session_state.client:
            client = st.session_state.client
            response = client.beta.thread.delete(st.session_state.thread_id)
            del st.session_state.messages
            st.rerun()

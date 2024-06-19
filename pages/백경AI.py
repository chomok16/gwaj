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
        file_paths = ["메뉴와가격.pdf", "건물1.pdf", "건물2.pdf"]
        file_streams = [open(path, "rb") for path in file_paths]
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id = vector_store.id,
            files = file_streams
        )
        assistant = client.beta.assistants.create(
            instructions="""
            당신의 이름은 '백경이봇'입니다. 존댓말이 아닌 반말로 대답해주세요.
            욕설은 사용하지 말아주세요. 챗봇으로서 성실하게 대답해주세요. 업로드된 파일을 바탕으로 대답해주세요.
            '메뉴와가격.pdf'는 교내 식당 '들락날락'의 메뉴판입니다. 메뉴에 관한 정보를 요청받는다면 '들락날락'의 메뉴임을 알려주세요.
            '건물1.pdf'는 교내 시설의 위치를 적어놓은 파일입니다. 숫자로만 이루어진 정보는 시설의 번호입니다.
            '건물2.pdf'는 교내 건물의 명칭과 번호를 입력한 파일입니다. 알파벳과 숫자로 이루어진 정보는 건물의 번호입니다.
            건물의 위치 정보에 관한 정보를 요청받는다면 '건물1.pdf' 또는 '건물2.pdf' 파일을 참고하여 알려주세요.
            건물 위치에 관한 질문을 받으면, 대답에 해당하는 시설에 대응하는 이미지 파일을 
            vector_store에 파일이 업로드가 되어있다는 것은 언급하지 마세요. '업로드한 파일'이라는 표현은 쓰지 마세요.
            대답에 사용자가 자료를 올렸다는 표현은 사용하지 마세요. 
            업로드된 파일에서 정보를 찾을 수 없다면, 자료에서 정보를 찾을 수 없았다고 말하지 말고 잘 모르겠다고 대답하세요.
            메시지에 출처에 대한 인용표시와 각주는 출력하지 마세요. 파일을 참고하였다는 사실도 말하지 마세요.
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
        bldg_data = [ # 건물 정보와 이미지 주소 정리 {"name": "건물 이름", "code": "건물 번호", "code_alt": "건물 번호(소문자)", "img_url": "이미지 주소", "width": "", "height": ""},
        {"name": "대학본부", "code": "A11", "code_alt": "a11", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%8C%80%ED%95%99%EB%B3%B8%EB%B6%80.png?raw=true", "width": "599", "height": "288"},
        {"name": "웅비관", "code": "A12", "code_alt": "a12", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%9B%85%EB%B9%84%EA%B4%80.png?raw=true", "width": "654", "height": "400"},
        {"name": "누리관", "code": "A13", "code_alt": "a13", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%88%84%EB%A6%AC%EA%B4%80.png?raw=true", "width": "561", "height": "411"},
        {"name": "향파관", "code": "A15", "code_alt": "a15", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%ED%96%A5%ED%8C%8C%EA%B4%80.png?raw=true", "width": "734", "height": "605"},
        {"name": "미래관", "code": "A21", "code_alt": "a21", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%AF%B8%EB%9E%98%EA%B4%80.png?raw=true", "width": "431", "height": "248"},
        {"name": "디자인관", "code": "A22", "code_alt": "a22", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%94%94%EC%9E%90%EC%9D%B8%EA%B4%80.png?raw=true", "width": "409", "height": "342"},
        {"name": "나래관", "code": "A23", "code_alt": "a23", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%82%98%EB%9E%98%EA%B4%80.png?raw=true", "width": "360", "height": "504"},
        {"name": "부산창업카페 2호점", "code": "A26", "code_alt": "a26", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%B6%80%EC%82%B0%EC%B0%BD%EC%97%85%EC%B9%B4%ED%8E%98.png?raw=true", "width": "485", "height": "536"},
        {"name": "위드센터", "code": "B11", "code_alt": "b11", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%9C%84%EB%93%9C%EC%84%BC%ED%84%B0.png?raw=true", "width": "970", "height": "278"},
        {"name": "나비센터", "code": "B12", "code_alt": "b12", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%82%98%EB%B9%84%EC%84%BC%ED%84%B0.png?raw=true", "width": "449", "height": "558"},
        {"name": "충무관", "code": "B13", "code_alt": "b13", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%B6%A9%EB%AC%B4%EA%B4%80.png?raw=true", "width": "614", "height": "489"},
        {"name": "환경해양관", "code": "B14", "code_alt": "b14", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%ED%99%98%EA%B2%BD%ED%95%B4%EC%96%91%EA%B4%80.png?raw=true", "width": "429", "height": "286"},
        {"name": "자연과학 1관", "code": "B15", "code_alt": "b15", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%9E%90%EC%97%B0%EA%B3%BC%ED%95%991%EA%B4%80.png?raw=true", "width": "667", "height": "362"},
        {"name": "가온관", "code": "B21", "code_alt": "b21", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EA%B0%80%EC%98%A8%EA%B4%80.png?raw=true", "width": "503", "height": "511"},
        {"name": "청운관", "code": "B22", "code_alt": "b22", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%B2%AD%EC%9A%B4%EA%B4%80.png?raw=true", "width": "560", "height": "410"},
        {"name": "수산질병관리원", "code": "C11", "code_alt": "c11", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%88%98%EC%82%B0%EC%A7%88%EB%B3%91%20%EA%B4%80%EB%A6%AC%EC%9B%90.png?raw=true", "width": "471", "height": "535"},
        {"name": "장영실관", "code": "C12", "code_alt": "c12", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%9E%A5%EC%98%81%EC%8B%A4%EA%B4%80.png?raw=true", "width": "551", "height": "489"},
        {"name": "해양공동연구관", "code": "C13", "code_alt": "c13", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%ED%95%B4%EC%96%91%EA%B3%B5%EB%8F%99%EC%97%B0%EA%B5%AC%EA%B4%80.png?raw=true", "width": "571", "height": "281"},
        {"name": "수조실험동", "code": "C27", "code_alt": "c27", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%88%98%EC%A1%B0%EC%8B%A4%ED%97%98%EB%8F%99.png?raw=true", "width": "445", "height": "732"},
        {"name": "아름관", "code": "C28", "code_alt": "c28", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%95%84%EB%A6%84%EA%B4%80.png?raw=true", "width": "385", "height": "744"},
        {"name": "테니스장", "code": "D12", "code_alt": "d12", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%ED%85%8C%EB%8B%88%EC%8A%A4%EC%9E%A5.png?raw=true", "width": "651", "height": "387"},
        {"name": "대운동장", "code": "D13", "code_alt": "d13", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%8C%80%EC%9A%B4%EB%8F%99%EC%9E%A5.png?raw=true", "width": "1080", "height": "506"},
        {"name": "한울관", "code": "D14", "code_alt": "d14", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%ED%95%9C%EC%9A%B8%EA%B4%80.png?raw=true", "width": "302", "height": "859"},
        {"name": "창의관", "code": "D15", "code_alt": "d15", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%B0%BD%EC%9D%98%EA%B4%80.png?raw=true", "width": "388", "height": "801"},
        {"name": "대학극장", "code": "D21", "code_alt": "d21", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%8C%80%ED%95%99%EA%B7%B9%EC%9E%A5.png?raw=true", "width": "840", "height": "422"},
        {"name": "체육관", "code": "D22", "code_alt": "d22", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%B2%B4%EC%9C%A1%EA%B4%80.png?raw=true", "width": "808", "height": "296"},
        {"name": "안전관리관", "code": "D23", "code_alt": "d23", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%95%88%EC%A0%84%EA%B4%80%EB%A6%AC%EA%B4%80.png?raw=true", "width": "844", "height": "474"},
        {"name": "수상레저관", "code": "D24", "code_alt": "d24", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%88%98%EC%83%81%EB%A0%88%EC%A0%80%EA%B4%80.png?raw=true", "width": "829", "height": "405"},
        {"name": "세종 1관", "code": "E11", "code_alt": "e11", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%84%B8%EC%A2%851%EA%B4%80.png?raw=true", "width": "503", "height": "367"},
        {"name": "세종 2관", "code": "E12", "code_alt": "e12", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%84%B8%EC%A2%852%EA%B4%80.png?raw=true", "width": "286", "height": "356"},
        {"name": "공학 1관", "code": "E13", "code_alt": "e13", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EA%B3%B5%ED%95%991%EA%B4%80.png?raw=true", "width": "440", "height": "346"},
        {"name": "학술정보관", "code": "E14", "code_alt": "e14", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%ED%95%99%EC%88%A0%EC%A0%95%EB%B3%B4%EA%B4%80(%EC%A4%91%EC%95%99%EB%8F%84%EC%84%9C%EA%B4%80).png?raw=true", "width": "638", "height": "477"},
        {"name": "공학 2관", "code": "E21", "code_alt": "e21", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EA%B3%B5%ED%95%992%EA%B4%80.png?raw=true", "width": "402", "height": "334"},
        {"name": "동원 장보고관", "code": "E22", "code_alt": "e22", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EB%8F%99%EC%9B%90%20%EC%9E%A5%EB%B3%B4%EA%B3%A0%EA%B4%80.png?raw=true", "width": "555", "height": "319"},
        {"name": "양어장 관리사", "code": "E29", "code_alt": "e29", "img_url": "https://github.com/chomok16/gwaj/blob/main/maps/%EC%96%91%EC%96%B4%EC%9E%A5%EA%B4%80%EB%A6%AC%EC%82%AC.png?raw=true", "width": "497", "height": "291"}
        ]
        for bldg_data_component in bldg_data:
            compared_phrase1 = bldg_data["name"]
            if compared_phrase1 in prompt:
                img_path=bldg_data["img_url"]
                img_data=f'<img width={bldg_data["width"]} height={bldg_data["height"]} src="{img_path}"/>'
                message(img_data, avatar_style = 'no-avatar', allow_html = True)
                st.session_state.messages.append({"content": img_data, "is_user": False, "html": True})
            elif compared_phrase1 not in prompt:
                compared_phrase2 = bldg_data["code"]
                if compared_phrase2 in prompt:
                    img_path=bldg_data["img_url"]
                    img_data=f'<img width={bldg_data["width"]} height={bldg_data["height"]} src="{img_path}"/>'
                    message(img_data, avatar_style = 'no-avatar', allow_html = True)
                    st.session_state.messages.append({"content": img_data, "is_user": False, "html": True})
                compared_phrase3 = bldg_data["code_alt"]
                if compared_phrase3 in prompt:
                    img_path=bldg_data["img_url"]
                    img_data=f'<img width={bldg_data["width"]} height={bldg_data["height"]} src="{img_path}"/>'
                    message(img_data, avatar_style = 'no-avatar', allow_html = True)
                    st.session_state.messages.append({"content": img_data, "is_user": False, "html": True})
            
if st.button("대화 내역 지우기"):
    if st.session_state.thread_id:
        if st.session_state.client:
            client = st.session_state.client
            response = client.beta.thread.delete(st.session_state.thread_id)
            del st.session_state.messages
            st.rerun()






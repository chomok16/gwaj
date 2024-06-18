from openai import OpenAI
import streamlit as st

userkey=st.text_input
client = OpenAI(api_key=userkey)
#assistant = client.beta.assistants.create(
#    instructions="당신의 이름은 백경AI입니다. 친근한 말투로 대답해주세요. 챗봇으로서 성실하게 대답해주세요.",
#    model="gpt-4o",
#)
st.markdown(client)

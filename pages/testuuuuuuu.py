import streamlit as st
from streamlit_chat import message
from streamlit.components.v1 import html

img_path="https://www.groundzeroweb.com/wp-content/uploads/2017/05/Funny-Cat-Memes-11.jpg"
message(f'<img width="100%" height="200" src="{img_path}"/>')

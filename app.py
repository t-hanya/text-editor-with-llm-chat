"""
AI editor app main.
"""

import streamlit as st
import ollama

from editor import Editor
from editor import editor_ui


st.set_page_config(
    page_title='AI Editor',
    page_icon='⚡️',
    layout="wide"
)


def generate() -> 'Generator[str, None, None]':
    stream = ollama.chat(
        model='gemma2',
        messages=st.session_state.messages,
        stream=True
    )
    content = ''
    for chunk in stream:
        content += chunk['message']['content']
        yield chunk['message']['content']
    st.session_state.messages.append(
        {'role': 'assistant', 'content': content})


if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.editor = Editor(columns=2)

columns = st.columns(3)

chat_container = columns[0].container(height=740)

editor_ui(columns[1:], st.session_state.messages, st.session_state.editor)

if user_msg := st.chat_input():
    st.session_state.messages.append({'role': 'user', 'content': user_msg})

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

if (st.session_state.messages and
    st.session_state.messages[-1]['role'] == 'user'):
    with chat_container:
        with st.chat_message('assistant'):
            st.write_stream(generate())

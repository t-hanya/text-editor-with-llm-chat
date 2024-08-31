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


NUM_EDITOR_COLS = 1


def generate() -> 'Generator[str, None, None]':
    # embed reference contents
    ref_msgs = []
    if st.session_state.chat_references:
        editor = st.session_state.editor
        ref_contents = '\n\n-----\n\n'.join(
            [editor.files[fname].content
             for fname in st.session_state.chat_references]
        )
        ref_msgs = [
            {'role': 'user', 'content': '以下のファイルの内容を参考にしてください:\n\n' + ref_contents},
            {'role': 'assistant', 'content': '分かりました。'}
        ]
    # chat completion
    stream = ollama.chat(
        model='gemma2',
        messages=(ref_msgs + st.session_state.messages),
        stream=True
    )
    content = ''
    for chunk in stream:
        content += chunk['message']['content']
        yield chunk['message']['content']
    st.session_state.messages.append(
        {'role': 'assistant', 'content': content})


if 'messages' not in st.session_state:
    st.session_state.chat_references = []
    st.session_state.messages = []
    st.session_state.editor = Editor(columns=NUM_EDITOR_COLS)

columns = st.columns(1 + NUM_EDITOR_COLS)

chat_container = columns[0].container(height=740)

editor_ui(columns[1:], st.session_state.messages, st.session_state.editor)

with chat_container:
    # chat references
    st.multiselect(
        'Chat references',
        list(st.session_state.editor.files.keys()),
        placeholder='Add to context',
        key='chat_references',
        label_visibility='collapsed'
    )

    # chat action buttons
    btn_cols = st.columns(4)
    messages = st.session_state.messages
    if btn_cols[0].button('Clear', key='clear', use_container_width=True):
        messages.clear()
    if btn_cols[1].button('Retry', key='retry', use_container_width=True):
        if messages and messages[-1]['role'] == 'assistant':
            messages.pop(-1)
    if btn_cols[2].button('Remove', key='remove', use_container_width=True):
        while messages:
            last = messages.pop(-1)
            if last['role'] == 'user':
                break
    with btn_cols[3]:
        use_markdown = st.toggle('Markdown', value=True, key='enalbe-markdown')

if user_msg := st.chat_input():
    st.session_state.messages.append({'role': 'user', 'content': user_msg})

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            if use_markdown:
                st.markdown(msg['content'])
            else:
                st.code(msg['content'], language='markdown', wrap_lines=True)

if (st.session_state.messages and
    st.session_state.messages[-1]['role'] == 'user'):
    with chat_container:
        with st.chat_message('assistant'):
            st.write_stream(generate())

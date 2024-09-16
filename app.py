"""
AI editor app main.
"""

from collections.abc import Generator

import streamlit as st
import ollama

from editor import Editor
from editor import editor_ui


st.set_page_config(
    page_title='AI Editor',
    page_icon='⚡️',
    layout="wide",
    initial_sidebar_state="collapsed"
)


NUM_EDITOR_COLS = 1
MODEL_DEFS = {
    'gemma2': 'gemma2',
    # add optional models here.
}


def generate() -> Generator[str, None, None]:
    # embed reference contents
    ref_msgs = []
    if st.session_state.chat_references:
        editor = st.session_state.editor
        ref_contents = '\n\n-----\n\n'.join(
            [editor.files[fname].content
             for fname in st.session_state.chat_references]
        )
        ref_msgs = [
            {'role': 'user', 'content': 'Please refer to the contents of the following file.:\n\n' + ref_contents},
            {'role': 'assistant', 'content': 'OK.'}
        ]
    # chat completion
    stream = ollama.chat(
        model=MODEL_DEFS[st.session_state.model],
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
    st.session_state.model = list(MODEL_DEFS.keys())[0]
    st.session_state.chat_references = []
    st.session_state.messages = []
    st.session_state.editor = Editor(columns=NUM_EDITOR_COLS)


with st.sidebar:
    # model selection
    st.radio('Model', list(MODEL_DEFS.keys()), key='model')
    # page height
    page_height = st.number_input(
        'Page height', min_value=500, max_value=1000, value=760)


columns = st.columns(1 + NUM_EDITOR_COLS)

chat_container = columns[0].container(height=page_height)

editor_ui(columns[1:], st.session_state.messages, st.session_state.editor, page_height=page_height)

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

with columns[0]:
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

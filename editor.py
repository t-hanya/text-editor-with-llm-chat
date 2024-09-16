"""
An text editor app.
"""

from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
import re

import streamlit as st


TEMPLATE_PARAM_PATTERN = re.compile(r"{{\s*([a-zA-Z]\w*)\s*}}")  # {{paramname}}
TEMPLATE_BLOCK_PATTERN = re.compile(r"(## \d+\..*?)(?=(## \d+\.)|$)", flags=re.DOTALL)


@dataclass
class File:
    name: str
    content: str = ''


@dataclass
class Block:
    header: str
    content: str
    parameters: list[str]


@dataclass
class FileTab:
    file: File
    blocks: list[Block] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.update_params_and_steps()

    def update_params_and_steps(self) -> None:
        content = self.file.content.strip()
        matches = TEMPLATE_BLOCK_PATTERN.finditer(content)

        sections = [content]
        sections += [match.group(1).strip() for match in matches]
        blocks = []
        for section in sections:
            lines = section.strip().splitlines()
            if len(lines) < 2:  # header and body is needed
                continue
            header = lines[0].strip()
            body = '\n'.join(lines[1:]).strip()
            params = TEMPLATE_PARAM_PATTERN.findall(body)
            blocks.append(Block(header, body, params))
        self.blocks = blocks


@dataclass
class Column:
    tabs: list[FileTab]


class Editor:
    """An text editor data model."""

    def __init__(self,
                 data_dir: Path = Path('./workspace'),
                 columns: int = 2,
                ) -> None:
        self.data_dir = data_dir
        self.files = {}
        for path in sorted(self.data_dir.iterdir()):
            if path.is_file() and path.suffix in ('.md', '.txt'):
                content = path.open().read().strip()
                self.files[path.name] = File(path.name, content)
        self.columns = [Column([]) for _ in range(columns)]

    def save_file(self, file_name: str) -> None:
        """Reflect current content to the file."""
        if file_name not in self.files:
            raise KeyError(file_name)
        path = self.data_dir / file_name
        with path.open('w') as f:
            f.write(self.files[file_name].content)

    def assign_params(self, param_names: list[str]
                      ) -> tuple[dict[str, str], list[str]]:
        unused_params = []
        assignment = {}
        contents = {Path(fname).stem: file.content
                    for fname, file in self.files.items()}
        for pname in param_names:
            if pname in contents:
                assignment[pname] = contents[pname]
            else:
                unused_params.append(pname)
        return assignment, unused_params

    @property
    def not_opened_files(self) -> list[str]:
        opened_files = set()
        for column in self.columns:
            for tab in column.tabs:
                opened_files.add(tab.file.name)
        return [fname for fname in self.files if fname not in opened_files]

def editor_ui(columns: list,
              messages: list[dict],
              editor: Editor,
              page_height: int = 760):

    @st.dialog("Create new file")
    def _create_new_file_dialog(col_idx: int) -> None:
        fname = st.text_input('File name')
        if st.button('Create') and fname:
            if not fname.endswith('.md') or not fname.endswith('.txt'):
                fname += '.md'
            file = File(fname)
            editor.files[file.name] = file
            editor.columns[col_idx].tabs.append(FileTab(file))
            st.rerun()

    def _on_text_change(tab: FileTab):
        fname = tab.file.name
        text = st.session_state['txtarea-' + fname]
        if text != editor.files[fname].content:
            editor.files[fname].content = text
            editor.save_file(fname)
            tab.update_params_and_steps()

    def _on_step_exec_button(xxx):
        pass

    for col_idx, (col, col_data) in enumerate(zip(columns, editor.columns)):
        tabs = col.tabs([tab.file.name for tab in col_data.tabs] + ['＋'])

        # file tabs
        for tab, tab_data in zip(tabs, col_data.tabs):

            # add text areas
            tab.text_area(
                'Content',
                tab_data.file.content,
                height=page_height - 80,
                key='txtarea-' + tab_data.file.name,
                on_change=partial(_on_text_change, tab=tab_data),
                label_visibility="collapsed",
            )

            # action buttons (with close button)
            btn_cols = tab.columns(max(1, len(tab_data.blocks)))
            for col, block in zip(btn_cols, tab_data.blocks):
                key = f'btn-{tab_data.file.name}-{block.header}'
                if col.button(block.header, key=key, use_container_width=True):
                    filled, unfilled = editor.assign_params(block.parameters)
                    if unfilled:
                        # invoke dialog to fill unfilled params
                        pass
                    else:
                        messages.append({'role': 'user', 'content': block.content})

        # file open tab
        with tabs[-1]:
            if st.button('New file', key=f'col{col_idx}-new-btn'):
                _create_new_file_dialog(col_idx)
            for fname in editor.not_opened_files:
                if st.button(f'Open: {fname}', key=f'col{col_idx}-open-{fname}'):
                    file = editor.files[fname]
                    editor.columns[col_idx].tabs.append(FileTab(file))
                    st.rerun()
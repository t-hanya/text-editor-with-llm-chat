# Text editor with LLM chat

This is a prototype text editor for collaborative creation with LLM.

![Text editor demo](./demo.gif)

## Requirements

- ollama-python
- streamlit>=1.38

## Download language model

```bash
ollama pull gemma2
```

## Run app

```bash
streamlit run app.py
```

Notes:

- Text files with `.txt` or `.md` suffix under the `workspace` directory can be accessed from the app.
- In a text file, header line in `## 1. Some Title` format will be treated as an instruction. For each instruction in the text, button will be created to invoke LLM text generation with the instruction.
- Please check Gemma2 terms of use and prohibited use policy before using this app. To use other model, please edit `MODEL_DEFS` in `app.py`.


# How to Install Ollama on Mac (macOS) — Video Notes

Video: https://www.youtube.com/watch?v=ucxtk-jUj6c

## Summary

### 1. Download & Install
- Search "Ollama" in a browser; the official site is ollama.com.
- The homepage has a one-line install command to copy.
- Open Terminal (via Spotlight search) and paste the command (curl -fsSL installer script).
- Press Enter; you'll be prompted for your Mac login password to allow the install.
- Terminal shows "starting Ollama" then "installation complete."

### 2. Running Ollama
- Ollama runs as a background process (visible under Background Activity; manageable via Login Items & Extensions in macOS System Settings).
- It also installs as an app in Applications with a graphical user interface (GUI).

### 3. Using the GUI
- Opening the app shows a model picker. By default it lists cloud-based models; models with a download icon can be run locally on your Mac.
- Selecting a cloud model (e.g., MiniMax M2) prompts you to sign in to an Ollama account to use cloud models.
- Sign in with Google, then click "Connect" to link the device ("device connected successfully").
- Back in the chat view, you can prompt the selected model (e.g., "write a C++ hello world program") and it returns code plus a line-by-line explanation.
- Menus: the Ollama menu has settings and quit; the File menu lets you start a New Chat and toggle the sidebar to view chat history; the Edit menu has standard text-editing options.

### 4. Installing Models via Terminal
- Run: `ollama run <model-name>`
- Model names are listed on ollama.com under "Models," sortable by popularity and filterable by type (cloud, embeddings, visual/vision, tools, thinking models).
- Browsing ollama.com/library shows the most popular models — e.g., Llama 3.1 is the most popular, with about 110 million pulls/downloads.

## Conclusion
A short walkthrough covering: downloading and installing Ollama via Terminal on macOS, signing in for cloud model access, chatting with a model through the GUI, and installing/running additional local models from the command line or the online model library.

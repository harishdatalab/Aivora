
import streamlit as st
import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from gtts import gTTS
import base64
import tempfile
import google.generativeai as genai
import uuid
import speech_recognition as sr

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY not found. Please set it in your environment or Streamlit Secrets.")
    st.stop()
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="KINA - AI Buddy", page_icon="📘")
st.title("🎓 KINA - AI Assistant")

# Sidebar: Enhanced Sidebar with Goals and Tasks
st.sidebar.title("📌 KINA Dashboard")

st.sidebar.subheader("🎯 Your Learning Goals")
learning_goal = st.sidebar.text_input("Add a Goal")
if st.sidebar.button("➕ Add Goal") and learning_goal:
    if "goals" not in st.session_state:
        st.session_state.goals = []
    st.session_state.goals.append(learning_goal)

if "goals" in st.session_state:
    for goal in st.session_state.goals:
        st.sidebar.markdown(f"✅ {goal}")

st.sidebar.subheader("📋😎Task Tracker")
if "todo" not in st.session_state:
    st.session_state.todo = []
if "done" not in st.session_state:
    st.session_state.done = []

new_task = st.sidebar.text_input("🆕👉 New Task")
if st.sidebar.button("📌🎯 Add Task") and new_task:
    st.session_state.todo.append(new_task)

for i, task in enumerate(st.session_state.todo):
    if st.sidebar.checkbox(f"⬜ {task}", key=f"todo_{i}_{task}"):
        st.session_state.todo.remove(task)
        st.session_state.done.append(task)

st.sidebar.subheader("✅🙌Task Completed")
for i, task in enumerate(st.session_state.done):
    st.sidebar.checkbox(f"✔️ {task}", value=True, disabled=True, key=f"done_{i}_{task}")

def safe_translate(text, lang):
    max_len = 500
    chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    return " ".join([GoogleTranslator(source='auto', target=lang).translate(chunk) for chunk in chunks])

TABS = st.tabs([
    "📘 Customised Learning Path",
    "💬 Micro Learning",
    "🧪 Quiz Generator",
    "🎧 Audio Generator",
    "🌐 Language Converter",
    "🧠 AI Content Chunker",
    "🗣 Scenario Builder with AI Personas"
])

# Tab 1
with TABS[0]:
    st.header("📘 Customised Learning Path")
    lang = st.selectbox("🌐 Language", ["english", "spanish", "french", "chinese"])
    knowledge = st.text_area("🧠 Your Current Knowledge")
    goal = st.text_area("Learning Goals")
    style = st.selectbox("🧩 Learning Style", ["Visual", "Reading", "Hands-on", "Mixed"])
    if st.button("🚀 Generate Plan"):
        with st.spinner("🧠 Crafting your custom roadmap..."):
            prompt = f"""
            You are KINA, an expert AI tutor.
            The user has the following:
            - Current knowledge: {knowledge}
            - Goal: {goal}
            - Preferred learning style: {style}

            Please generate a full markdown learning roadmap that includes:
            1. 📘 Stage-by-stage steps with estimated timelines.
            2. 🎨 Visual-style flow or layout described in text if user chose 'Visual'.
            3. 📺 Three **specific YouTube videos** including titles and real video **hyperlinks**.
            4. 📚 Recommended resources, tools or tutorials related to the goal.
            5. 🧠 Personalized study tips matching the selected learning style.

            Format all sections clearly with markdown headers (##) and bullet points.
            Example: [How Neural Networks Learn](https://www.youtube.com/watch?v=aircAruvnKk)
            """
            response = model.generate_content(prompt)
            plan = response.text
            if lang != "english":
                plan = safe_translate(plan, lang)
            st.markdown("### 📜 Your Learning Plan")
            st.markdown(plan)
            st.download_button("⬇️ Download Plan as .txt", plan, file_name="learning_plan.txt", mime="text/plain")
            st.success("✅ Video links are now clickable. Save this roadmap and start learning!")

# Tab 2: Micro Learning
with TABS[1]:
    st.header("💬 Micro Learning")
    if "study_step" not in st.session_state:
        st.session_state.study_step = 1
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.session_state.study_step == 1:
        st.write("Let's get started ✨")
        st.session_state.study_topic = st.text_input("📘 What topic are you studying?")
        st.session_state.confidence_level = st.slider("Confidence (0-10)", 0, 10)
        if st.button("➡️ Continue"):
            st.session_state.study_step = 2

    elif st.session_state.study_step == 2:
        topic = st.session_state.study_topic
        score = st.session_state.confidence_level
        prompt = f"User is studying: {topic}, confidence: {score}/10. Suggest action plan, style-based activities & encouragement."
        reply = model.generate_content(prompt).text
        st.markdown("### 🎯 Suggestion")
        st.markdown(reply)
        if st.button("💬 Ask a Question🌟"):
            st.session_state.study_step = 3

    elif st.session_state.study_step == 3:
        st.subheader("🤖 Chat with Your Twin")
        user_msg = st.text_input("You:", key="twin_input")
        if st.button("📨 Send"):
            chat = model.start_chat(history=st.session_state.chat_history)
            reply = chat.send_message(user_msg)
            st.session_state.chat_history.append({"role": "user", "parts": [user_msg]})
            st.session_state.chat_history.append({"role": "model", "parts": [reply.text]})

        for msg in st.session_state.chat_history:
            role = "🧑 You" if msg["role"] == "user" else "🤖 Twin"
            st.markdown(f"**{role}:** {msg['parts'][0]}")

# Tab 3: Quiz Generator
with TABS[2]:
    st.header("🧪 Quiz Generator")
    topic = st.text_input("📘 Enter a topic to quiz yourself:")
    if st.button("🎯 Generate Quiz"):
        prompt = f"""
        You are a quiz master.
        Generate 5 multiple choice questions (MCQs) for the topic: {topic}.
        Each question must include:
        - Question
        - Four options (a, b, c, d)
        - Correct answer line: Answer: x)
        Format:
        Q: [question]
        a) ...
        b) ...
        c) ...
        d) ...
        Answer: x)
        """
        quiz_text = model.generate_content(prompt).text
        st.session_state.quiz_data = quiz_text.strip().split("\n\n")
        st.session_state.full_quiz_text = quiz_text

    if "quiz_data" in st.session_state:
        st.markdown("### 📝 Your Quiz")
        for i, q_block in enumerate(st.session_state.quiz_data):
            lines = q_block.strip().split("\n")
            q_line = next((l for l in lines if l.strip().lower().startswith("q:")), None)
            opts = [line for line in lines if line.strip()[:2] in ["a)", "b)", "c)", "d)"]]
            ans_line = next((l for l in lines if "Answer:" in l), None)

            if not (q_line and opts and ans_line):
                st.warning(f"❌ Skipping malformed Q{i+1}")
                continue

            correct = ans_line.split(":")[-1].strip().lower()
            selected = st.radio(f"Q{i+1}: {q_line[2:].strip()}", opts, key=f"quiz_{i}")

            if st.button(f"✔️ Check Q{i+1}", key=f"btn_{i}"):
                if selected.lower().startswith(correct):
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Wrong. Correct answer is: {correct}")
        st.download_button("⬇️ Download Full Quiz (.txt)", st.session_state.full_quiz_text, file_name="quiz.txt")

# Tab 4: Audio Generator
with TABS[3]:
    st.header("🎧 Audio Generator")
    text = st.text_area("Enter content:")
    if st.button("🔊 Generate Audio"):
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as f:
                audio_data = f.read()
                b64 = base64.b64encode(audio_data).decode()
                st.audio(f"data:audio/mp3;base64,{b64}", format='audio/mp3')
                st.download_button("⬇️ Download Audio", audio_data, file_name="audio_summary.mp3")

# Tab 5: Language Converter
with TABS[4]:
    st.header("🌐 Language Converter")
    lang = st.selectbox("Choose Language", ["spanish", "french", "chinese"])
    msg = st.text_area("Type your message:")
    if st.button("🔁 Translate"):
        try:
            translated = GoogleTranslator(source="en", target=lang).translate(msg)
            st.success(f"Translated ({lang.upper()}): {translated}")
        except Exception as e:
            st.error(f"Error: {e}")

# Tab 6: AI Content Chunker
with TABS[5]:
    st.header("🧠 AI Content Chunker")
    st.markdown("Split large content into digestible chunks for course design or eLearning development.")
    raw_content = st.text_area("📄 Paste your raw content here (e.g., textbook extract, notes):", height=250)
    chunk_style = st.selectbox("🧩 Chunking Style", ["By Topic", "By Learning Objective", "By Key Concepts"])
    if st.button("🪄 Chunk My Content"):
        with st.spinner("Breaking it down for you..."):
            prompt = f"""
            You are KINA, an expert instructional designer.
            The user has pasted the following raw content:
            ---
            {raw_content}
            ---
            Please chunk this content into clear, labeled sections based on: {chunk_style}.
            Each chunk should include:
            - A short heading (##)
            - A short summary or key point
            - (Optional) suggestion of what format this would work well in (e.g., video, quiz, flashcard)

            Format the output in Markdown for readability.
            """
            try:
                chunks = model.generate_content(prompt).text
                st.markdown("### 🧩 Chunked Content")
                st.markdown(chunks, unsafe_allow_html=True)
                st.download_button("⬇️ Download as .txt", chunks, file_name="chunked_content.txt", mime="text/plain")
                st.success("✅ Content chunked and ready to use!")
            except Exception as e:
                st.error(f"⚠️ Something went wrong: {e}")

# Tab 7: Scenario Builder with AI Personas
with TABS[6]:
    st.header("🗣 Scenario Builder with AI Personas")
    st.markdown("Create interactive, realistic learning scenarios by defining a role and situation.")
    scenario_topic = st.text_input("🎯 Topic or Context for the Scenario", placeholder="e.g., Giving constructive feedback to a teammate")
    persona = st.selectbox("🧍 Persona to Simulate", ["Learner", "Manager", "Subject Matter Expert (SME)", "Peer/Colleague"])
    tone = st.selectbox("🎭 Tone of Conversation", ["Formal", "Casual", "Supportive", "Challenging"])
    length = st.selectbox("🕐 Scenario Length", ["Short (1-2 turns)", "Medium (3-4 turns)", "Long (5+ turns)"])
    if st.button("🎬 Generate Scenario"):
        with st.spinner("Crafting your roleplay..."):
            prompt = f"""
            You are KINA, an instructional designer assistant.

            Please generate a realistic, dialogue-based learning scenario based on:
            - Topic: {scenario_topic}
            - Persona Role: {persona}
            - Tone: {tone}
            - Desired Length: {length}

            Structure the output like a roleplay, alternating between "You" and "{persona}".
            Highlight learner decisions or challenges clearly.
            Add markdown formatting for readability (bold names, headers, bullet points if helpful).
            """
            try:
                scenario = model.generate_content(prompt).text
                st.markdown("### 🎭 Generated Learning Scenario")
                st.markdown(scenario, unsafe_allow_html=True)
                st.download_button("⬇️ Download Scenario as .txt", data=scenario, file_name="learning_scenario.txt", mime="text/plain")
                st.success("✅ Scenario generated successfully!")
            except Exception as e:
                st.error(f"⚠️ Error: {e}")

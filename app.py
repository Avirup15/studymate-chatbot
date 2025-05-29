import streamlit as st
from dotenv import load_dotenv
import os
import requests
from googleapiclient.discovery import build
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Load API keys from .env
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")


# Set Together API endpoint and model
TOGETHER_API_URL = "https://api.together.xyz/v1/completions"
MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"

# YouTube setup
   

def get_youtube_videos(query, max_results=3):
    YOUTUBE_KEYS = [
        os.getenv("YOUTUBE_API_KEY_1"),
        os.getenv("YOUTUBE_API_KEY_2"),
        os.getenv("YOUTUBE_API_KEY_3"),
        os.getenv("YOUTUBE_API_KEY_4"),
        os.getenv("YOUTUBE_API_KEY_5"),
        os.getenv("YOUTUBE_API_KEY_6") 
    ]
    for key in YOUTUBE_KEYS:
        try:
            youtube = build('youtube', 'v3', developerKey=key)
            request = youtube.search().list(
                q=query,
                part='snippet',
                type='video',
                order='relevance',
                videoDuration='medium',
                maxResults=max_results
            )
            response = request.execute()

            videos = []
            for item in response['items']:
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                thumbnail_url = item['snippet']['thumbnails']['high']['url']
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                videos.append({
                    "title": title,
                    "thumbnail_url": thumbnail_url,
                    "video_url": video_url
                })

            return videos
        except Exception:
            continue
    return []


def get_web_context(query):
    SERPER_KEYS = [
        os.getenv("SERPER_API_KEY_1"),
        os.getenv("SERPER_API_KEY_2"),
        os.getenv("SERPER_API_KEY_3")
    ]

    for key in SERPER_KEYS:
        try:
            headers = {
                "X-API-KEY": key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query
            }
            response = requests.post("https://google.serper.dev/search", headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                snippets = []
                for item in data.get("organic", []):
                    snippet = item.get("snippet")
                    if snippet:
                        snippets.append(snippet)
                return "\n".join(snippets[:5])
            else:
                continue  # Try next key

        except Exception:
            continue

    return "Web context could not be retrieved due to exhausted API limits."


def generate_easy_explanation(question, context):
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are a helpful and structured study assistant.
Use the provided web search results and YouTube video titles to answer the user's question clearly and in a student-friendly manner.

Respond in this format:

Gist:
A clear and concise explanation paragraph (around 4–5 sentences) with helpful context.

Key Points:
- Bullet 1
- Bullet 2
- Bullet 3

---

[BEGIN_EXAMPLE]
Question: What is photosynthesis?

Context:
Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.

Gist:
Photosynthesis is how green plants make their food using sunlight, carbon dioxide, and water. It happens in the chloroplasts of plant cells. It is essential for life on Earth as it produces the oxygen we breathe and forms the base of most food chains.

Key Points:
- Happens in green plants, algae, and some bacteria.
- Uses sunlight to convert carbon dioxide and water into glucose and oxygen.
- Takes place inside the chloroplasts of plant cells.
- Produces oxygen as a byproduct.
[END_EXAMPLE]

Now answer the following question using the context. 
Only use the information from the context. Do not include unrelated questions or hallucinate details.

Question: {question}

Context:
{context[:2500]}

Gist:
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": 700,
        "temperature": 0.4,
        "top_p": 0.9
        # No stop tokens to allow full generation
    }

    response = requests.post(TOGETHER_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        text = response.json()['choices'][0]['text'].strip()

        if "Key Points:" in text:
            gist, keypoints = text.split("Key Points:", 1)
            return gist.replace("Gist:", "").strip(), keypoints.strip()
        else:
            return text.strip(), "⚠️ Key points could not be generated."
    else:
        return f"❌ Error: {response.text}", ""




# ---- Streamlit UI ----
st.title("📚 StudyMate - Smart Study Chatbot")
if "gist" not in st.session_state:
    st.session_state.gist = ""
if "keypoints" not in st.session_state:
    st.session_state.keypoints = ""

if "video_count" not in st.session_state:
    st.session_state.video_count = 3
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""

# Subject and grade selectors
subject = st.selectbox("📖 Select Subject", ["General", "Physics", "Math", "Biology", "Computer Science", "History", "Geography", "Chemistry"])
grade = st.selectbox("🎓 Select Grade Level", ["All", "Middle School", "High School", "Undergraduate"])

prompt = st.text_input("Ask a study question:")
prompt = prompt.strip()
query = f"{prompt} - {subject} - {grade}"

# Initialize how many videos to show


# Button to load more videos


if prompt:
    
    st.write(f"🔍 You asked: {prompt}")
    videos = get_youtube_videos(query, max_results=st.session_state.video_count)
    if not videos:
        st.warning("😕 Sorry, no relevant videos found. Try rephrasing your question.")
          # prevent further execution like video rendering

    # Get context from web + video titles
    video_titles = "\n".join([video['title'] for video in videos])
    web_context = get_web_context(query)
    full_context = f"{video_titles}\n\n{web_context[:2000]}"

    # Generate LLM explanation
    if prompt != st.session_state.last_prompt:
        with st.spinner("📘 Generating easy explanation..."):
            gist, keypoints = generate_easy_explanation(prompt, full_context)
            st.session_state.gist = gist
            st.session_state.keypoints = keypoints

            st.session_state.last_prompt = prompt
            st.session_state.chat_history.append({
                "question": prompt,
                "explanation": st.session_state.gist + "\n\n" + st.session_state.keypoints
            })


    

# View toggle radio button
    st.markdown("---")
    st.subheader("🧠 Easy Explanation")

    view_option = st.radio("📖 Choose Explanation Format", ["📝 Paragraph", "🔹 Bullet Points"], help="Switch between a short explanation and bullet summary", index=0, horizontal=True)


    if view_option == "📝 Paragraph":
        st.markdown(st.session_state.gist)
        st.caption("Prefer quick facts? Try the bullet point view.")
    elif view_option == "🔹 Bullet Points":
        st.markdown("### 🔹 Quick Summary")
        for line in st.session_state.keypoints.splitlines():
            clean_line = line.strip().lstrip("-•*").strip()
            if clean_line:
                st.markdown(f"- {clean_line}")




    # Show top YouTube videos
    
    st.subheader("🎥 Recommended YouTube Videos")
    cols = st.columns(3)
    for idx, video in enumerate(videos[:st.session_state.video_count]):

        with cols[idx % 3]:
            st.markdown(
                f"""
                <div style="text-align: center; padding: 10px 0 20px;">
                    <img src="{video['thumbnail_url']}" width="100%" style="border-radius: 10px;" />
                    <p style="font-size: 14px; font-weight: bold; margin: 10px 0;">{video['title']}</p>
                    <a href="{video['video_url']}" target="_blank" style="text-decoration: none;">
                        <button style="padding: 6px 12px; font-size: 13px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
                            ▶️ Watch Video
                        </button>
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )
    if st.button("➕ Show More Videos"):
        st.session_state.video_count += 3
    

st.markdown("---")
st.markdown("Was this helpful? 👍 👎")
col1, col2 = st.columns(2)
with col1:
    if st.button("👍 Yes, it helped!"):
        st.success("Thanks for your feedback! 😊")
with col2:
    if st.button("👎 Not really"):
        st.info("Thanks! We'll try to improve. 💡")

st.markdown("---")
import random

suggested_topics = {
    "gravity": ["Newton's Laws", "Projectile Motion", "Free Fall"],
    "photosynthesis": ["Light Reaction", "Chloroplast", "Carbon Cycle"],
    "electricity": ["Ohm's Law", "Circuits", "Magnetism"],
    "evolution": ["Natural Selection", "Darwin", "Genetics"]
}

if prompt:  # ✅ only check suggestions if user entered something
    for keyword in suggested_topics:
        if keyword.lower() in prompt.lower():
            suggestions = random.sample(suggested_topics[keyword], 2)
            st.subheader("📌 Suggested Topics")
            st.markdown(f"**You might also like:** {', '.join(suggestions)}")
            break



if st.session_state.chat_history:
    st.subheader("🕘 Previous Queries")
    for chat in reversed(st.session_state.chat_history[-5:]):  # Show last 5
        with st.expander(f"🗨️ {chat['question']}"):
            st.markdown(chat["explanation"])


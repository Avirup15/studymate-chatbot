import streamlit as st
from dotenv import load_dotenv
import os
import requests
from googleapiclient.discovery import build


# Load API keys from .env
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Set Together API endpoint and model
TOGETHER_API_URL = "https://api.together.xyz/v1/completions"
MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"

# YouTube setup
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_youtube_videos(query, max_results=3):
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


def get_web_context(query):
    api_key = os.getenv("SERPER_API_KEY")
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query
    }
    response = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
    data = response.json()
    
    snippets = []
    for item in data.get("organic", []):
        snippet = item.get("snippet")
        if snippet:
            snippets.append(snippet)
    
    return "\n".join(snippets[:5])

def generate_easy_explanation(question, context):
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are a helpful study assistant.
Use the provided web search results and video titles to answer the user's question in a simple and clear way.

Question: {question}

Context:
{context[:3000]}

Answer:
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": 300,
        "temperature": 0.3,
        "top_p": 0.8,
        "stop": ["\n"]
    }

    response = requests.post(TOGETHER_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['text'].strip()
    else:
        return f"❌ Error: {response.text}"

# ---- Streamlit UI ----
st.title("📚 StudyMate - Smart Study Chatbot")
prompt = st.text_input("Ask a study question:")

if prompt:
    st.write(f"🔍 You asked: {prompt}")

    # Show top YouTube videos
    videos = get_youtube_videos(prompt)
    st.subheader("🎥 Recommended YouTube Videos")
    cols = st.columns(3)
    for idx, video in enumerate(videos):
        with cols[idx % 3]:
            st.image(video['thumbnail_url'], use_container_width=True)
            st.write(f"**{video['title']}**")
            st.markdown(f"[▶️ Watch Video]({video['video_url']})")

    # Get context from web + video titles
    video_titles = "\n".join([video['title'] for video in videos])
    web_context = get_web_context(prompt)
    full_context = f"{video_titles}\n\n{web_context}"

    # Generate LLM explanation
    with st.spinner("📘 Generating easy explanation..."):
        explanation = generate_easy_explanation(prompt, full_context)
        st.subheader("🧠 Easy Explanation")
        st.markdown(explanation)

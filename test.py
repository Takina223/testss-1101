
import streamlit as st
import subprocess
import tempfile
import os
import re
from moviepy.editor import VideoFileClip, concatenate_videoclips

def detect_silence(input_path, log_path, noise_threshold='-30dB', duration=0.5):
    cmd = [
        'ffmpeg', '-i', input_path,
        '-af', f'silencedetect=noise={noise_threshold}:d={duration}',
        '-f', 'null', '-'
    ]
    with open(log_path, 'w') as log_file:
        subprocess.run(cmd, stderr=log_file)

def parse_silence_log(log_path):
    with open(log_path, 'r') as f:
        lines = f.readlines()

    silence_starts, silence_ends = [], []
    for line in lines:
        if 'silence_start' in line:
            silence_starts.append(float(re.search(r'silence_start: (\d+\.?\d*)', line).group(1)))
        elif 'silence_end' in line:
            silence_ends.append(float(re.search(r'silence_end: (\d+\.?\d*)', line).group(1)))

    return list(zip(silence_starts, silence_ends))

def remove_silence(input_path, silence_segments, output_path):
    video = VideoFileClip(input_path)
    duration = video.duration
    nonsilent = []
    prev_end = 0

    for start, end in silence_segments:
        if start > prev_end:
            nonsilent.append(video.subclip(prev_end, start))
        prev_end = end

    if prev_end < duration:
        nonsilent.append(video.subclip(prev_end, duration))

    final = concatenate_videoclips(nonsilent)
    final.write_videofile(output_path, codec='libx264')

# Streamlit UI
st.title("🎬 Silence Cutter")

uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
        temp_input.write(uploaded_file.read())
        input_path = temp_input.name

    silence_log = tempfile.NamedTemporaryFile(delete=False).name
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

    st.info("Detecting silence...")
    detect_silence(input_path, silence_log)
    silence_segments = parse_silence_log(silence_log)

    st.info("Removing silent segments...")
    remove_silence(input_path, silence_segments, output_path)

    st.success("✅ Processing complete. Download your video below.")
    with open(output_path, "rb") as file:
        st.download_button("Download Cleaned Video", file, file_name="cleaned_video.mp4")

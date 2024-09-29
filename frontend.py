'''
Frontend Works as Intended: Cannot get the vector DB to work and I don't care about it that much anymore. 
    If I want, just give text as context --> Very bad but will work 

Now: Just need to get the backend to work properly and then have the frontend call it 
'''

import streamlit as st
import google.generativeai as genai
import time

# Configure the Google Gemini API
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
complete_notes_lst = []

# Placeholder for your video generation function
# def generate_video(text, num_frames):
#     main(text, num_frames)
#     return "merge_video.mp4"

# Function to generate a response from the LLM, returning only the text
def generate_chatbot_response(user_input):
    response = model.generate_content(user_input)
    complete_notes_lst.append([user_input, response.text])
    return response.text  # Extracting just the text from the response

# def summarize_everything():
#     return "hi"


# Streamlit UI
st.title("Text to Video")

# Prompt user for number of frames
num_frames = st.number_input("How long of a video do you want?", min_value=1, step=1)

st.subheader("Upload a Text File or Paste Text Below")

# Option to upload a text file
uploaded_file = st.file_uploader("Choose a text file", type=["txt"])

# Option to paste text
text_input = st.text_area("Or paste your text here:", height=200)

video_path = None
input_type = ""
text = ""
if uploaded_file is not None:
    # Read the uploaded text file
    text = uploaded_file.read().decode("utf-8")
    input_type = "File"
    st.write("Uploaded Text Successfully")
elif text_input:
    text = text_input
    input_type = "Paste"
    st.write("Pasted Text Successfully")
else: 
    st.write("Please upload or paste text")



if text:
    # Call the function to generate the video
    # from checker import main
    # main(text, num_frames, input_type)
    video_path = "final_video.mp4"

# Create columns for layout
col1, col2 = st.columns(2)

# Display video in the first column
with col1:
    if video_path:
        st.video(video_path)

# Display chatbot in the second column
with col2:
    st.subheader("Any questions about the video?")
    
    # Create a session state to keep track of previous questions
    if 'responses' not in st.session_state:
        st.session_state.responses = []

    user_question = st.text_input("Ask here:")
    
    if user_question:
        response = generate_chatbot_response(user_question)
        st.write(response)  # Display only the text from the response
        
        # Store the response in session state
        st.session_state.responses.append((user_question, response))
        
        # Display all previous questions and responses
        st.write("### Previous Questions and Answers:")
        for question, answer in st.session_state.responses:
            st.write(f"**Q:** {question}")
            st.write(f"**A:** {answer}")

    # if st.button("Get Summary"):
    #     if text:
    #         summary = summarize_everything()
    #         st.write("### Summary:")
    #         st.write(summary)
    #     else:
    #         st.write("No text available to summarize.")



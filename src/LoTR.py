import time
import streamlit as st
import openai
import os
import re

import base64
from PIL import Image
from io import BytesIO

# Set TESTING to True to read from pre-generated text files, False to use OpenAI API
TESTING = True

# Load environmental variables
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

IMG_MODEL =  "dall-e-2"   #"dall-e-3"      #dall-e-2" 
IMG_SIZE = '1024x1024'   #'1792x1024'     "1024x1024"

# Set up the OpenAI client with the actual API key
openai.api_key = OPENAI_API_KEY

# Path to the debug directory for testing
debug_dir = 'img/debug/'
test_image_path = "img/debug/img/"

# Paths for output generation
generation_dir = 'img/gen/'

# TODO: Find the way to collect outputs from different testers.



# Function to interact with OpenAI API or read from files in TESTING mode
def execute_openai_command(conversation_history, command, command_type):
    if TESTING:
        # If testing, read from pre-generated text files instead of making an API call
        if command_type == "summary":
            return read_from_file('summary_response.txt')
        elif command_type == "trivia":
            return read_from_file('trivia_response.txt')
        elif command_type == "imageprompt":
            return read_from_file('image_prompt_response.txt')
        else:
            return "Unknown command in TESTING mode."
    else:
        # Add user command to the conversation history
        conversation_history.append({"role": "user", "content": command})

        # Create a new thread by sending the entire conversation history to the assistant
        thread = openai.beta.threads.create(messages=conversation_history)

        # Start the assistant process (create the run)
        run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=OPENAI_ASSISTANT_ID)

        # Poll the status of the run until it is complete
        while run.status != "completed":
            run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            time.sleep(1)

        # Once the run is completed, retrieve the messages from the thread
        message_response = openai.beta.threads.messages.list(thread_id=thread.id)
        messages = message_response.data

        # Get the latest message (which contains the assistant's response)
        latest_message = messages[0]
        response = latest_message.content[0].text.value

        # Save the response for future testing
        if command_type == "summary":
            save_to_txt('summary_response.txt', response)
        elif command_type == "trivia":
            save_to_txt('trivia_response.txt', response)
        elif command_type == "imageprompt":
            save_to_txt('image_prompt_response.txt', response)

        # Add the assistant's response to the conversation history
        conversation_history.append({"role": "assistant", "content": response})

        return response

def generate_image_with_openai(prompt, output_path="imgtest.webp"):
    try:
        # Make the API call to generate the image
        response = openai.images.generate(
            model=IMG_MODEL,
            prompt=prompt,
            n=1,
            size=IMG_SIZE,  # Adjust the size as per your requirement
            response_format="b64_json"
        )
        
        # Decode the Base64 string into binary data
        image_data = base64.b64decode(response.data[0].b64_json)
        
        # Convert the binary data into an image using PIL
        image = Image.open(BytesIO(image_data))
        
        # Save the image in WebP format
        file_path = os.path.join(generation_dir,output_path)
        image.save(file_path, format="WEBP")
        
        return file_path
    except Exception as e:
        st.error(f"An error occurred while generating image: {e}")
        return None



# Function to read from a file in testing mode
def read_from_file(filename):
    filepath = os.path.join(debug_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    else:
        return "File not found"

# Function to save responses to text files for inspection
def save_to_txt(filename, content):
    filepath = os.path.join(generation_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)

def format_question_text(question_text):
    # Detect if the question and options are on the same line
    # and insert line breaks after each option
    formatted_text = re.sub(r'([A]\))', r'\n\1', question_text)
    
    # Ensure there's a newline after the question and before the first option
    #formatted_text = re.sub(r'\?([ \t]*)A\)', r'?\nA)', question_text)
    
    return formatted_text

# Function to split trivia questions (easy, medium, hard)
def split_trivia(text):
    try:
        easy_question = re.search(r"Easy Question:(.*?)(###|$)", text, re.DOTALL).group(1).strip()
    except AttributeError:
        easy_question = "No Easy Question Found"

    try:
        medium_question = re.search(r"Medium Question:(.*?)(###|$)", text, re.DOTALL).group(1).strip()
    except AttributeError:
        medium_question = "No Medium Question Found"

    try:
        hard_question = re.search(r"Hard Question:(.*)", text, re.DOTALL).group(1).strip()
    except AttributeError:
        hard_question = "No Hard Question Found"

    return easy_question, medium_question, hard_question

def split_trivia(text):
    try:
        # Extract the easy question without capturing the divider "---"
        easy_question = re.search(r"Easy Question:(.*?)(?=\n---|\n###|$)", text, re.DOTALL).group(1).strip()
    except AttributeError:
        easy_question = "No Easy Question Found"

    try:
        # Extract the medium question without capturing the divider "---"
        medium_question = re.search(r"Medium Question:(.*?)(?=\n---|\n###|$)", text, re.DOTALL).group(1).strip()
    except AttributeError:
        medium_question = "No Medium Question Found"

    try:
        # Extract the hard question (no need to worry about divider for the last question)
        hard_question = re.search(r"Hard Question:(.*)", text, re.DOTALL).group(1).strip()
    except AttributeError:
        hard_question = "No Hard Question Found"

    return easy_question, medium_question, hard_question
# Improved function to split image prompts by extracting the text between single quotes
def split_image_prompts(text):
    # Adjusted regex to account for possessive forms like "Legolas' child"
    matches = re.findall(r"'(.*?)'(?!\w|'s)", text, re.DOTALL)

    # Debug: Print the matches found
    if len(matches) < 3:
        print(f"Found {len(matches)} matches. Here they are: {matches}")

    # Assign the found matches to easy, medium, and hard prompts
    easy_prompt = matches[0].strip() if len(matches) > 0 else "No Easy Image Prompt Found"
    medium_prompt = matches[1].strip() if len(matches) > 1 else "No Medium Image Prompt Found"
    hard_prompt = matches[2].strip() if len(matches) > 2 else "No Hard Image Prompt Found"

    return easy_prompt, medium_prompt, hard_prompt

# Function to split image prompts based on "Create" and ending on line break, single quote, or dot followed by a line break
def split_image_prompts(text):
    # Use a non-greedy match and explicitly look for end markers like periods, single quotes, or line breaks
    matches = re.findall(r"(Create.*?)(?:\.\s*\n|\n|$|'(?!\w))", text, re.DOTALL)

    # Debug: Print the matches found
    if len(matches) < 3:
        print(f"Found {len(matches)} matches. Here they are: {matches}")

    # Assign the found matches to easy, medium, and hard prompts
    easy_prompt = matches[0].strip() if len(matches) > 0 else "No Easy Image Prompt Found"
    medium_prompt = matches[1].strip() if len(matches) > 1 else "No Medium Image Prompt Found"
    hard_prompt = matches[2].strip() if len(matches) > 2 else "No Hard Image Prompt Found"

    return easy_prompt, medium_prompt, hard_prompt

# Function to split the trivia question into question, answer, and explanation
# Function to split the trivia question into question, answer, and explanation
def split_trivia_question_answer(question):
    try:
        # Extract the question part before "**Answer" or "Answer"
        question_text = re.search(r"(.*?)(\*\*Answer:|Answer:)", question, re.DOTALL).group(1).strip()
        question_text = format_question_text(question_text)
    except AttributeError:
        question_text = "Error: Missing Question."
        print("Error: Missing Question in the provided trivia.")

    try:
        # Extract the answer part including the label "**Answer:" or "Answer:"
        answer_text = re.search(r"(\*\*Answer:|Answer:)(.*?)(?=\*\*Explanation:|Explanation:|$)", question, re.DOTALL).group(0).strip()
    except AttributeError:
        answer_text = "There is no Answer."
        print("Error: Missing Answer in the provided trivia.")

    try:
        # Extract the explanation part including the label "**Explanation:" or "Explanation:"
        explanation_text = re.search(r"(\*\*Explanation:|Explanation:)(.*)", question, re.DOTALL).group(0).strip()
    except AttributeError:
        explanation_text = "There is no Explanation."
        print("Error: Missing Explanation in the provided trivia.")

    # Return the results as a dictionary
    return {
        "question": question_text,
        "answer": answer_text,
        "explanation": explanation_text
    }


# Streamlit app
def main():
    st.title("Interactive OpenAI Assistant")

    # Initialize session state for conversation history and responses
    if 'conversation_history' not in st.session_state:
        st.session_state['conversation_history'] = []

    if 'summary_response' not in st.session_state:
        st.session_state['summary_response'] = None

    if 'trivia_response' not in st.session_state:
        st.session_state['trivia_response'] = None

    if 'image_prompt_response' not in st.session_state:
        st.session_state['image_prompt_response'] = None

    if 'easy_question' not in st.session_state:
        st.session_state['easy_question'] = None

    if 'medium_question' not in st.session_state:
        st.session_state['medium_question'] = None

    if 'hard_question' not in st.session_state:
        st.session_state['hard_question'] = None

    if 'easy_image_prompt' not in st.session_state:
        st.session_state['easy_image_prompt'] = None

    if 'medium_image_prompt' not in st.session_state:
        st.session_state['medium_image_prompt'] = None

    if 'hard_image_prompt' not in st.session_state:
        st.session_state['hard_image_prompt'] = None

    # Sidebar for input
    with st.sidebar:
        user_input = st.text_area("Enter your query:", value="Of Valanquenta from The Silmarillion", key="query_input")

        # Button to generate the summary, trivia, and image prompts
        if st.button("Get Summary & Trivia"):
            if user_input:
                with st.spinner("Fetching summary, trivia, and image prompts from the assistant..."):
                    try:
                        # Step 1: Get the summary response
                        summary_response = execute_openai_command(st.session_state['conversation_history'], user_input, "summary")
                        st.session_state['summary_response'] = summary_response

                        # Step 2: Generate Trivia based on the summary
                        trivia_response = execute_openai_command(st.session_state['conversation_history'], "/trivia", "trivia")
                        st.session_state['trivia_response'] = trivia_response

                        # Split trivia into easy, medium, and hard
                        easy_question, medium_question, hard_question = split_trivia(trivia_response)

                        # Split each difficulty into dictionary
                        easy_question_dictionary  = split_trivia_question_answer(easy_question)
                        medium_question_dictionary  = split_trivia_question_answer(medium_question)
                        hard_question_dictionary  = split_trivia_question_answer(hard_question)

                        # Assign dicitoonary with question/answer/explanation to each state
                        st.session_state['easy_question'] = easy_question_dictionary
                        st.session_state['medium_question'] = medium_question_dictionary
                        st.session_state['hard_question'] = hard_question_dictionary

                        # Step 3: Generate Image Prompt based on the trivia
                        image_prompt_response = execute_openai_command(st.session_state['conversation_history'], "For each trivia question, /imageprompt", "imageprompt")
                        st.session_state['image_prompt_response'] = image_prompt_response

                        # Split image prompts into easy, medium, and hard
                        easy_image_prompt, medium_image_prompt, hard_image_prompt = split_image_prompts(image_prompt_response)
                        st.session_state['easy_image_prompt'] = easy_image_prompt
                        st.session_state['medium_image_prompt'] = medium_image_prompt
                        st.session_state['hard_image_prompt'] = hard_image_prompt

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            else:
                st.warning("Please enter a valid query.")


    # Create tabs for summary and trivia
    if st.session_state['summary_response']:
        tab1, tab2 = st.tabs(["Summary", "Trivia & Image Prompts"])

        with tab1:
            st.subheader("Summary Response")
            st.write(st.session_state['summary_response'])

        with tab2:
            # Dropdown to select difficulty level
            difficulty = st.selectbox("Select difficulty level", ["Easy", "Medium", "Hard"])

######### EASY #########

            if difficulty == "Easy":
                st.write("**Trivia Question:**")
                st.write(st.session_state['easy_question']['question'])

                # Add show/hide toggle for the answer
                if st.checkbox("Show Answer", key="easy_answer"):    
                    st.write(st.session_state['easy_question']['answer'])
                    st.write(st.session_state['easy_question']['explanation'])  
                st.write("---")

                # Ensure the session state for the generated image is initialized
                if 'generated_image_easy' not in st.session_state:
                    st.session_state['generated_image_easy'] = None

                # Add the "Generate Image" button
                if st.button("Generate Image", key="generate_image_easy"):
                    if TESTING:
                        ## IMAGE NON GENERATED (TEST)
                        image_path = os.path.join(test_image_path, "easy_image.webp")
                        if os.path.exists(image_path):
                            # Save the image path in session state for persistence
                            st.session_state['generated_image_easy'] = image_path
                        else:
                            st.write("No image found for Easy difficulty.")
                    else:
                        ## AI IMAGE GENERATION
                        image_easy_path = generate_image_with_openai(st.session_state['easy_image_prompt'], output_path="easy_image.webp")  # GENERATE PATH
                        if os.path.exists(image_easy_path):
                            st.session_state['generated_image_easy'] = image_easy_path
                        

                # If the image has been generated, display it persistently
                if st.session_state['generated_image_easy'] is not None:
                    st.image(st.session_state['generated_image_easy'], caption=st.session_state['easy_image_prompt'], use_column_width=True)
                else:
                    st.write("**Image Prompt:**")
                    st.write(st.session_state['easy_image_prompt'])

######### MEDIUM #########



            elif difficulty == "Medium":
                st.write("**Trivia Question:**")
                st.write(st.session_state['medium_question']['question'])

                # Add show/hide toggle for the answer
                if st.checkbox("Show Answer", key="medium_answer"):    
                    st.write(st.session_state['medium_question']['answer'])
                    st.write(st.session_state['medium_question']['explanation'])

                st.write("---")

                if 'generated_image_medium' not in st.session_state:
                    st.session_state['generated_image_medium'] = None

                # Add the "Generate Image" button
                if st.button("Generate Image", key="generate_image_medium"):
                    if TESTING:
                        image_path = os.path.join(test_image_path, "medium_image.webp")
                        if os.path.exists(image_path):
                            st.session_state['generated_image_medium'] = image_path
                        else:
                            st.write("No image found for Medium difficulty.")
                    else:
                        ## AI IMAGE GENERATION
                        image_medium_path = generate_image_with_openai(st.session_state['medium_image_prompt'], output_path="medium_image.webp")  
                        if os.path.exists(image_medium_path):
                            st.session_state['generated_image_medium'] = image_medium_path
                
                # If the image has been generated, display it persistently
                if st.session_state['generated_image_medium'] is not None:
                    st.image(st.session_state['generated_image_medium'], caption=st.session_state['medium_image_prompt'], use_column_width=True)
                else:
                    st.write("**Image Prompt:**")
                    st.write(st.session_state['medium_image_prompt'])

######### HARD #########

            elif difficulty == "Hard":
                st.write("**Trivia Question:**")
                st.write(st.session_state['hard_question']['question'])
                # Add show/hide toggle
                if st.checkbox("Show Answer", key="easy_answer"):    
                    st.write(st.session_state['hard_question']['answer'])
                    st.write(st.session_state['hard_question']['explanation'])

                st.write("---")

                if 'generated_image_hard' not in st.session_state:
                    st.session_state['generated_image_hard'] = None

                # Add the "Generate Image" button
                if st.button("Generate Image", key="generate_image_hard"):
                    if TESTING:
                        image_path = os.path.join(test_image_path, "hard_image.webp")
                        if os.path.exists(image_path):
                            st.session_state['generated_image_hard'] = image_path
                        else:
                            st.write("No image found for Hard difficulty.")
                    else:
                        ## AI IMAGE GENERATION
                        image_hard_path = generate_image_with_openai(st.session_state['hard_image_prompt'], output_path="hard_image.webp")  
                        if os.path.exists(image_hard_path):
                            st.session_state['generated_image_hard'] = image_hard_path
                
                
                # If the image has been generated, display it persistently
                if st.session_state['generated_image_hard'] is not None:
                    st.image(st.session_state['generated_image_hard'], caption=st.session_state['hard_image_prompt'], use_column_width=True)
                else:
                    st.write("**Image Prompt:**")
                    st.write(st.session_state['hard_image_prompt'])

# Run the app
if __name__ == "__main__":
    main()

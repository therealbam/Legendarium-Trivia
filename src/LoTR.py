import time
import streamlit as st
import openai
import os
import re

import base64
from PIL import Image
from io import BytesIO
from datetime import datetime

# Set TESTING to True to read from pre-generated text files, False to use OpenAI API
TESTING = False

# Load environmental variables
from dotenv import load_dotenv

# Set the port to listen on
port = int(os.environ.get('PORT', 8080))

# Check if we are in production or development
if os.getenv('ENVIRONMENT') != 'PRODUCTION':
    load_dotenv()  # Only load .env file if not in production

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

PROMPT_INIT="[Request a summary of a Chapter of Silmarillion or information about specific Characters or events]"
IMG_MODEL =  "dall-e-3"   #"dall-e-3"      #dall-e-2" 
IMG_SIZE = '1792x1024'   #'1792x1024'     "1024x1024"

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

def generate_image_with_openai(prompt, output_dir, output_filename="imgtest.webp"):
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
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Existing code to generate and save image...
        file_path = os.path.join(output_dir, output_filename)
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


# Function to display trivia question and handle image generation
def display_trivia_section(difficulty_key, question_data_key, image_prompt_key):
    # Retrieve the question data from session state
    question_data = st.session_state[question_data_key]
    
    st.write("**Trivia Question:**")
    st.write(question_data['question'])
    
    # Add show/hide toggle for the answer
    if st.checkbox("Show Answer", key=f"{difficulty_key}_answer"):    
        st.write(question_data['answer'])
        st.write(question_data['explanation'])
    
    st.write("---")
    
    # Initialize session state for the generated image if not already done
    generated_image_key = f'generated_image_{difficulty_key}'
    if generated_image_key not in st.session_state:
        st.session_state[generated_image_key] = None
    
    # Define the image filename based on difficulty
    output_image_name = f"{difficulty_key}_image.webp"


    # Use the output directory from session state
    output_dir = st.session_state['output_dir']

    
    # Add the "Generate Image" button
    if st.button("Generate Image", key=f"generate_image_{difficulty_key}"):
        if TESTING:
            # Use predefined image paths for testing
            test_dir = test_image_path
            image_path = os.path.join(test_dir, output_image_name)
            if os.path.exists(image_path):
                # Save the image path in session state for persistence
                st.session_state[generated_image_key] = image_path
            else:
                st.write(f"No image found for {difficulty_key.capitalize()} difficulty.")
        else:
            # Generate the image using OpenAI API
            image_path = generate_image_with_openai(
                st.session_state[image_prompt_key],
                output_dir= output_dir,
                output_filename=output_image_name
            )
            if image_path:
                st.session_state[generated_image_key] = image_path
            else:
                st.error("Failed to generate image.")
    
    # Display the image if it has been generated
    if st.session_state[generated_image_key] is not None:
        st.image(
            st.session_state[generated_image_key],
            caption=st.session_state[image_prompt_key],
            use_column_width=True
        )
    else:
        st.write("**Image Prompt:**")
        st.write(st.session_state[image_prompt_key])


# Streamlit app
def main():
    st.title("Legendarium - An AI Trivia & Image Generator")

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

    if 'output_dir' not in st.session_state:
        st.session_state['output_dir'] = None

    # Sidebar for input
    with st.sidebar:
        user_input = st.text_area("Enter your query:", value=PROMPT_INIT, key="query_input")

        # Button to generate the summary, trivia, and image prompts
        if st.button("Get Summary & Trivia"):
            if user_input:

                if not TESTING:
                    #Generate a new output directory
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    output_dir = os.path.join(generation_dir, f"run_{timestamp}")
                    os.makedirs(output_dir, exist_ok=True)
                    st.session_state['output_dir'] = output_dir

                with st.spinner("Fetching summary, trivia, and image prompts from the assistant..."):
                    try:
                        # Step 1: Get & Save the summary response
                        summary_response = execute_openai_command(st.session_state['conversation_history'], user_input, "summary")
                        st.session_state['summary_response'] = summary_response
                        
                        if not TESTING: 
                            summary_file_path = os.path.join(output_dir, "summary.txt")
                            with open(summary_file_path, 'w') as f:
                                f.write(summary_response)

                        # Step 2: Generate Trivia based on the summary
                        trivia_response = execute_openai_command(st.session_state['conversation_history'], "/trivia", "trivia")
                        st.session_state['trivia_response'] = trivia_response

                        if not TESTING: 
                            trivia_file_path = os.path.join(output_dir, "trivia.txt")
                            with open(trivia_file_path, 'w') as f:
                                f.write(trivia_response)

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
            # Map difficulty levels to their corresponding session state keys
            difficulty_keys = {
                "Easy": {
                    "question_data_key": "easy_question",
                    "image_prompt_key": "easy_image_prompt"
                },
                "Medium": {
                    "question_data_key": "medium_question",
                    "image_prompt_key": "medium_image_prompt"
                },
                "Hard": {
                    "question_data_key": "hard_question",
                    "image_prompt_key": "hard_image_prompt"
                }
            }
            
            # Get the keys for the selected difficulty
            keys = difficulty_keys[difficulty]
            
            # Call the reusable function with appropriate keys
            display_trivia_section(
                difficulty_key=difficulty.lower(),
                question_data_key=keys["question_data_key"],
                image_prompt_key=keys["image_prompt_key"]
            )


# Run the app
if __name__ == "__main__":
    main()

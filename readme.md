# Legendarium Trivia

**Legendarium Trivia** is a trivia application built with **Streamlit** that generates questions and prompts about Tolkien's *Legendarium* using OpenAI. It supports image generation and features multiple difficulty levels for trivia, including **Easy**, **Medium**, and **Hard**. The project is Dockerized and can be easily deployed using Docker or Google Cloud.

## Features

- **Trivia Questions**: Generate trivia questions about Tolkien's works (*The Silmarillion*, *The Lord of the Rings*, etc.) with easy, medium, and hard difficulty levels.
- **Image Generation**: Automatically generate image prompts for each trivia question.
- **API Integration**: Uses OpenAI to generate trivia questions, summaries, and more.
- **Streamlit Web Interface**: Provides an interactive user interface for users to interact with the trivia and image generation features.
- **Dockerized**: The application can be easily deployed in any environment using Docker.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python** (>= 3.8)
- **Streamlit** (for running the web app)
- **Docker** (for containerized deployment)
- **OpenAI API Key** (required for generating trivia and images)
- **Google Cloud Account** (optional for deployment on Google Cloud Run)

## Project Structure

/Legendarium ├── .devcontainer/ # VS Code dev container settings ├── .dockerignore # Docker ignore rules ├── .gitignore # Git ignore rules ├── .vscode/ # VS Code launch and task settings ├── Dockerfile # Docker build configuration ├── main.py # Main entry point for the Streamlit app ├── img/ # Contains debug response files and image assets ├── readme.md # Project readme file ├── requirements.txt # Python dependencies ├── src/ # Source code for trivia generation │ ├── LoTR.py # Trivia-related functions │ └── lotr_temp.py # Temporary or experimental code └── .env # (excluded) Environment file for API keys


## Getting Started

### Clone the Repository

To get a copy of the project up and running on your local machine:

```bash
git clone https://github.com/therealbam/Legendarium-Trivia.git
cd Legendarium-Trivia
```

### Install Dependencies
You can install the required Python packages using:
```bash
pip install -r requirements.txt
```
Make sure you have an .env file containing your OpenAI API key:
```bash
# .env
OPENAI_API_KEY=your-openai-api-key
```

## Running the Application

### To run the application locally, use Streamlit:

```bash
streamlit run __main__.py
```

### Docker

You can also run the application using Docker:

#### Build the Docker image:

```bash
docker build -t legendarium-trivia .
```

#### Run the Docker container:

```bash
docker run -p 8501:8501 legendarium-trivia
```

### Google Cloud Deployment

To deploy this application on Google Cloud Run:

#### Build and push the Docker image to Google Container Registry (GCR):

```bash
docker build -t gcr.io/<your-project-id>/legendarium-trivia .
docker push gcr.io/<your-project-id>/legendarium-trivia
```

#### Deploy on Google Cloud Run:

```bash
gcloud run deploy --image gcr.io/<your-project-id>/legendarium-trivia --platform managed
```

The deployed app will provide you with a URL to access the running app.

## Usage

### Generating Trivia Questions

Once the application is running, the user can input a query related to Tolkien's universe to generate trivia questions. The trivia is categorized into **Easy**, **Medium**, and **Hard** difficulties, and each question has an associated image prompt that can be generated.

### Toggle Answers

Users can toggle answers for each trivia question by clicking the "Show Answer" checkbox.

### Image Generation

If the testing mode is disabled, clicking the "Generate Image" button will trigger the generation of images based on the trivia.

## Environment Variables

Make sure to set the following environment variables in your `.env` file:

```plaintext
OPENAI_API_KEY=your-openai-api-key
```

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push the changes (`git push origin feature-branch`).
5. Open a pull request.

## License

This project is open-source and available under the MIT License.

## Acknowledgements

- **OpenAI**: For the trivia generation API.
- **Streamlit**: For providing the UI framework.
- **Tolkien’s Legendarium**: For the rich source material.

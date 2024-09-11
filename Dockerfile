# Use a lightweight version of Python 3.8
FROM python:3.8-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Update and install necessary dependencies
RUN apt-get update && \
    apt-get -y install git gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt -v

# Install additional dependency for tvdatafeed package
RUN pip install --upgrade --no-cache-dir git+https://github.com/rongardF/tvdatafeed.git

# Set the working directory in the container
WORKDIR /app

# Copy the content of the app to the working directory
COPY . /app

# Expose the default port used by Streamlit
EXPOSE 8501

# Command to run the Streamlit app, update this path to src/LoTR.py
CMD ["streamlit", "run", "src/LoTR.py", "--server.port=8501", "--server.address=0.0.0.0"]

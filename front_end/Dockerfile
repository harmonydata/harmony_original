FROM python:3.10
# Create a directory where the code is to be hosted

RUN pip install sentence-transformers==2.2.2
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
RUN pip install spacy==3.2.3
# Make sure Spacy language model is downloaded
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download pt_core_news_sm


RUN mkdir /app
# Define the working directory in the container
WORKDIR /app
# Copy and install the requirements.
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
# Copy application code to the image
COPY . /app/

# Define environment variables
ENV dash_port=80
ENV dash_debug=False

ARG COMMIT_ID="No commit ID specified"
ENV COMMIT_ID=$COMMIT_ID

CMD ["python", "application.py"]


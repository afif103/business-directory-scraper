import os
import shutil
import re
import pandas as pd
import json
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Load environment variables for API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def scrape_business_directory(url: str):
    """
    Scrape a business directory page and extract business information.
    """
    # Load the web page
    loader = WebBaseLoader(url)
    documents = loader.load()

    # Split the text for processing
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Clear previous vector store
    if os.path.exists("./chroma_db"):
        try:
            shutil.rmtree("./chroma_db")
        except OSError:
            pass  # Ignore if locked

    # Create vector store
    vectorstore = Chroma.from_documents(texts, embeddings, persist_directory="./chroma_db")

    # Initialize LLM
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key="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")

    # Define prompt for extraction
    prompt_template = """
    Extract business information from the following text. Output as a JSON array of objects, where each object has keys: name, address, phone, email, services, website_url.

    If information is not available, use null or empty string.

    Text: {context}

    JSON Output:
    """

    prompt = PromptTemplate(template=prompt_template, input_variables=["context"])

    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )

    # Query to extract all businesses
    query = "Extract all business listings from the directory."
    result = qa_chain.run(query)

    # Parse the result into structured data
    businesses = parse_businesses(result)
    if businesses:
        return businesses
    else:
        return result  # Fallback to raw text

def parse_businesses(text):
    """
    Parse the LLM output into a list of business dictionaries.
    """
    try:
        # Try to parse as JSON
        start = text.find('[')
        end = text.rfind(']') + 1
        if start != -1 and end != -1:
            json_str = text[start:end]
            businesses = json.loads(json_str)
            return businesses
    except json.JSONDecodeError:
        pass
    # Fallback to old parsing if JSON fails
    businesses = []
    business_blocks = re.split(r'Business \d+:', text)
    for block in business_blocks[1:]:
        business = {}
        lines = block.strip().split('\n')
        for line in lines:
            if ': ' in line:
                key, value = line.split(': ', 1)
                key = key.strip().lower().replace(' ', '_')
                business[key] = value.strip()
        if business:
            businesses.append(business)
    return businesses

if __name__ == "__main__":
    # Example usage
    url = "https://example.com/business-directory"  # Replace with actual URL
    businesses = scrape_business_directory(url)
    print(businesses)
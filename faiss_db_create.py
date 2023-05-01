import os
from dotenv import load_dotenv
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader

load_dotenv()

openai_api_key = os.environ["OPENAI_API_KEY"]

data_dir = 'data'
documents = TextLoader(os.path.join(data_dir, 'all_count.csv')).load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()

db = FAISS.from_documents(docs, embeddings)


db.save_local("faiss_index")
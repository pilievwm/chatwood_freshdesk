import os
from dotenv import load_dotenv
from langchain.document_transformers import EmbeddingsRedundantFilter
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain.text_splitter import CharacterTextSplitter
from langchain.retrievers.document_compressors import LLMChainFilter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.chat_models import ChatOpenAI

load_dotenv()

openai_api_key = os.environ["OPENAI_API_KEY"]
embeddings = OpenAIEmbeddings()

def pretty_print_docs(docs):
    return f"\n{'-'}\n".join([d.page_content for i, d in enumerate(docs)])


# Create retriever and index documents

retriever = FAISS.load_local("faiss_index",embeddings).as_retriever()



llm = ChatOpenAI(model='gpt-3.5-turbo',temperature=0)


splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=0, separator=". ")
redundant_filter = EmbeddingsRedundantFilter(embeddings=embeddings)
relevant_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.83, k=2)
# _filter = LLMChainFilter.from_llm(llm)
# compressor = LLMChainExtractor.from_llm(llm)
pipeline_compressor = DocumentCompressorPipeline(
    transformers=[splitter, redundant_filter, relevant_filter]
)
compression_retriever = ContextualCompressionRetriever(base_compressor=pipeline_compressor, base_retriever=retriever)

#llm = OpenAI(temperature=0)
#compressor = LLMChainExtractor.from_llm(llm)
#compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)

def answer_db(message_text):
    compressed_docs = compression_retriever.get_relevant_documents(message_text)
    answer = pretty_print_docs(compressed_docs)
    return answer
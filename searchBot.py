import numpy as np
import openai
import pandas as pd
import tiktoken
import os
from dotenv import load_dotenv
from main import *
from searchDB import *

load_dotenv()

openai.api_key = os.getenv("OPEN_AI")


# Update the models to use
EMBEDDING_MODEL = "text-embedding-ada-002"

# Read the CSV into a pandas DataFrame
data_dir = 'data'
df = pd.read_csv(os.path.join(data_dir, 'all_count.csv'))
df = df.set_index(["title"])

def get_embedding(text: str, model: str=EMBEDDING_MODEL) -> list[float]:
    try:
        result = openai.Embedding.create(
          model=model,
          input=text
        )
        return result["data"][0]["embedding"]
    except openai.error.RateLimitError:
        print("Please try again later.")

def load_embeddings(fname: str) -> dict[tuple[str, str], list[float]]:
    
    df = pd.read_csv(fname, header=0)
    max_dim = max([int(c) for c in df.columns if c != "title"])
    return {
           (r.title): [r[str(i)] for i in range(max_dim + 1)] for _, r in df.iterrows()
    }

# Compute the embeddings for each row in the DataFrame
document_embeddings = load_embeddings(os.path.join(data_dir, 'all_embeddings.csv'))

def vector_similarity(x: list[float], y: list[float]) -> float:
    return np.dot(np.array(x), np.array(y))

def order_document_sections_by_query_similarity(query: str, contexts: dict[(str, str), np.array], num_results: int = 3, similarity_threshold: float = 0.5) -> list[(float, (str, str))]:
    query_embedding = get_embedding(query)
    
    document_similarities = sorted([
        (vector_similarity(query_embedding, doc_embedding), doc_index) for doc_index, doc_embedding in contexts.items()
    ], reverse=True)
    
    filtered_document_similarities = [(similarity, doc_index) for similarity, doc_index in document_similarities if similarity >= similarity_threshold]
    
    return filtered_document_similarities[:num_results]


MAX_SECTION_LEN = 1200
MIN_SECTION_LEN = 20
SEPARATOR = "\n* "
ENCODING = "cl100k_base"  # encoding for text-embedding-ada-002

encoding = tiktoken.get_encoding(ENCODING)
separator_len = len(encoding.encode(SEPARATOR))

f"Context separator contains {separator_len} tokens"

def construct_prompt(search: str, context_embeddings: dict, df: pd.DataFrame, num_results: int = 3) -> str:

    most_relevant_document_sections = order_document_sections_by_query_similarity(search, context_embeddings, num_results, similarity_threshold=0.8)

    chosen_sections = []
    chosen_sections_len = 0
    chosen_sections_indexes = []

    for _, section_index in most_relevant_document_sections:
        document_section = df.loc[section_index]
        if isinstance(document_section, pd.DataFrame):
            document_section = document_section.iloc[0]
        section_text = document_section['description']
        section_length = len(section_text.split())
        if section_length < MIN_SECTION_LEN:
            continue
        chosen_sections_len += section_length + separator_len

        if chosen_sections_len > MAX_SECTION_LEN:
            break
                
        chosen_sections.append(section_text.replace("\n", " "))
        chosen_sections_indexes.append(str(section_index))
    
    return "\n".join(chosen_sections)




def answer_query_with_context(
    query: str,
    df: pd.DataFrame,
    document_embeddings: dict[(str, str), np.array],
    num_results: int = 3,
    show_prompt: bool = False
) -> str:

    prompt = construct_prompt(
        query,
        document_embeddings,
        df,
        num_results
    )

    return prompt


def answer_bot(message_text, num_results):
    answer = answer_query_with_context(message_text, df, document_embeddings, num_results)
    
    return answer

"""
def main():
    parser = argparse.ArgumentParser(description="Get the answer for a query using the answer_bot function.")
    parser.add_argument("message_text", help="The hardcoded query to search for")
    parser.add_argument("num_results", type=int, help="The number of results to display")
    args = parser.parse_args()
    answer = answer_bot(args.message_text, args.num_results)
    print(answer)

if __name__ == '__main__':
    main()



def answer_bot(message_text, num_results):
    search_result = answer_query_with_context(message_text, df, document_embeddings, num_results)

    # Using GPT-3.5-turbo to find the most suitable answer
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Just find the most suitable block of text for answer to the user question. If there is no sutable text, return empty - {search_result}. "},
            {"role": "user", "content": message_text}
        ]
    )

    answer = response['choices'][0]['message']['content']
    return answer
"""
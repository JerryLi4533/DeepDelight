# Mengyang's langchain imports
# from langchain.document_loaders import JSONLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.embeddings import GPT4AllEmbeddings
# from langchain.vectorstores import Chroma
# from langchain.llms import GPT4All
# from langchain.chains import RetrievalQA

# Weimao's langchain import on Mac
from langchain_community.document_loaders import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import GPT4All
from langchain.chains import RetrievalQA

# Additional imports
from collections import Counter
import numpy as np
from collections import defaultdict
import json
from pathlib import Path
from langchain.prompts import PromptTemplate
import logging
import time
from langchain.embeddings.huggingface import HuggingFaceInstructEmbeddings
import torch
import pandas as pd
import nltk
from nltk.tokenize import sent_tokenize

#The link of the files is https://github.com/salesforce/QAConv/tree/master/dataset, which in QAConv-V1.0.zip
# file_path='E:/QA/article_segment.json' #The file here should be article_segment.txt, but its actual structure is json file
file_path = "/Users/wk77/Documents/data/QAConv-V1.0/article_segment.json"
data = json.loads(Path(file_path).read_text())
# QA = pd.read_json("E:/QAConv-V1.0/QAConv-V1.0/sample.json") #For the file here, either trn.json, tst.json or val.json can be used as Question_Answer data
QA = pd.read_json("/Users/wk77/Documents/data/QAConv-V1.0/trn.json")
QA['text']=''
for i in range(len(QA)):
    text=''
    for j in data[QA.iloc[i]['article_segment_id']]['prev_ctx']:
        text+=j['text']
    for k in data[QA.iloc[i]['article_segment_id']]["seg_dialog"]:
        text+=k['text']
    QA.loc[i,'text']=text

# save and reuse processed data? 
file_path2 = "/Users/wk77/Documents/data/QAConv-V1.0/QA_data_sample.json"
QA.to_json(file_path2, orient='records') #The file path here should be the same as the following line
combined_data = json.loads(Path(file_path2).read_text())

from nltk.tokenize import word_tokenize
import collections

def compute_f1(a_gold, a_pred):
    gold_toks = word_tokenize(a_gold)
    pred_toks = word_tokenize(a_pred)
    common = collections.Counter(gold_toks) & collections.Counter(pred_toks)
    num_same = sum(common.values())
    
    if len(gold_toks) == 0 or len(pred_toks) == 0:
        # If either is no-answer, then F1 is 1 if they agree, 0 otherwise
        return int(gold_toks == pred_toks)
    
    if num_same == 0:
        return 0
    
    precision = 1.0 * num_same / len(pred_toks)
    recall = 1.0 * num_same / len(gold_toks)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1

def compute_precision(a_gold, a_pred):
    gold_toks = word_tokenize(a_gold)
    pred_toks = word_tokenize(a_pred)
    common = collections.Counter(gold_toks) & collections.Counter(pred_toks)
    num_same = sum(common.values())
    
    if len(gold_toks) == 0 or len(pred_toks) == 0:
        # If either is no-answer, then F1 is 1 if they agree, 0 otherwise
        return int(gold_toks == pred_toks)
    
    if num_same == 0:
        return 0
    
    precision = 1.0 * num_same / len(pred_toks)
    recall = 1.0 * num_same / len(gold_toks)
    f1 = (2 * precision * recall) / (precision + recall)
    return precision

def compute_recall(a_gold, a_pred):
    gold_toks = word_tokenize(a_gold)
    pred_toks = word_tokenize(a_pred)
    common = collections.Counter(gold_toks) & collections.Counter(pred_toks)
    num_same = sum(common.values())
    
    if len(gold_toks) == 0 or len(pred_toks) == 0:
        # If either is no-answer, then F1 is 1 if they agree, 0 otherwise
        return int(gold_toks == pred_toks)
    
    if num_same == 0:
        return 0
    
    precision = 1.0 * num_same / len(pred_toks)
    recall = 1.0 * num_same / len(gold_toks)
    f1 = (2 * precision * recall) / (precision + recall)
    return recall
'''
#Modified template
template = """Based on the following information only: 

"{context}"

{question} Please provide the answer in as few words as possible and please do NOT repeat any word in the question, i.e. "{question}". 
"""
QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
llm = GPT4All(model="E:/ggml-model-gpt4all-falcon-q4_0.bin", max_tokens=2048)

instruct_embedding_model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
# instruct_embedding_model_kwargs = {'device': 'cpu'}
instruct_embedding_model_kwargs = {'device': 'mps'}
instruct_embedding_encode_kwargs = {'normalize_embeddings': True}


answers_pairs=[]
model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
# model_kwargs = {'device': 'cpu'}
model_kwargs = {'device': 'mps'}
encode_kwargs = {'normalize_embeddings': True}

def process_story_questions(combined_data, model_name, instruction,chunk_size,overlap_percentage):
    word_embed = HuggingFaceInstructEmbeddings(
        model_name=instruct_embedding_model_name,
        model_kwargs=instruct_embedding_model_kwargs,
        encode_kwargs=instruct_embedding_encode_kwargs,
        embed_instruction="Represent the story for retrieval:"
    )

    for cov in combined_data:
        all_splits = text_splitter.split_text(cov['text'])
        vectorstore = Chroma.from_texts(texts=all_splits, embedding=word_embed)
        qa_chain = RetrievalQA.from_chain_type(llm, retriever=vectorstore.as_retriever(), return_source_documents=True, chain_type_kwargs={"prompt": QA_CHAIN_PROMPT})

        question = cov['question']
        hf_query_embs = HuggingFaceInstructEmbeddings(
            model_name=instruct_embedding_model_name,
            model_kwargs=instruct_embedding_model_kwargs,
            encode_kwargs=instruct_embedding_encode_kwargs,
            query_instruction=instruction
        )
        question_emb = hf_query_embs.embed_query(question)
        docs = vectorstore.similarity_search_by_vector(question_emb)
        predict = qa_chain({"query": question})
        answers_pairs.append((cov['answers'],predict,chunk_size,overlap_percentage))

model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
instruction = "Represent the story for retrieval:" 
#Try different chunk sizes and overlap percentages
chunk_sizes = [100, 200]
overlap_percentages = [0, 0.1]
for i in chunk_sizes:
    for j in overlap_percentages:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=i, chunk_overlap=j)
        process_story_questions(combined_data, model_name, instruction, i, j)

for i in answers_pairs:
    f1_score = compute_f1(i[0][0],i[1]['result'])
    precision = compute_precision(i[0][0],i[1]['result'])
    recall = compute_recall(i[0][0],i[1]['result'])
    print(f"For chunk_size {i[2]} and chunk_overlap {i[3]}")
    print(f"Question: {i[1]['query']}")
    print(f"Predicted Answer: {i[1]['result']}")
    print(f"Actual Answer: {i[0][0]}")
    print(f"F1 Score: {f1_score:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    retrieved_sentences = i[1].get('source_documents', [])
    print("\nRetrieved Sentence(s):")
    for sentence in retrieved_sentences:
        print(sentence)
    print()
'''
answers_pairs=[]
text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0.1)
model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
# model_kwargs = {'device': 'cpu'}
model_kwargs = {'device': 'mps'}
encode_kwargs = {'normalize_embeddings': True}

def process_story_questions(combined_data, model_name, instruction):
    hf_story_embs = HuggingFaceInstructEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
        embed_instruction="Use the following pieces of context to answer the question at the end:"
    )

    for cov in combined_data:
        sentences = sent_tokenize(cov['text'])
        sentence_embs = hf_story_embs.embed_documents(sentences)
        #all_splits = text_splitter.split_text(cov['text'])
        #vectorstore = Chroma.from_texts(texts=all_splits, embedding=word_embed)
        #qa_chain = RetrievalQA.from_chain_type(llm, retriever=vectorstore.as_retriever(), return_source_documents=True)

        question = cov['question'] 
        hf_query_embs = HuggingFaceInstructEmbeddings(
            model_name=model_name,
            model_kwargs=instruct_embedding_model_kwargs,
            encode_kwargs=instruct_embedding_encode_kwargs,
            query_instruction=instruction
        )
        question_emb = hf_query_embs.embed_query(question)
        scores = [torch.cosine_similarity(torch.tensor(sentence_emb).unsqueeze(0), torch.tensor(question_emb).unsqueeze(0))[0].item() for sentence_emb in sentence_embs]
        
        best_sentence_idx = scores.index(max(scores))
        best_sentence = sentences[best_sentence_idx]
        
        
        #docs = vectorstore.similarity_search_by_vector(question_emb)
        #predict = qa_chain({"query": question})
        answers_pairs.append((cov['question'],cov['answers'],best_sentence))
        
    
instruct_embedding_model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
# instruct_embedding_model_kwargs = {'device': 'cpu'}
instruct_embedding_model_kwargs = {'device': 'mps'}
instruct_embedding_encode_kwargs = {'normalize_embeddings': True}
model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
instruction = "Represent the story for retrieval:" 
process_story_questions(combined_data, model_name, instruction)
result_list=[]
for i in answers_pairs:
    f1_score = compute_f1(i[1][0],i[2])
    precision = compute_precision(i[1][0],i[2])
    recall = compute_recall(i[1][0],i[2])
    '''
    print(f"Question: {i[0]}")
    print(f"Predicted Answer: {i[2]}")
    print(f"Actual Answer: {i[1][0]}")
    print(f"F1 Score: {f1_score:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print()
    '''
    result_list.append([i[0],i[2],i[1][0],f1_score,precision,recall])

df=pd.DataFrame({'Quesion':[],'Predicted Answer':[],'Actual Answer':[],'f1 score':[],'Precision':[],'Recall':[]})
while((len(df))!=(len(result_list))):
    df.loc[len(df)]=result_list[len(df)]
df.to_csv('../results/qaconv_output.csv', index=False)


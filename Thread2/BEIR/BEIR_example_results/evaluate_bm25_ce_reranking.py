from beir import util, LoggingHandler
from beir.datasets.data_loader import GenericDataLoader
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.lexical import BM25Search as BM25
from beir.reranking.models import CrossEncoder
from beir.reranking import Rerank

import pathlib, os
import logging
import random

# Added for Lixiao's local machine
from beir.retrieval.search.lexical.elastic_search import ElasticSearch
from elasticsearch import Elasticsearch

#### Just some code to print debug information to stdout
logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    handlers=[LoggingHandler()])
#### /print debug information to stdout

#### Download trec-covid.zip dataset and unzip the dataset
dataset = "scifact"
url = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{}.zip".format(dataset)
out_dir = os.path.join(pathlib.Path(__file__).parent.absolute(), "datasets")
data_path = util.download_and_unzip(url, out_dir)

#### Provide the data path where trec-covid has been downloaded and unzipped to the data loader
# data folder would contain these files: 
# (1) trec-covid/corpus.jsonl  (format: jsonlines)
# (2) trec-covid/queries.jsonl (format: jsonlines)
# (3) trec-covid/qrels/test.tsv (format: tsv ("\t"))

corpus, queries, qrels = GenericDataLoader(data_path).load(split="test")

#########################################
#### (1) RETRIEVE Top-100 docs using BM25
#########################################

#### Provide parameters for Elasticsearch
hostname = "https://localhost:9200" #localhost
index_name = "reranking" # trec-covid
initialize = True # False

######### Added for Lixiao's local machine #########
elastic_password = "Mf5wAwVTOwk2VMYnrJwz"

# Initialize Elasticsearch with SSL verification
es_client = Elasticsearch(
    [hostname],
    http_auth=('elastic', elastic_password),
    use_ssl=True,
    verify_certs=True,
    ca_certs='C:/Users/24075/http_ca.crt'  # Path to your CA certificate
)

# Update the ElasticSearch class to use the configured es_client
config = {
    "hostname": hostname,
    "index_name": index_name,
    "keys": {"title": "title", "body": "txt"},
    "timeout": 100,
    "retry_on_timeout": True,
    "maxsize": 24,
    "number_of_shards": "default",
    "language": "english"
}

elastic_search = ElasticSearch(config)
elastic_search.es = es_client

###############################

model = BM25(index_name=index_name, hostname=hostname, initialize=initialize)

###### Added for Lixiao's local machine ######
model.es = elastic_search
###########################################

retriever = EvaluateRetrieval(model)

#### Retrieve dense results (format of results is identical to qrels)
results = retriever.retrieve(corpus, queries)

################################################
#### (2) RERANK Top-100 docs using Cross-Encoder
################################################

#### Reranking using Cross-Encoder models #####
#### https://www.sbert.net/docs/pretrained_cross-encoders.html
# cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-electra-base')

#### Or use MiniLM, TinyBERT etc. CE models (https://www.sbert.net/docs/pretrained-models/ce-msmarco.html)
# cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
# cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-6')
cross_encoder_name = 'cross-encoder/ms-marco-TinyBERT-L-2-v2'
print(f"\nThe cross encoder model used is: {cross_encoder_name}.\n")
cross_encoder_model = CrossEncoder(cross_encoder_name)

reranker = Rerank(cross_encoder_model, batch_size=128)

# Rerank top-100 results using the reranker provided
rerank_results = reranker.rerank(corpus, queries, results, top_k=100)

#### Evaluate your retrieval using NDCG@k, MAP@K ...
ndcg, _map, recall, precision = EvaluateRetrieval.evaluate(qrels, rerank_results, retriever.k_values)

#### Print top-k documents retrieved ####
top_k = 10

query_id, ranking_scores = random.choice(list(rerank_results.items()))
scores_sorted = sorted(ranking_scores.items(), key=lambda item: item[1], reverse=True)
logging.info("Query : %s\n" % queries[query_id])

for rank in range(top_k):
    doc_id = scores_sorted[rank][0]
    # Format: Rank x: ID [Title] Body
    logging.info("Rank %d: %s [%s] - %s\n" % (rank+1, doc_id, corpus[doc_id].get("title"), corpus[doc_id].get("text")))
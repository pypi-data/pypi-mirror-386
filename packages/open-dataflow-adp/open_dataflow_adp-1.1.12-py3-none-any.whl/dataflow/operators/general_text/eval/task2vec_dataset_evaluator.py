from dataflow.operators.general_text.eval.task2vec.task2vec import Task2Vec
from dataflow.operators.general_text.eval.task2vec import task_similarity
import torch
import random
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from dataflow.utils.storage import DataFlowStorage
from dataflow.core import OperatorABC
from dataflow.utils.registry import OPERATOR_REGISTRY
from torch.utils.data import Dataset
from dataflow import get_logger
from typing import Optional
# Task2Vec dataset diversity evaluation
# Cited from: Beyond Scale: the Diversity Coefficient as a Data Quality Metric Demonstrates LLMs are Pre-trained on Formally Diverse Data
@OPERATOR_REGISTRY.register()
class Task2VecDatasetEvaluator(OperatorABC):
    def __init__(self, device='cuda', sample_nums=10, sample_size=1, method: Optional[str]='montecarlo', model_cache_dir='./dataflow_cache'):
        self.logger = get_logger()
        self.logger.info(f'Initializing {self.__class__.__name__}...')
        # evaluating diversity by extract sample_nums * sample_size samples
        self.sample_nums = sample_nums  
        self.sample_size = sample_size  
        self.device = device
        self.model_cache_dir = model_cache_dir  
        self.score_name = 'Task2VecScore'
        self.method = method
        if method not in ['montecarlo', 'variational']:
            raise ValueError(f"Invalid method '{method}'. Valid options are 'montecarlo' and 'variational'.")
        self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2', cache_dir=self.model_cache_dir)
        self.probe_network = GPT2LMHeadModel.from_pretrained('gpt2', cache_dir=self.model_cache_dir)
        self.device = torch.device(self.device if self.device and torch.cuda.is_available() else "cpu")
        self.probe_network = self.probe_network.to(self.device)
        self.logger.info(f'{self.__class__.__name__} initialized.')
    
    @staticmethod
    def get_desc(lang: str = "zh"):
        if lang == "zh":
            return (
                "使用Task2Vec方法评估数据集的多样性，通过计算样本嵌入的余弦距离矩阵来量化多样性。\n"
                "输入参数：\n"
                "- device：计算设备，默认为'cuda'\n"
                "- sample_nums：采样次数，默认为10\n"
                "- sample_size：每次采样样本数，默认为1\n"
                "- method：嵌入方法，可选'montecarlo'或'variational'，默认为'montecarlo'\n"
                "- model_cache_dir：模型缓存目录，默认为'./dataflow_cache'\n"
                "- input_key：输入文本字段名\n"
                "输出参数：\n"
                "- Task2VecDiversityScore：多样性得分\n"
                "- ConfidenceInterval：置信区间"
            )
        elif lang == "en":
            return (
                "Evaluate dataset diversity using Task2Vec by calculating cosine distance matrix of sample embeddings.\n"
                "Input Parameters:\n"
                "- device: Computing device, default 'cuda'\n"
                "- sample_nums: Number of sampling iterations, default 10\n"
                "- sample_size: Number of samples per iteration, default 1\n"
                "- method: Embedding method, 'montecarlo' or 'variational', default 'montecarlo'\n"
                "- model_cache_dir: Model cache directory, default './dataflow_cache'\n"
                "- input_key: Field name for input text\n"
                "Output Parameters:\n"
                "- Task2VecDiversityScore: Diversity score\n"
                "- ConfidenceInterval: Confidence interval"
            )
        else:
            return "Evaluate dataset diversity using Task2Vec method."
    
    def preprocess(self, texts):
        self.tokenizer.pad_token = self.tokenizer.eos_token
        tokenized_outputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        return {key: value.to(self.device) for key, value in tokenized_outputs.items()}

    def get_score(self, sentences):
        embeddings = []
        data_length = len(sentences)
        for sample_num in range(self.sample_nums):
            self.logger.info(f'--> Sample {sample_num + 1}/{self.sample_nums}')
            indices = random.sample(range(data_length), self.sample_size)
            texts = [sentences[i] for i in indices]
            tokenized_batch = self.preprocess(texts)
            tokenized_dataset = CustomTensorDataset(tokenized_batch)
            embedding, _ = Task2Vec(self.probe_network, method=self.method).embed(tokenized_dataset)
            embeddings.append(embedding)
        distance_matrix = task_similarity.pdist(embeddings, distance='cosine')
        div_coeff, conf_interval = task_similarity.stats_of_distance_matrix(distance_matrix)
        
        return {
            "Task2VecDiversityScore": div_coeff,
            "ConfidenceInterval": conf_interval
        }

    def run(self, storage: DataFlowStorage, input_key: str):
        dataframe = storage.read("dataframe")
        samples = dataframe[input_key].to_list()
        self.logger.info(f"Evaluating {self.score_name}...")
        task2vec_score = self.get_score(samples)
        self.logger.info("Evaluation complete!")
        self.logger.info(f"Task2Vec Diversity Score: {task2vec_score}")
        return task2vec_score


class CustomTensorDataset(Dataset):
    def __init__(self, tokenized_batch):
        self.tokenized_batch = tokenized_batch

    def __getitem__(self, index):
        return {key: self.tokenized_batch[key][index] for key in self.tokenized_batch}

    def __len__(self):
        return len(next(iter(self.tokenized_batch.values())))

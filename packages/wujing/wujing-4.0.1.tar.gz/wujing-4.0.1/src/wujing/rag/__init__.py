"""检索增强生成（RAG）模块

本模块包含向量数据库、检索器、重排序等RAG相关功能。
"""

# 延迟导入，避免在包初始化时就加载依赖
def __getattr__(name):
    """延迟导入模块以避免依赖问题"""
    if name == "Embedder":
        from .embedder import Embedder
        return Embedder
    elif name == "Reranker":
        from .reranker import Reranker
        return Reranker
    elif name == "BM25Retriever":
        from .bm25retriever import BM25Retriever
        return BM25Retriever
    elif name == "ChineseTokenizer":
        from .tokenizer import ChineseTokenizer
        return ChineseTokenizer
    elif name == "MixedLanguageStemmer":
        from .stemmer import MixedLanguageStemmer
        return MixedLanguageStemmer
    elif name == "split_markdown_by_headers":
        from .markdown import split_markdown_by_headers
        return split_markdown_by_headers
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "Embedder",
    "Reranker", 
    "BM25Retriever",
    "ChineseTokenizer",
    "MixedLanguageStemmer",
    "split_markdown_by_headers",
]
import os

from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_ollama import OllamaEmbeddings
from langchain_experimental.text_splitter import SemanticChunker

# 项目根目录（src/load/load_file.py 向上两级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZILIAO_DIR = os.path.join(BASE_DIR, "ziliao")

# 文件后缀 -> 对应的 Loader
LOADERS = {
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".docx": UnstructuredWordDocumentLoader,
}


def load_and_split_documents(
    ziliao_dir: str = ZILIAO_DIR,
    embedding_model: str = "nomic-embed-text",
    breakpoint_threshold_type: str = "percentile",
    breakpoint_threshold_amount: float = 95,
):
    """遍历 ziliao 目录（含子目录），每读取一个文件就立即进行语义分割。

    使用 Ollama 嵌入模型 + SemanticChunker，根据语义相似度变化自动识别边界，
    而非按固定字符数切割。

    Args:
        ziliao_dir: 资料目录路径
        embedding_model: Ollama 嵌入模型名称（默认 nomic-embed-text，也可用 bge-m3）
        breakpoint_threshold_type: 断点阈值类型，可选 "percentile" / "standard_deviation" / "interquartile"
        breakpoint_threshold_amount: 断点阈值数值，percentile 下 95 表示仅在相似度变化最大的 5% 位置切段

    返回：(所有加载到的原始文档, 所有语义分割后的文本块)
    """
    embeddings = OllamaEmbeddings(model=embedding_model)
    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type=breakpoint_threshold_type,
        breakpoint_threshold_amount=breakpoint_threshold_amount,
    )

    documents = []
    splits = []
    for root, _, files in os.walk(ziliao_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            loader_cls = LOADERS.get(ext)
            if loader_cls is None:
                continue
            file_path = os.path.join(root, file)
            # TextLoader 支持指定编码，避免 Windows 下默认 GBK 解码失败
            if loader_cls is TextLoader:
                loader = loader_cls(file_path, encoding="utf-8")
            else:
                loader = loader_cls(file_path)

            # 读取单个文件后立即语义分割
            file_docs = loader.load()
            documents.extend(file_docs)
            file_splits = splitter.split_documents(file_docs)
            splits.extend(file_splits)

            print(
                f"- 已读取 {file_path}: "
                f"{len(file_docs)} 个文档, 语义分割为 {len(file_splits)} 个文本块"
            )
    return documents, splits


if __name__ == "__main__":
    docs, splits = load_and_split_documents()
    print(f"\n共加载 {len(docs)} 个文档")
    print(f"语义分割后得到 {len(splits)} 个文本块")

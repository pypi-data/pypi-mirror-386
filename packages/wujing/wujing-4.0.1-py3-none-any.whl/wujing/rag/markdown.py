from typing import List, Optional
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core import Document
from llama_index.core.schema import BaseNode
import re


class MarkdownProcessor:
    """Markdown 文档处理器，用于将 Markdown 文本解析为节点"""

    def __init__(
        self,
        include_metadata: bool = True,
        include_prev_next_rel: bool = True,
        chunk_size: Optional[int] = None,
        chunk_overlap: int = 200,
    ):
        """
        初始化 Markdown 处理器

        Args:
            include_metadata: 是否包含元数据
            include_prev_next_rel: 是否包含前后节点关系
            chunk_size: 最大块大小（字符数）。如果指定，将使用 SentenceSplitter 进行二次分割
            chunk_overlap: 块重叠大小，默认为 200
        """
        self.include_metadata = include_metadata
        self.include_prev_next_rel = include_prev_next_rel
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 使用 MarkdownNodeParser 作为主解析器
        self.parser = MarkdownNodeParser(include_metadata=include_metadata, include_prev_next_rel=include_prev_next_rel)

        # 如果指定了 chunk_size，创建二级分割器
        self.secondary_parser = (
            SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                include_metadata=include_metadata,
                include_prev_next_rel=include_prev_next_rel,
            )
            if chunk_size is not None
            else None
        )

    def _extract_section_title(self, content: str) -> Optional[str]:
        """
        从内容中提取第一个标题作为section_title（标题应在第一行）

        Args:
            content: 文本内容

        Returns:
            提取到的第一个标题，如果没有则返回None
        """
        # 匹配markdown标题格式 (# 标题)，只检查第一行
        title_pattern = r'^#+\s+(.+)$'
        lines = content.split('\n')
        
        if lines:
            first_line = lines[0].strip()
            match = re.match(title_pattern, first_line)
            if match:
                return match.group(1).strip()

        return None

    def parse_markdown_text(self, markdown_text: str) -> List[BaseNode]:
        """
        解析 Markdown 文本为节点列表

        Args:
            markdown_text: Markdown 文本内容

        Returns:
            解析后的节点列表
        """
        documents = [Document(text=markdown_text)]

        # 先用 MarkdownNodeParser 分割
        markdown_nodes = self.parser.get_nodes_from_documents(documents)

        # 如果没有二级分割器，直接返回结果
        if self.secondary_parser is None:
            return markdown_nodes

        # 使用二级分割器对超过大小限制的节点进行细分
        final_nodes = []
        for md_node in markdown_nodes:
            # 为md_node添加section_title
            section_title = self._extract_section_title(md_node.get_content())
            if section_title:
                if not hasattr(md_node, "metadata") or md_node.metadata is None:
                    md_node.metadata = {}
                md_node.metadata["section_title"] = section_title

            # 如果节点内容超过 chunk_size，使用二级分割器
            if len(md_node.get_content()) > self.chunk_size:
                sub_documents = [Document(text=md_node.get_content())]
                sub_nodes = self.secondary_parser.get_nodes_from_documents(sub_documents)

                # 保留原始节点的元数据并添加子块索引
                for idx, sub_node in enumerate(sub_nodes):
                    if hasattr(md_node, "metadata") and md_node.metadata:
                        if not hasattr(sub_node, "metadata") or sub_node.metadata is None:
                            sub_node.metadata = {}
                        sub_node.metadata.update(md_node.metadata)

                    # 添加子块索引信息
                    if not hasattr(sub_node, "metadata") or sub_node.metadata is None:
                        sub_node.metadata = {}
                    sub_node.metadata["sub_chunk_index"] = idx
                    sub_node.metadata["total_sub_chunks"] = len(sub_nodes)
                    sub_node.metadata["is_sub_chunk"] = True

                final_nodes.extend(sub_nodes)
            else:
                final_nodes.append(md_node)

        return final_nodes

    def parse_markdown_file(self, file_path: str, encoding: str = "utf-8") -> List[BaseNode]:
        """
        解析 Markdown 文件为节点列表

        Args:
            file_path: Markdown 文件路径
            encoding: 文件编码，默认为 utf-8

        Returns:
            解析后的节点列表
        """
        with open(file_path, "r", encoding=encoding) as f:
            markdown_text = f.read()
        return self.parse_markdown_text(markdown_text)


def create_processor(
    chunk_size: Optional[int] = None,
    chunk_overlap: int = 200,
    include_metadata: bool = True,
    include_prev_next_rel: bool = True,
) -> MarkdownProcessor:
    """
    创建 Markdown 处理器

    Args:
        chunk_size: 最大块大小（字符数）。如果为 None，则只按 Markdown 结构分割
        chunk_overlap: 块重叠大小，默认为 200
        include_metadata: 是否包含元数据，默认为 True
        include_prev_next_rel: 是否包含前后节点关系，默认为 True

    Returns:
        配置好的 MarkdownProcessor 实例
    """
    return MarkdownProcessor(
        include_metadata=include_metadata,
        include_prev_next_rel=include_prev_next_rel,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

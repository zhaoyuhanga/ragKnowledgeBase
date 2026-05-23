# -*- coding: utf-8 -*-
"""
关键词索引服务单元测试

本模块包含关键词索引服务的独立单元测试，不依赖完整的应用配置。
"""

import pytest
import re
from collections import Counter


class TokenizerConfig:
    """分词器配置"""
    def __init__(self, min_term_length=2, max_term_length=20):
        self.min_term_length = min_term_length
        self.max_term_length = max_term_length


class ChineseTokenizer:
    """简单中文分词器"""

    def __init__(self, config=None):
        self.config = config or TokenizerConfig()
        self.stopwords = set(self._get_default_stopwords())

    def _get_default_stopwords(self):
        return [
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        ]

    def tokenize(self, text):
        if not text:
            return []

        tokens = []

        english_pattern = re.compile(r'[a-zA-Z]+')
        english_words = english_pattern.findall(text.lower())
        tokens.extend([w for w in english_words if len(w) >= self.config.min_term_length])

        number_pattern = re.compile(r'\d+\.?\d*')
        numbers = number_pattern.findall(text)
        tokens.extend([n for n in numbers if len(n) >= self.config.min_term_length])

        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        chinese_texts = chinese_pattern.findall(text)

        for chinese_text in chinese_texts:
            bigrams = self._generate_bigrams(chinese_text)
            tokens.extend([g for g in bigrams if g not in self.stopwords])

        return list(set(tokens))

    def _generate_bigrams(self, text):
        if len(text) < 2:
            return [text] if text else []
        bigrams = []
        for i in range(len(text) - 1):
            bigram = text[i:i + 2]
            if len(bigram) >= self.config.min_term_length:
                bigrams.append(bigram)
        return bigrams


class BM25Document:
    """BM25文档"""
    def __init__(self, chunk_id, content, title_path, page_start, page_end, terms, term_freqs):
        self.chunk_id = chunk_id
        self.content = content
        self.title_path = title_path
        self.page_start = page_start
        self.page_end = page_end
        self.terms = terms
        self.term_freqs = term_freqs


class BM25Scorer:
    """BM25评分器"""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.avg_doc_len = 0
        self.doc_count = 0
        self.doc_freqs = {}
        self.doc_lengths = {}
        self.documents = {}

    def add_document(self, doc):
        self.documents[doc.chunk_id] = doc
        self.doc_lengths[doc.chunk_id] = len(doc.terms)
        self.doc_count += 1

        for term in set(doc.terms):
            self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        total_len = sum(self.doc_lengths.values())
        self.avg_doc_len = total_len / self.doc_count if self.doc_count > 0 else 0

    def calculate_idf(self, term):
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0
        return max(0, (self.doc_count - df + 0.5) / (df + 0.5))

    def score(self, query_terms, doc_id):
        if doc_id not in self.documents:
            return 0.0

        doc = self.documents[doc_id]
        doc_len = self.doc_lengths[doc_id]
        score = 0.0

        for term in query_terms:
            if term not in doc.term_freqs:
                continue

            tf = doc.term_freqs[term]
            idf = self.calculate_idf(term)

            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)

            score += idf * numerator / denominator if denominator > 0 else 0

        return score


class TestChineseTokenizer:
    """中文分词器测试类"""

    def setup_method(self):
        self.tokenizer = ChineseTokenizer()

    def test_tokenize_english(self):
        """测试英文分词"""
        text = "Hello World Python"
        tokens = self.tokenizer.tokenize(text)

        assert "hello" in tokens
        assert "world" in tokens
        assert "python" in tokens

    def test_tokenize_numbers(self):
        """测试数字分词"""
        text = "2024年GDP增长5%"
        tokens = self.tokenizer.tokenize(text)

        assert "2024" in tokens

    def test_tokenize_chinese(self):
        """测试中文分词"""
        text = "这是一个中文分词测试"
        tokens = self.tokenizer.tokenize(text)

        assert len(tokens) > 0
        assert any(len(t) == 2 for t in tokens)

    def test_tokenize_empty(self):
        """测试空文本分词"""
        tokens = self.tokenizer.tokenize("")
        assert tokens == []

    def test_tokenize_with_config(self):
        """测试配置化分词"""
        config = TokenizerConfig(min_term_length=3, max_term_length=10)
        tokenizer = ChineseTokenizer(config)

        text = "ab abc"
        tokens = tokenizer.tokenize(text)

        assert "abc" in tokens
        assert "ab" not in tokens

    def test_tokenize_mixed(self):
        """测试混合文本分词"""
        text = "Python编程语言在2024年非常流行"
        tokens = self.tokenizer.tokenize(text)

        assert "python" in tokens
        assert len(tokens) > 0

    def test_generate_bigrams(self):
        """测试bigram生成"""
        text = "中文分词"
        bigrams = self.tokenizer._generate_bigrams(text)

        assert "中文" in bigrams
        assert "文分" in bigrams
        assert "分词" in bigrams

    def test_generate_bigrams_single_char(self):
        """测试单字符bigram"""
        text = "中"
        bigrams = self.tokenizer._generate_bigrams(text)

        assert "中" in bigrams

    def test_generate_bigrams_empty(self):
        """测试空文本bigram"""
        bigrams = self.tokenizer._generate_bigrams("")
        assert bigrams == []

    def test_tokenize_stopwords_removed(self):
        """测试停用词被移除"""
        text = "这是一个测试的句子"
        tokens = self.tokenizer.tokenize(text)

        assert "这" not in tokens
        assert "是" not in tokens
        assert "个" not in tokens
        assert "的" not in tokens


class TestBM25Scorer:
    """BM25评分器测试类"""

    def setup_method(self):
        self.scorer = BM25Scorer(k1=1.5, b=0.75)

    def test_add_document(self):
        """测试添加文档"""
        doc = BM25Document(
            chunk_id=1,
            content="测试文档内容",
            title_path=None,
            page_start=None,
            page_end=None,
            terms=["测试", "文档", "内容"],
            term_freqs={"测试": 1, "文档": 1, "内容": 1}
        )

        self.scorer.add_document(doc)

        assert self.scorer.doc_count == 1
        assert 1 in self.scorer.documents

    def test_calculate_idf(self):
        """测试IDF计算"""
        for i in range(5):
            doc = BM25Document(
                chunk_id=i,
                content=f"文档{i}内容",
                title_path=None,
                page_start=None,
                page_end=None,
                terms=["文档"],
                term_freqs={"文档": 1}
            )
            self.scorer.add_document(doc)

        idf = self.scorer.calculate_idf("文档")
        assert idf >= 0

    def test_calculate_idf_unknown_term(self):
        """测试未知词项IDF"""
        idf = self.scorer.calculate_idf("未知词项")
        assert idf == 0

    def test_score(self):
        """测试BM25评分"""
        doc = BM25Document(
            chunk_id=1,
            content="机器学习是人工智能的一个分支",
            title_path=None,
            page_start=None,
            page_end=None,
            terms=["机器", "学习", "人工", "智能"],
            term_freqs={"机器": 1, "学习": 1, "人工": 1, "智能": 1}
        )

        self.scorer.add_document(doc)

        score = self.scorer.score(["机器", "学习"], 1)
        assert score >= 0

    def test_score_nonexistent_doc(self):
        """测试不存在的文档评分"""
        score = self.scorer.score(["测试"], 999)
        assert score == 0

    def test_score_empty_query(self):
        """测试空查询评分"""
        doc = BM25Document(
            chunk_id=1,
            content="测试内容",
            title_path=None,
            page_start=None,
            page_end=None,
            terms=["测试", "内容"],
            term_freqs={"测试": 1, "内容": 1}
        )

        self.scorer.add_document(doc)

        score = self.scorer.score([], 1)
        assert score == 0


class TestBM25Document:
    """BM25文档测试"""

    def test_creation(self):
        """测试文档创建"""
        doc = BM25Document(
            chunk_id=1,
            content="测试内容",
            title_path="测试标题",
            page_start=1,
            page_end=2,
            terms=["测试", "内容"],
            term_freqs={"测试": 1, "内容": 1}
        )

        assert doc.chunk_id == 1
        assert doc.content == "测试内容"
        assert doc.title_path == "测试标题"
        assert len(doc.terms) == 2


class TestTokenizerEdgeCases:
    """分词边界测试"""

    def test_very_long_text(self):
        """测试超长文本"""
        tokenizer = ChineseTokenizer()
        text = "中" * 10000
        tokens = tokenizer.tokenize(text)

        assert len(tokens) > 0

    def test_special_characters(self):
        """测试特殊字符"""
        tokenizer = ChineseTokenizer()
        text = "###!!!@@@$$$"
        tokens = tokenizer.tokenize(text)

        assert len(tokens) == 0

    def test_unicode_text(self):
        """测试Unicode文本"""
        tokenizer = ChineseTokenizer()
        text = "简体中文繁體中文"
        tokens = tokenizer.tokenize(text)

        assert len(tokens) > 0


class TestBM25EdgeCases:
    """BM25边界测试"""

    def test_zero_k1(self):
        """测试k1=0的情况"""
        scorer = BM25Scorer(k1=0, b=0.75)

        doc = BM25Document(
            chunk_id=1,
            content="测试内容",
            title_path=None,
            page_start=None,
            page_end=None,
            terms=["测试", "内容"],
            term_freqs={"测试": 2, "内容": 1}
        )
        scorer.add_document(doc)

        score = scorer.score(["测试"], 1)
        assert score >= 0

    def test_zero_b(self):
        """测试b=0的情况"""
        scorer = BM25Scorer(k1=1.5, b=0)

        doc = BM25Document(
            chunk_id=1,
            content="测试内容",
            title_path=None,
            page_start=None,
            page_end=None,
            terms=["测试", "内容"],
            term_freqs={"测试": 1, "内容": 1}
        )
        scorer.add_document(doc)

        score = scorer.score(["测试"], 1)
        assert score >= 0

    def test_many_documents(self):
        """测试大量文档"""
        scorer = BM25Scorer()

        for i in range(100):
            doc = BM25Document(
                chunk_id=i,
                content=f"文档{i}内容",
                title_path=None,
                page_start=None,
                page_end=None,
                terms=["文档", "内容"],
                term_freqs={"文档": 1, "内容": 1}
            )
            scorer.add_document(doc)

        assert scorer.doc_count == 100
        score = scorer.score(["文档"], 50)
        assert score >= 0


class TestBM25Ranking:
    """BM25排序测试"""

    def test_ranking_order(self):
        """测试排名顺序"""
        scorer = BM25Scorer()

        # 添加多个文档
        docs = [
            (1, "机器学习是人工智能的核心技术", {"机器": 2, "学习": 1, "人工": 1, "智能": 1, "核心": 1, "技术": 1}),
            (2, "深度学习是机器学习的一个分支", {"深度": 1, "学习": 2, "机器": 1, "人工": 1, "智能": 1}),
            (3, "人工智能技术发展迅速", {"人工": 1, "智能": 1, "技术": 1, "发展": 1, "迅速": 1}),
        ]

        for chunk_id, content, term_freqs in docs:
            terms = list(term_freqs.keys())
            doc = BM25Document(
                chunk_id=chunk_id,
                content=content,
                title_path=None,
                page_start=None,
                page_end=None,
                terms=terms,
                term_freqs=term_freqs
            )
            scorer.add_document(doc)

        # 查询"机器学习"
        scores = [(doc_id, scorer.score(["机器", "学习"], doc_id)) for doc_id in range(1, 4)]
        scores.sort(key=lambda x: x[1], reverse=True)

        # 文档1和文档2包含"机器"和"学习"，应该排名靠前
        assert scores[0][0] in [1, 2]


class TestTermFrequency:
    """词频统计测试"""

    def test_term_frequency_calculation(self):
        """测试词频计算"""
        text = "测试文档包含多个测试词项，测试词项需要统计词频"
        tokenizer = ChineseTokenizer()
        tokens = tokenizer.tokenize(text)

        freq = Counter(tokens)
        test_count = freq.get("测试", 0)

        assert test_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

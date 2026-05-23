# -*- coding: utf-8 -*-
"""
清洗服务测试

测试清洗服务的各项功能：
- 编码修复与乱码检测
- 噪声过滤
- 重复检测
- 敏感信息脱敏
- 质量评分
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.clean_service import (
    CleanService,
    CleanedElement,
    CleaningConfig,
    CleaningContext,
    CleaningReport,
    DESENSITIZATION_PATTERNS,
    GARBLED_PATTERNS,
    NOISE_PATTERNS,
)
from app.models.parse import DocumentElement


class TestCleanService:
    """清洗服务测试类"""

    def setup_method(self):
        """测试前准备"""
        self.service = CleanService()

    def test_fix_encoding_basic(self):
        """测试基本编码修复"""
        text = "这是一个测试文档"
        fixed, issues = self.service._fix_encoding(text)
        assert fixed == text
        assert len(issues) == 0

    def test_fix_encoding_with_control_chars(self):
        """测试控制字符移除"""
        text = "测试\x00文档\x07内容"
        fixed, issues = self.service._fix_encoding(text)
        assert "\x00" not in fixed
        assert "\x07" not in fixed
        assert "测试" in fixed
        assert "文档" in fixed

    def test_fix_encoding_with_whitespace(self):
        """测试空白字符归一化"""
        text = "测试    文档\n\n内容"
        fixed, issues = self.service._fix_encoding(text)
        assert "  " not in fixed
        assert "\n\n" not in fixed

    def test_desensitize_phone(self):
        """测试手机号脱敏"""
        text = "联系电话：13812345678"
        desensitized, done = self.service._desensitize(text)
        assert "13812345678" not in desensitized
        assert "138****1234" in desensitized
        assert done is True

    def test_desensitize_id_card(self):
        """测试身份证号脱敏"""
        text = "身份证号：310101199001011234"
        desensitized, done = self.service._desensitize(text)
        assert "310101199001011234" not in desensitized
        assert "310***********1234" in desensitized
        assert done is True

    def test_desensitize_email(self):
        """测试邮箱脱敏"""
        text = "邮箱：test@example.com"
        desensitized, done = self.service._desensitize(text)
        assert "test@example.com" not in desensitized
        assert "user@example.com" in desensitized
        assert done is True

    def test_desensitize_no_sensitive(self):
        """测试无敏感信息文本"""
        text = "这是一段普通文本，没有任何敏感信息。"
        desensitized, done = self.service._desensitize(text)
        assert desensitized == text
        assert done is False

    def test_check_duplicate_exact(self):
        """测试精确重复检测"""
        context = CleaningContext(document_id=1, version_id=1)
        context.seen_contents = ["这是一段文本"]

        is_duplicate, similarity = self.service._check_duplicate("这是一段文本", context)
        assert is_duplicate is True
        assert similarity == 1.0

    def test_check_duplicate_similar(self):
        """测试相似重复检测"""
        context = CleaningContext(document_id=1, version_id=1)
        context.seen_contents = ["这是一段完全相同的文本内容"]

        is_duplicate, similarity = self.service._check_duplicate("这是一段完全相同的文本内容测试", context)
        assert is_duplicate is True
        assert similarity >= 0.85

    def test_check_duplicate_unique(self):
        """测试唯一内容检测"""
        context = CleaningContext(document_id=1, version_id=1)
        context.seen_contents = ["这是第一段文本"]

        is_duplicate, similarity = self.service._check_duplicate("这是完全不同的另一段文本", context)
        assert is_duplicate is False

    def test_score_quality_good(self):
        """测试高质量评分"""
        text = "这是一个正常长度的文本内容，包含足够的信息量用于评估。" * 5
        score, flag, issues = self.service._score_quality(text, 1.0)
        assert score >= 0.7
        assert flag == "good"
        assert len(issues) == 0

    def test_score_quality_short(self):
        """测试过短文本评分"""
        text = "短"
        score, flag, issues = self.service._score_quality(text, 1.0)
        assert "文本内容过短" in issues
        assert flag != "good"

    def test_apply_cleaning_rules_delete(self):
        """测试正则删除规则"""
        text = "这是第1页的内容"
        context = CleaningContext(document_id=1, version_id=1)

        # 添加页眉删除规则
        from app.services.clean_service import CleaningRuleItem
        context.rules = [
            CleaningRuleItem(
                rule_id=1,
                name="页眉清洗",
                rule_type="regex_delete",
                config={"patterns": [r"^第\s*\d+\s*页$", r"^Page\s+\d+$"]},
                priority=10
            )
        ]

        cleaned, applied = self.service._apply_cleaning_rules(text, context)
        assert "第1页" not in cleaned
        assert "页眉清洗" in applied

    def test_apply_cleaning_rules_replace(self):
        """测试正则替换规则"""
        text = "测试    多余   空格"
        context = CleaningContext(document_id=1, version_id=1)

        # 添加空白归一化规则
        from app.services.clean_service import CleaningRuleItem
        context.rules = [
            CleaningRuleItem(
                rule_id=2,
                name="空白归一化",
                rule_type="regex_replace",
                config={"pattern": r"\s+", "replacement": " "},
                priority=20
            )
        ]

        cleaned, applied = self.service._apply_cleaning_rules(text, context)
        assert "    " not in cleaned
        assert "空白归一化" in applied

    def test_clean_element_full_pipeline(self):
        """测试完整清洗流程"""
        # 创建测试元素
        element = MagicMock(spec=DocumentElement)
        element.element_id = "test-001"
        element.content = "联系电话：13912345678\n这是正文内容"
        element.confidence = 0.9

        context = CleaningContext(document_id=1, version_id=1)
        config = CleaningConfig()

        report = self.service._clean_element(element, context, config)

        assert report.element_id == "test-001"
        assert "13912345678" not in report.cleaned_content
        assert "敏感信息脱敏" in report.applied_rules
        assert report.quality_score > 0

    def test_clean_config_defaults(self):
        """测试默认配置"""
        config = CleaningConfig()
        assert config.enable_encoding_fix is True
        assert config.enable_noise_removal is True
        assert config.enable_duplicate_detection is True
        assert config.enable_desensitization is True
        assert config.enable_quality_scoring is True
        assert config.quality_threshold == 0.5

    def test_calculate_garbled_ratio(self):
        """测试乱码比例计算"""
        normal_text = "这是一个正常的中文文本"
        ratio = self.service._calculate_garbled_ratio(normal_text)
        assert ratio == 0.0

        # 包含替换字符的文本
        bad_text = "测试\ufffd\ufffd文本"
        ratio = self.service._calculate_garbled_ratio(bad_text)
        assert ratio > 0

    def test_calculate_valid_ratio(self):
        """测试有效字符比例计算"""
        valid_text = "这是一个123中文文本。"
        ratio = self.service._calculate_valid_ratio(valid_text)
        assert ratio > 0.5

    def test_compute_hash(self):
        """测试哈希计算"""
        hash1 = self.service._compute_hash("测试文本")
        hash2 = self.service._compute_hash("测试文本")
        hash3 = self.service._compute_hash("不同文本")

        assert hash1 == hash2
        assert hash1 != hash3

        # 大小写不敏感
        hash4 = self.service._compute_hash("TEST")
        hash5 = self.service._compute_hash("test")
        assert hash4 == hash5


class TestDesensitizationPatterns:
    """脱敏模式测试"""

    def test_phone_pattern(self):
        """测试手机号正则"""
        import re
        pattern = DESENSITIZATION_PATTERNS["手机号"][0]

        # 有效手机号
        assert re.search(pattern, "13812345678")
        assert re.search(pattern, "19912345678")

        # 无效手机号
        assert not re.search(pattern, "1234567890")
        assert not re.search(pattern, "1381234567")  # 不足11位

    def test_id_card_pattern(self):
        """测试身份证号正则"""
        import re
        pattern = DESENSITIZATION_PATTERNS["身份证号"][0]

        # 有效身份证号
        assert re.search(pattern, "310101199001011234")
        assert re.search(pattern, "11010519880505321X")

    def test_email_pattern(self):
        """测试邮箱正则"""
        import re
        pattern = DESENSITIZATION_PATTERNS["邮箱"][0]

        # 有效邮箱
        assert re.search(pattern, "test@example.com")
        assert re.search(pattern, "user.name@domain.co.uk")


class TestNoisePatterns:
    """噪声模式测试"""

    def test_header_footer_patterns(self):
        """测试页眉页脚模式"""
        import re

        patterns = NOISE_PATTERNS["页眉页脚"]
        assert any(re.search(p, "第1页") for p in patterns)
        assert any(re.search(p, "Page 1") for p in patterns)
        assert any(re.search(p, "1/10") for p in patterns)

    def test_watermark_patterns(self):
        """测试水印模式"""
        import re

        patterns = NOISE_PATTERNS["水印"]
        assert any(re.search(p, "草稿") for p in patterns)
        assert any(re.search(p, "机密") for p in patterns)
        assert any(re.search(p, "Draft") for p in patterns)


class TestCleaningReport:
    """清洗报告测试"""

    def test_report_creation(self):
        """测试报告创建"""
        report = CleaningReport(
            element_id="test-001",
            original_content="原始内容",
            cleaned_content="清洗后内容",
            applied_rules=["规则1"],
            issues=["问题1"],
            quality_score=0.8,
            quality_flag="good",
            is_duplicate=False
        )

        assert report.element_id == "test-001"
        assert report.quality_score == 0.8
        assert len(report.applied_rules) == 1
        assert len(report.issues) == 1

    def test_report_modification(self):
        """测试报告修改"""
        report = CleaningReport(
            element_id="test-001",
            original_content="原始内容",
            cleaned_content="清洗后内容"
        )

        report.applied_rules.append("新规则")
        report.issues.append("新问题")

        assert len(report.applied_rules) == 1
        assert len(report.issues) == 1


class TestCleaningContext:
    """清洗上下文测试"""

    def test_context_creation(self):
        """测试上下文创建"""
        context = CleaningContext(document_id=1, version_id=1)

        assert context.document_id == 1
        assert context.version_id == 1
        assert len(context.rules) == 0
        assert len(context.seen_contents) == 0

    def test_context_with_rules(self):
        """测试带规则的上下文"""
        from app.services.clean_service import CleaningRuleItem

        rules = [
            CleaningRuleItem(
                rule_id=1,
                name="规则1",
                rule_type="regex_delete",
                config={},
                priority=10
            )
        ]

        context = CleaningContext(document_id=1, version_id=1, rules=rules)
        assert len(context.rules) == 1
        assert context.rules[0].name == "规则1"

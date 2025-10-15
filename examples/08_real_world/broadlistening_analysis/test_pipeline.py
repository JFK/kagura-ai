"""
Tests for Broadlistening Analysis Pipeline

Run with: pytest test_pipeline.py -v
"""

import pytest
from pipeline import Comment, Opinion
from filtering import PropertyFilter


# ============================================
# Filtering Tests
# ============================================


def test_property_filter_single_value():
    """Test filtering by single property value"""
    opinions = [
        Opinion(id="A1", text="意見1", comment_id="C1", properties={"gender": "女性"}),
        Opinion(id="A2", text="意見2", comment_id="C2", properties={"gender": "男性"}),
        Opinion(id="A3", text="意見3", comment_id="C3", properties={"gender": "女性"}),
    ]

    filter_obj = PropertyFilter(opinions)
    result = filter_obj.filter(gender="女性")

    assert len(result) == 2
    assert all(op.properties["gender"] == "女性" for op in result)


def test_property_filter_multiple_values():
    """Test filtering by multiple property values (OR)"""
    opinions = [
        Opinion(
            id="A1",
            text="意見1",
            comment_id="C1",
            properties={"region": "東京都"},
        ),
        Opinion(
            id="A2",
            text="意見2",
            comment_id="C2",
            properties={"region": "大阪府"},
        ),
        Opinion(
            id="A3",
            text="意見3",
            comment_id="C3",
            properties={"region": "神奈川県"},
        ),
    ]

    filter_obj = PropertyFilter(opinions)
    result = filter_obj.filter(region=["東京都", "大阪府"])

    assert len(result) == 2


def test_property_filter_multiple_properties():
    """Test filtering by multiple properties (AND)"""
    opinions = [
        Opinion(
            id="A1",
            text="意見1",
            comment_id="C1",
            properties={"gender": "女性", "region": "東京都"},
        ),
        Opinion(
            id="A2",
            text="意見2",
            comment_id="C2",
            properties={"gender": "男性", "region": "東京都"},
        ),
        Opinion(
            id="A3",
            text="意見3",
            comment_id="C3",
            properties={"gender": "女性", "region": "大阪府"},
        ),
    ]

    filter_obj = PropertyFilter(opinions)
    result = filter_obj.filter(gender="女性", region="東京都")

    assert len(result) == 1
    assert result[0].id == "A1"


def test_property_distribution():
    """Test property distribution calculation"""
    opinions = [
        Opinion(id="A1", text="意見1", comment_id="C1", properties={"gender": "女性"}),
        Opinion(id="A2", text="意見2", comment_id="C2", properties={"gender": "男性"}),
        Opinion(id="A3", text="意見3", comment_id="C3", properties={"gender": "女性"}),
    ]

    filter_obj = PropertyFilter(opinions)
    dist = filter_obj.get_property_distribution("gender")

    assert dist == {"女性": 2, "男性": 1}


def test_property_filter_empty_result():
    """Test filtering with no matches"""
    opinions = [
        Opinion(
            id="A1",
            text="意見1",
            comment_id="C1",
            properties={"region": "東京都"},
        ),
    ]

    filter_obj = PropertyFilter(opinions)
    result = filter_obj.filter(region="大阪府")

    assert len(result) == 0


def test_property_filter_custom():
    """Test custom property filtering"""
    opinions = [
        Opinion(
            id="A1",
            text="意見1",
            comment_id="C1",
            properties={"occupation": "会社員"},
        ),
        Opinion(
            id="A2",
            text="意見2",
            comment_id="C2",
            properties={"occupation": "公務員"},
        ),
    ]

    filter_obj = PropertyFilter(opinions)
    result = filter_obj.filter(custom={"occupation": "会社員"})

    assert len(result) == 1
    assert result[0].properties["occupation"] == "会社員"


def test_property_summary():
    """Test summary statistics generation"""
    opinions = [
        Opinion(
            id="A1",
            text="意見1",
            comment_id="C1",
            properties={"gender": "女性", "region": "東京都"},
        ),
        Opinion(
            id="A2",
            text="意見2",
            comment_id="C2",
            properties={"gender": "男性", "region": "未回答"},
        ),
        Opinion(
            id="A3",
            text="意見3",
            comment_id="C3",
            properties={"gender": "女性", "region": "大阪府"},
        ),
    ]

    filter_obj = PropertyFilter(opinions)
    summary = filter_obj.summary()

    assert summary["total_opinions"] == 3
    assert "gender" in summary["property_names"]
    assert "region" in summary["property_names"]
    assert summary["completeness"]["gender"] == 1.0  # All answered
    assert summary["completeness"]["region"] == 2.0 / 3.0  # 2 out of 3 answered


# ============================================
# Data Model Tests
# ============================================


def test_opinion_model():
    """Test Opinion Pydantic model"""
    op = Opinion(
        id="A1",
        text="公園の遊具を増やしてほしい",
        comment_id="C1",
        properties={"gender": "女性", "region": "東京都"},
    )

    assert op.id == "A1"
    assert op.text == "公園の遊具を増やしてほしい"
    assert op.comment_id == "C1"
    assert op.properties["gender"] == "女性"
    assert op.properties["region"] == "東京都"


def test_comment_model():
    """Test Comment Pydantic model"""
    comment = Comment(
        comment_id="C1",
        comment_body="公園の遊具を増やしてほしい",
        gender="女性",
        region="東京都",
        age_group="30代",
    )

    assert comment.comment_id == "C1"
    assert comment.gender == "女性"
    assert comment.region == "東京都"
    assert comment.age_group == "30代"


# ============================================
# Integration Tests (requires LLM API)
# ============================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_opinion_extraction_mock():
    """Test opinion extraction with mock (no actual LLM call)"""
    from kagura.testing import LLMMock
    from pipeline import opinion_extractor

    # Mock LLM response
    with LLMMock('["意見1", "意見2"]'):
        result = await opinion_extractor("サンプルコメント")
        assert isinstance(result, list)
        # Note: With mock, result might not match exactly due to Kagura's parsing


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cluster_labeling_mock():
    """Test cluster labeling with mock"""
    from kagura.testing import LLMMock
    from pipeline import cluster_labeler

    opinions = ["意見A", "意見B", "意見C"]

    with LLMMock('{"label": "テストラベル", "description": "テスト説明"}'):
        result = await cluster_labeler(opinions)
        assert isinstance(result, dict)


# ============================================
# Utility Tests
# ============================================


def test_property_get_values():
    """Test get_property_values function"""
    opinions = [
        Opinion(
            id="A1",
            text="意見1",
            comment_id="C1",
            properties={"region": "東京都"},
        ),
        Opinion(
            id="A2",
            text="意見2",
            comment_id="C2",
            properties={"region": "大阪府"},
        ),
        Opinion(
            id="A3",
            text="意見3",
            comment_id="C3",
            properties={"region": "東京都"},
        ),
    ]

    filter_obj = PropertyFilter(opinions)
    values = filter_obj.get_property_values("region")

    assert sorted(values) == ["大阪府", "東京都"]


def test_all_property_distributions():
    """Test get_all_property_distributions"""
    opinions = [
        Opinion(
            id="A1",
            text="意見1",
            comment_id="C1",
            properties={"gender": "女性", "region": "東京都"},
        ),
        Opinion(
            id="A2",
            text="意見2",
            comment_id="C2",
            properties={"gender": "男性", "region": "大阪府"},
        ),
    ]

    filter_obj = PropertyFilter(opinions)
    dists = filter_obj.get_all_property_distributions()

    assert "gender" in dists
    assert "region" in dists
    assert dists["gender"] == {"女性": 1, "男性": 1}
    assert dists["region"] == {"東京都": 1, "大阪府": 1}

from services.classifier import classify
from services.importance_ranker import score_article
def test_classifier_limits_category():
    assert classify("New critical vulnerability discovered") == "Cybersecurity"
def test_score_is_bounded_and_explained():
    score,factors=score_article("2026-10-21T08:00:00+00:00","Cybersecurity","Critical vulnerability release","Security patch",20)
    assert 0 <= score <= 100
    assert set(factors)=={"recency","relevance","source_priority","signals"}

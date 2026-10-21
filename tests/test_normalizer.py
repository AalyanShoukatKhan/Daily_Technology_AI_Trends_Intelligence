from services.article_normalizer import canonicalize_url, normalize_entry
def test_canonical_url_removes_tracking_and_fragment():
    assert canonicalize_url("https://Example.com/story/?utm_source=x#section") == "https://example.com/story"
def test_normalizer_rejects_missing_title_or_url():
    assert normalize_entry({"title":"", "link":"https://example.com"}) is None
def test_normalizer_keeps_source_link():
    a=normalize_entry({"title":"A title","link":"https://example.com/a","summary":"An excerpt long enough"})
    assert a["url"]=="https://example.com/a"

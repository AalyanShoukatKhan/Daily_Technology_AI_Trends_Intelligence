def test_dashboard_and_health(client):
    assert client.get("/").status_code==200
    assert client.get("/health").json["ok"] is True
def test_source_validation(client):
    response=client.post("/sources",data={"name":"Bad","feed_url":"file:///etc/passwd"},follow_redirects=True)
    assert b"valid HTTP(S)" in response.data
def test_article_page_loads(client):
    assert client.get("/articles").status_code==200

def test_run_history_route(client):
    response=client.get("/history")
    assert response.status_code==200
def test_sources_page_shows_seeded_sources(client):
    response=client.get("/sources")
    assert response.status_code==200
    assert b"RSS source registry" in response.data

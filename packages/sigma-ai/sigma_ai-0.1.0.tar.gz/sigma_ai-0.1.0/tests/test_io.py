from sigma import io


def test_fetch_json_httpbin():
    data = io.fetch_json("https://httpbin.org/json")
    assert "slideshow" in data
    assert "slides" in data["slideshow"]

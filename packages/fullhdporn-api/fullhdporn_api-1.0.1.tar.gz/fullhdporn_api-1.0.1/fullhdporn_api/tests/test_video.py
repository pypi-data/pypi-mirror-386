from ..fullhdporn_api import Client

video = Client().get_video("https://www.fullhdporn.sex/leya-desantis-and-clea-gaultier-star-in-a-gonzo-threesome-with-anal/")

def test_all():
    assert isinstance(video.video_id, str)
    assert isinstance(video.video_status, str)
    assert isinstance(video.title, str)
    assert isinstance(video.description, str)
    assert isinstance(video.duration, int)
    assert isinstance(video.thumbnail, str)
    assert isinstance(video.tags, list)
    assert isinstance(video.embed_url, str)
    assert isinstance(video.publish_date, str)
    assert isinstance(video.categories, list)
    assert isinstance(video.rating, list)
    assert isinstance(video.total_views, int)

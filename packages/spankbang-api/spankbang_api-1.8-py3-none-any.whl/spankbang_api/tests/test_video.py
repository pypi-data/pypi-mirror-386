import httpx
from base_api.modules.errors import BotProtectionDetected
from spankbang_api.spankbang_api import Client

try:
    url = "https://spankbang.com/9qfxd/video/asian+girl+rides+fuck+machine+to+massive+squirt+no+hands+needed"
    video = Client().get_video(url)

except BotProtectionDetected:
    exit(0)

def test_title():
    assert isinstance(video.title, str) and len(video.title) > 3


def test_author():
    assert isinstance(video.title, str) and len(video.author) > 5


def test_description():
    assert isinstance(video.description, str) and len(video.description) > 20


def test_video_length():
    assert isinstance(video.length, str) and len(video.length) > 0


def test_tags():
    assert isinstance(video.tags, list) and len(video.tags) > 2


def test_qualities():
    assert isinstance(video.video_qualities, list) and len(video.video_qualities) > 2


def test_direct_download_urls():
    assert isinstance(video.direct_download_urls, list) and len(video.direct_download_urls) > 2


def test_thumbnail():
    assert isinstance(video.thumbnail, str) and len(video.thumbnail) > 3


def test_rating():
    assert isinstance(video.rating, str) and len(video.rating) > 1


def test_segments():
    assert isinstance(video.get_segments("best"), list) and len(video.get_segments("best")) > 25


def test_download_remux():
    assert video.download(quality="worst", downloader="threaded", remux=True) is True

def test_download_raw():
    assert video.download(quality="worst", downloader="threaded") is True
"""
Copyright 2021, Dana-Farber Cancer Institute and Weill Cornell Medicine
License: GNU GPL 2.0
"""

import urllib.request
import pytest


@pytest.mark.parametrize(
    "url",
    [
        "https://www.pathml.org",
        # Vignettes
        "https://github.com/Dana-Farber-AIOS/pathml/tree/master/examples/vignettes/",
        # Docs
        "https://pathml.readthedocs.io/en/latest/",
    ],
)
def test_urls(url):
    """
    Make sure that the URLs linked in the manuscript are not broken.
    Adds a User-Agent header to avoid 403 errors from some servers.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        response = urllib.request.urlopen(req)
        # HTTP status code 200 means "OK"
        assert response.getcode() == 200
    except urllib.error.HTTPError as e:
        # If site blocks CI (e.g., 403), skip the test instead of failing
        if e.code == 403:
            pytest.skip(f"URL {url} returned 403 Forbidden")
        else:
            raise

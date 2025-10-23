from base64 import urlsafe_b64encode
from dataclasses import dataclass
from urllib.parse import urljoin


def encode_page(site_url, page_url):
    page = urljoin(site_url, page_url)

    return urlsafe_b64encode(page.encode()).decode()


@dataclass
class LinkMaker:
    base_url: str

    def ap_object(self, site_url: str, page_url: str):
        return self.base_url + "pages/" + encode_page(site_url, page_url)

    def comments(self, site_url: str, page_url: str):
        return self.base_url + "comments/" + encode_page(site_url, page_url)

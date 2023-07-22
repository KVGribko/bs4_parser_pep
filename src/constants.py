from pathlib import Path
from urllib.parse import urljoin

BASE_DIR = Path(__file__).parent

DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"

MAIN_DOC_URL = "https://docs.python.org/3/"
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_URL = urljoin(MAIN_DOC_URL, "download.html")
PEPS_LIST_URL = "https://peps.python.org/"
WHATS_NEW_URL = urljoin(MAIN_DOC_URL, "whatsnew/")

EXPECTED_STATUS = {
    "A": ("Active", "Accepted"),
    "D": ("Deferred",),
    "F": ("Final",),
    "P": ("Provisional",),
    "R": ("Rejected",),
    "S": ("Superseded",),
    "W": ("Withdrawn",),
    "": ("Draft", "Active"),
}

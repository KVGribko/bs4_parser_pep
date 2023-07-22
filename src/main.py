import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR,
    DOWNLOADS_URL,
    EXPECTED_STATUS,
    MAIN_DOC_URL,
    PEPS_LIST_URL,
    WHATS_NEW_URL,
)
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    response = get_response(session, WHATS_NEW_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features="lxml")

    main_div = find_tag(soup, "section", attrs={"id": "what-s-new-in-python"})
    div_with_ul = find_tag(main_div, "div", attrs={"class": "toctree-wrapper"})
    sections_by_python = div_with_ul.find_all(
        "li",
        attrs={"class": "toctree-l1"},
    )

    results = [("Ссылка на статью", "Заголовок", "Редактор, Автор")]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find("a")
        version_link = urljoin(WHATS_NEW_URL, version_a_tag["href"])
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, "lxml")
        h1 = find_tag(soup, "h1")
        dl = find_tag(soup, "dl")
        dl_text = dl.text.replace("\n", " ")
        results.append((version_link, h1.text, dl_text))
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, "lxml")
    sidebar = find_tag(soup, "div", attrs={"class": "sphinxsidebarwrapper"})
    ul_tags = sidebar.find_all("ul")
    for ul in ul_tags:
        if "All versions" in ul.text:
            a_tags = ul.find_all("a")
            break
    else:
        raise Exception("Не найден список c версиями Python")

    results = [("Ссылка на документацию", "Версия", "Статус")]
    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"
    for a_tag in a_tags:
        link = a_tag["href"]
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ""
        results.append((link, version, status))
    return results


def download(session):
    response = get_response(session, DOWNLOADS_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features="lxml")

    table_tag = find_tag(soup, "table", attrs={"class": "docutils"})
    pdf_a4_tag = find_tag(
        table_tag,
        "a",
        attrs={"href": re.compile(r".+pdf-a4\.zip$")},
    )
    pdf_a4_link = pdf_a4_tag["href"]

    archive_url = urljoin(DOWNLOADS_URL, pdf_a4_link)
    filename = archive_url.split("/")[-1]
    downloads_dir = BASE_DIR / "downloads"  # без этого не проходит тест
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(archive_url)
    with open(archive_path, "wb") as file:
        file.write(response.content)

    logging.info(f"Архив был загружен и сохранён: {archive_path}")


def pep(session: requests_cache.CachedSession):
    response = get_response(session, PEPS_LIST_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features="lxml")

    pep_tables = soup.find_all(
        "table",
        attrs={"class": "pep-zero-table docutils align-default"},
    )
    status_count = defaultdict(int)
    for table in tqdm(pep_tables):
        table_body = find_tag(table, "tbody")
        table_rows = table_body.find_all("tr")
        for row in table_rows:
            status = None
            if row.abbr and len(row.abbr.text.strip()) == 2:
                status = row.abbr.text.strip()[1]
            link = urljoin(PEPS_LIST_URL, row.a["href"])
            response = get_response(session, link)
            soup = BeautifulSoup(response.text, "lxml")
            dl = find_tag(soup, "dl")
            status_element = dl.find(string="Status").parent
            status_in_link = status_element.find_next_sibling("dd").text

            if status:
                table_status = EXPECTED_STATUS[status]
                if status_in_link not in table_status:
                    msg = (
                        f"Несовпадающие статусы:\n"
                        f"{link}\n"
                        f"Статус в карточке: {status_in_link}\n"
                        f"Ожидаемые статусы: {table_status}\n"
                    )
                    logging.error(msg, stack_info=True)
            status_count[status_in_link] += 1

    pep_count = sum(status_count.values())
    status_count = [("Статус", "Количество")] + sorted(
        status_count.items(), key=lambda x: x[1]
    )
    status_count.append(("Total", pep_count))

    return status_count


MODE_TO_FUNCTION = {
    "whats-new": whats_new,
    "latest-versions": latest_versions,
    "download": download,
    "pep": pep,
}


def main():
    configure_logging()
    logging.info("Парсер запущен!")
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f"Аргументы командной строки: {args}")
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)

    logging.info("Парсер завершил работу.")


if __name__ == "__main__":
    main()

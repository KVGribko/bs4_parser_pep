import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import RequestException

from constants import EXPECTED_STATUS, PEPS_LIST_URL
from exceptions import ParserFindTagException


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = "utf-8"
        return response
    except RequestException:
        logging.exception(
            f"Возникла ошибка при загрузке страницы {url}", stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f"Не найден тег {tag} {attrs}"
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def get_all_peps(soup: BeautifulSoup) -> list[dict]:
    pep_tables = soup.find_all(
        "table",
        attrs={"class": "pep-zero-table docutils align-default"},
    )
    peps = []
    for table in pep_tables:
        table_body = find_tag(table, "tbody")
        table_rows = table_body.find_all("tr")
        for row in table_rows:
            cells = row.find_all("td")
            pep_type = cells[0].text.strip()[1:]
            status = None
            if len(pep_type) == 2:
                status = pep_type[1]
                pep_type = pep_type[0]
            number = int(cells[1].text.strip())
            link = urljoin(PEPS_LIST_URL, cells[2].a["href"])
            author = cells[3].text.strip()
            pep_dict = {
                "type": pep_type,
                "status_in_table": status,
                "status_in_link": None,
                "number": number,
                "link": link,
                "author": author,
            }
            peps.append(pep_dict)
    return peps


def set_pep_link_status(session, peps: list[dict]):
    for pep in peps:
        link = pep["link"]
        response = get_response(session, link)
        soup = BeautifulSoup(response.text, "lxml")
        dl = find_tag(soup, "dl")
        status_element = dl.find(string="Status").parent
        status_in_link = status_element.find_next_sibling("dd").text
        pep["status_in_link"] = status_in_link
        if pep["status_in_table"]:
            table_status = EXPECTED_STATUS[pep["status_in_table"]]
            if status_in_link not in table_status:
                msg = (
                    f"Несовпадающие статусы:\n"
                    f"{pep['link']}\n"
                    f"Статус в карточке: {status_in_link}\n"
                    f"Ожидаемые статусы: {table_status}\n"
                )
                logging.error(msg, stack_info=True)


def get_status_count(peps):
    status_count = {}
    for pep in peps:
        status_in_link = pep["status_in_link"]
        status_count[status_in_link] = status_count.get(status_in_link, 0) + 1
    status_count = [("Статус", "Количество")] + sorted(
        status_count.items(), key=lambda x: x[1]
    )
    status_count.append(("Total", len(peps)))
    return status_count

import re
from datetime import datetime
from enum import Enum
from typing import Union

import click
from Levenshtein import ratio
from unidecode import unidecode

from tbr_deal_finder.config import Config
from tbr_deal_finder.utils import get_duckdb_conn, execute_query, get_query_by_name, echo_info, float_to_currency

_AUTHOR_RE = re.compile(r'[^a-zA-Z0-9]')

class BookFormat(Enum):
    AUDIOBOOK = "Audiobook"
    EBOOK = "E-Book"
    NA = "N/A"  # When the format doesn't matter


class Book:

    def __init__(
        self,
        retailer: str,
        title: str,
        authors: str,
        timepoint: datetime,
        format: Union[BookFormat, str],
        list_price: float = 0,
        current_price: float = 0,
        ebook_asin: str = None,
        audiobook_isbn: str = None,
        audiobook_list_price: float = 0,
        deleted: bool = False,
        exists: bool = True,
        is_internal: bool = False,
    ):
        self.retailer = retailer
        self.title = get_normalized_title(title)
        self.authors = authors
        self.timepoint = timepoint

        self.ebook_asin = ebook_asin
        self.audiobook_isbn = audiobook_isbn
        self.audiobook_list_price = audiobook_list_price
        self.deleted = deleted
        self.exists = exists

        # Used but not REALLY tracked by the user
        # Example: We need to keep track of Kindle Unlimited for DCC for whispersync
        #   However, only the user only has DCC on their Audible wishlist
        #   We don't want to show the Kindle deal for the ebook but we need it for Audible pricing
        self.is_internal = is_internal

        self.list_price = list_price
        self.current_price = current_price
        self.normalized_authors = get_normalized_authors(authors)

        self._alt_price = None

        if isinstance(format, str):
            format = BookFormat(format)
        self.format = format

    def discount(self) -> int:
        if not self.current_price:
            return 100

        return int((1 - self.current_price/self.list_price) * 100)

    @property
    def deal_id(self) -> str:
        return f"{self.title}__{self.normalized_authors}__{self.format}__{self.retailer}"

    @property
    def title_id(self) -> str:
        return f"{self.title}__{self.normalized_authors}__{self.format}"

    @property
    def full_title_str(self) -> str:
        return f"{self.title}__{self.normalized_authors}"

    @property
    def current_price(self) -> float:
        return self._current_price

    @current_price.setter
    def current_price(self, price: float):
        self._current_price = round(price, 2)

    @property
    def alt_price(self) -> Union[float, None]:
        return self._alt_price

    @alt_price.setter
    def alt_price(self, price: float):
        self._alt_price = round(price, 2)

    @property
    def list_price(self) -> float:
        return self._list_price

    @list_price.setter
    def list_price(self, price: float):
        self._list_price = round(price, 2)

    def list_price_string(self):
        return float_to_currency(self.list_price)

    def current_price_string(self):
        return float_to_currency(self.current_price)

    def __str__(self) -> str:
        price = self.current_price_string()
        book_format = self.format.value
        title = self.title
        if len(self.title) > 75:
            title = f"{title[:75]}..."
        return f"{title} by {self.authors} - {price} - {self.discount()}% Off at {self.retailer}"

    def dict(self):
        return {
            "retailer": self.retailer,
            "title": self.title,
            "authors": self.authors,
            "list_price": self.list_price,
            "current_price": self.current_price,
            "timepoint": self.timepoint,
            "format": self.format.value,
            "deleted": self.deleted,
            "deal_id": self.deal_id,
            "is_internal": self.is_internal,
        }

    def tbr_dict(self):
        return {
            "title": self.title,
            "authors": self.authors,
            "format": self.format.value,
            "ebook_asin": self.ebook_asin,
            "audiobook_isbn": self.audiobook_isbn,
            "audiobook_list_price": self.audiobook_list_price,
            "book_id": self.title_id,
            "is_internal": self.is_internal,
        }

    def unknown_book_dict(self):
        return {
            "retailer": self.retailer,
            "title": self.title,
            "authors": self.authors,
            "format": self.format.value,
            "book_id": self.deal_id,
        }


def get_deals_found_at(timepoint: datetime) -> list[Book]:
    db_conn = get_duckdb_conn()
    query_response = execute_query(
        db_conn,
        get_query_by_name("get_deals_found_at.sql"),
        {"timepoint": timepoint}
    )
    return [Book(**book) for book in query_response]


def get_active_deals() -> list[Book]:
    db_conn = get_duckdb_conn()
    query_response = execute_query(
        db_conn,
        get_query_by_name("get_active_deals.sql")
    )
    return [Book(**book) for book in query_response]


def is_qualifying_deal(config: Config, book: Book) -> bool:
    return book.current_price <= config.max_price and book.discount() >= config.min_discount


def print_books(config: Config, books: list[Book]):
    audiobooks = [book for book in books if book.format == BookFormat.AUDIOBOOK]
    audiobooks = sorted(audiobooks, key=lambda book: book.deal_id)

    ebooks = [book for book in books if book.format == BookFormat.EBOOK]
    ebooks = sorted(ebooks, key=lambda book: book.deal_id)

    for books_in_format in [audiobooks, ebooks]:
        if not books_in_format:
            continue

        init_book = books_in_format[0]
        if not any(is_qualifying_deal(config, book) for book in books_in_format):
            continue

        echo_info(f"\n\n{init_book.format.value} Deals:")

        prior_title_id = init_book.title_id
        for book in books_in_format:
            if not is_qualifying_deal(config, book):
                continue

            if prior_title_id != book.title_id:
                prior_title_id = book.title_id
                click.echo()

            click.echo(str(book))


def get_full_title_str(title: str, authors: Union[list, str]) -> str:
    title = get_normalized_title(title)
    return f"{title}__{get_normalized_authors(authors)}"


def get_title_id(title: str, authors: Union[list, str], book_format: BookFormat) -> str:
    title = get_normalized_title(title)
    return f"{title}__{get_normalized_authors(authors)}__{book_format.value}"


def get_normalized_title(title: str) -> str:
    return title.split(":")[0].split("(")[0].strip()


def get_normalized_authors(authors: Union[str, list[str]]) -> list[str]:
    if isinstance(authors, str):
        authors = [i for i in authors.split(",")]

    return sorted([_AUTHOR_RE.sub('', unidecode(author)).lower() for author in authors])


def is_matching_authors(a1: list[str], a2: list[str]) -> bool:
    """Checks if two normalized authors are matching.
    Matching here means that they are at least 80% similar using levenshtein distance.

    Score is calculated as follows:
        1 - (distance / (len1 + len2))

    :param a1:
    :param a2:
    :return:
    """
    return any(
        any(ratio(author1, author2, score_cutoff=.8) for author2 in a2)
        for author1 in a1
    )

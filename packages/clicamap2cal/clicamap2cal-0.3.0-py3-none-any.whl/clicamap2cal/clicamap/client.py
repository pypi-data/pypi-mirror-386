#
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import TYPE_CHECKING, ClassVar, Generator

import pytz
from lxml import html
from requests import Session

from .. import __version__

if TYPE_CHECKING:
    from lxml.html import HtmlElement

    from ..logging import Logger


def requires_login(f):
    @wraps(f)
    def wrapper(self):
        if self._logged_in:
            return f(self)

        self.login()

        return f(self)

    return wrapper


@dataclass
class LivraisonDetails:
    title: str
    location: str
    items: list[str]


class NoLivraisonDetails(Exception): ...


class Client:
    BASE_URL: ClassVar[str] = "https://www.clicamap.org"
    LOGIN_URL: ClassVar[str] = BASE_URL + "/portail/connexion"
    LOGOUT_URL: ClassVar[str] = BASE_URL + "/portail/deconnexion"

    HTTP_USER_AGENT: ClassVar[str] = f"clicamap.client v{__version__}"
    LOGGER: ClassVar[Logger]

    LIVRAISON_DATE_EXTRACT_RE: ClassVar[re.Pattern] = re.compile(
        r"^Livraisons du (\d.+)$"
    )

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

        self._session = Session()
        self._session.headers.update(
            {
                "User-Agent": self.HTTP_USER_AGENT,
            }
        )

        self._logged_in = False

    @requires_login
    def get_livraisons(self):
        calendar_url = self._get_livraisons_calendar_url()
        self.LOGGER.debug(
            "calendar url successfully retrieved",
            calendar_url=calendar_url,
        )

        return self._get_livraisons_calendar(calendar_url)

    def _get_livraisons_calendar(
        self, url: str
    ) -> Generator[tuple[datetime, list[LivraisonDetails]], None]:
        start_dt = datetime.now()
        month = start_dt.month

        while month <= 12:
            cal_month_url = f"{url}/{start_dt.year}/{month:02d}"
            logger = self.LOGGER.bind(cal_month_url=cal_month_url)
            logger.debug(
                f"getting calendar month {month:02d}",
            )

            r = self._session.get(cal_month_url)
            r.raise_for_status()

            for (
                livraison_dt,
                livraison_details,
            ) in self._parse_calendar_livraison_month(
                logger=logger,
                body=r.text,
            ):
                yield livraison_dt, livraison_details

            month += 1

    def _parse_calendar_livraison_month(self, logger: Logger, body: str):
        f_logger = logger.bind(func="_parse_calendar_livraison_month")

        tree: HtmlElement = html.fromstring(body)
        match = tree.xpath('//div[starts-with(@id, "modal_")]')
        if len(match) == 0:
            f_logger.trace("no modals matched")
            return []

        i = 0
        for m in match:
            f_logger.trace("", modal_idx=i, match_idx=html.tostring(m))
            i += 1

        for m in match:
            m_logger = logger.bind(modal_id=m.get("id"))
            m_logger.debug("processing modal")
            try:
                yield self._parse_calendar_livraison_month_modal(m_logger, m)
            except NoLivraisonDetails:
                m_logger.debug("no livraison details")
                continue

    def _parse_calendar_livraison_month_modal(
        self,
        logger: Logger,
        modal: HtmlElement,
    ) -> tuple[datetime, list[LivraisonDetails]]:
        f_logger = logger.bind(func="_parse_calendar_livraison_month_modal")
        f_logger.trace("", modal=html.tostring(modal))
        modal_date = self._extract_date_livraison_from_modal(logger=logger, modal=modal)
        logger.debug("found modal date", modal_date=modal_date)

        livraison_details = self._extract_body_livraison_from_modal(
            logger=logger, modal=modal
        )
        logger.debug("found livraison details", livraison_details=livraison_details)

        return modal_date, livraison_details

    def _extract_body_livraison_from_modal(
        self,
        logger: Logger,
        modal: HtmlElement,
    ) -> list[LivraisonDetails]:
        f_logger = logger.bind(func="_extract_body_livraison_from_modal")
        f_logger.trace("", modal=html.tostring(modal))

        all_raw_livraisons = modal.xpath(
            ".//div[contains(concat(' ', normalize-space(@class), ' '), ' modal-body ')]/div"
        )

        if len(all_raw_livraisons) == 0:
            f_logger.trace("raising no livraison details")
            raise NoLivraisonDetails()

        livraison_details: list[LivraisonDetails] = []
        for raw_livraison in all_raw_livraisons:
            livraison_title = raw_livraison.xpath("./h3")[0].text
            livraison_location = raw_livraison.xpath("(./h4)[2]/strong")[0].text
            assert livraison_location != ""
            assert livraison_title != ""

            livraison_items: list[str] = []
            livraison_items_raw = raw_livraison.xpath("./ul/li")
            if len(livraison_items_raw) == 0:
                livraison_items = ["non précisé"]
            else:
                for livraison_item_raw in livraison_items_raw:
                    livraison_items.append(livraison_item_raw.text_content())

            livraison_details.append(
                LivraisonDetails(
                    title=livraison_title,
                    location=livraison_location,
                    items=livraison_items,
                )
            )

        f_logger.trace("", livraison_details=livraison_details)

        return livraison_details

    def _extract_date_livraison_from_modal(
        self,
        logger: Logger,
        modal: HtmlElement,
    ) -> datetime:
        f_logger = logger.bind(func="_extract_date_livraison_from_modal")
        f_logger.trace(": ", modal=html.tostring(modal))
        match_date = modal.xpath(
            ".//div[contains(concat(' ', normalize-space(@class), ' '), ' modal-header ')]/h4"
        )
        assert len(match_date) == 1
        f_logger.trace(
            "",
            match_date=html.tostring(match_date[0]),
        )

        # e.g: Livraisons du 18/03/2025
        return self._extract_date_livraison_from_raw_text(match_date[0].text)

    def _extract_date_livraison_from_raw_text(self, raw_txt: str) -> datetime:
        """Extract 'Livraisons du 18/03/2025' into a datetime"""
        m = self.LIVRAISON_DATE_EXTRACT_RE.match(raw_txt)
        assert m is not None

        raw_date = m.group(1)
        assert raw_date != ""

        raw_day, raw_month, raw_year = raw_date.split("/", maxsplit=3)

        return datetime(
            year=int(raw_year),
            month=int(raw_month),
            day=int(raw_day),
            hour=18,
            minute=30,
            tzinfo=pytz.timezone("Europe/Paris"),
        )

    def _get_livraisons_calendar_url(self) -> str:
        r = self._session.get(self.BASE_URL)
        r.raise_for_status()

        tree: HtmlElement = html.fromstring(r.text)
        match = tree.xpath('.//li/a[contains(text(), "Mes livraisons ")]')

        assert len(match) == 1

        return match[0].get("href")

    def _fetch_csrf_token(self) -> str:
        r = self._session.get(
            self.LOGIN_URL
        )  # to create a new session on the serverr side
        r.raise_for_status()

        tree: HtmlElement = html.fromstring(r.text)
        csrf_token = tree.xpath('.//input[@name="_csrf_token"]/@value')

        assert len(csrf_token) == 1
        csrf_token = csrf_token[0]

        assert csrf_token != ""

        self.LOGGER.debug("got CSRF token", csrf_token=csrf_token)

        return csrf_token

    def login(self) -> None:
        self.LOGGER.debug("logging in")

        params = {
            "_username": self.username,
            "_password": self.password,
            "_csrf_token": self._fetch_csrf_token(),
        }

        r = self._session.post(self.LOGIN_URL, data=params)
        r.raise_for_status()

        self.LOGGER.debug("successfully logged in")

        self._logged_in = True

    def logout(self) -> None:
        self.LOGGER.debug("logging out")
        self._session.get(self.LOGOUT_URL)
        self.LOGGER.debug("logged out")

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, type, value, traceback):
        self.logout()

"""Ordinance date extraction logic"""

import logging
from datetime import datetime
from collections import Counter

from compass.utilities.enums import LLMUsageCategory


logger = logging.getLogger(__name__)

# These domains contain the collection date in URL, not enactment date
_BANNED_DATE_DOMAINS = ["https://energyzoning.org"]


class DateExtractor:
    """Helper class to extract date info from document"""

    SYSTEM_MESSAGE = (
        "You are a legal scholar that reads ordinance text and extracts "
        "structured date information. "
        "Return your answer as a dictionary in JSON format (not markdown). "
        "Your JSON file must include exactly four keys. The first "
        "key is 'explanation', which contains a short summary of the most "
        "relevant date information you found in the text. The second key is "
        "'year', which should contain an integer value that represents the "
        "latest year this ordinance was enacted/updated, or null if that "
        "information cannot be found in the text. The third key is 'month', "
        "which should contain an integer value that represents the latest "
        "month of the year this ordinance was enacted/updated, or null if "
        "that information cannot be found in the text. The fourth key is "
        "'day', which should contain an integer value that represents the "
        "latest day of the month this ordinance was enacted/updated, or null "
        "if that information cannot be found in the text. Only provide values "
        "if you are confident that they represent the latest date this "
        "ordinance was enacted/updated"
    )
    """System message for date extraction LLM calls"""

    def __init__(self, structured_llm_caller, text_splitter=None):
        """

        Parameters
        ----------
        structured_llm_caller : StructuredLLMCaller
            Instance used for structured validation queries.
        text_splitter : LCTextSplitter, optional
            Optional text splitter (or subclass instance, or any object
            that implements a `split_text` method) to attach to doc
            (used for splitting out pages in an HTML document).
            By default, ``None``.
        """
        self.slc = structured_llm_caller
        self.text_splitter = text_splitter

    async def parse(self, doc):
        """Extract date (year, month, day) from doc

        Parameters
        ----------
        doc : elm.web.document.BaseDocument
            Document with a `raw_pages` attribute.

        Returns
        -------
        tuple
            3-tuple containing year, month, day, or ``None`` if any of
            those are not found.
        """
        if hasattr(doc, "text_splitter") and self.text_splitter is not None:
            old_splitter = doc.text_splitter
            doc.text_splitter = self.text_splitter
            out = await self._parse(doc)
            doc.text_splitter = old_splitter
            return out

        return await self._parse(doc)

    async def _parse(self, doc):
        """Extract date (year, month, day) from doc"""
        url = doc.attrs.get("source")
        can_check_url_for_date = url and not any(
            sub_str in url for sub_str in _BANNED_DATE_DOMAINS
        )
        if can_check_url_for_date:
            logger.debug("Checking URL for date: %s", url)
            response = await self.slc.call(
                sys_msg=self.SYSTEM_MESSAGE,
                content=(
                    "Please extract the date from the URL for this "
                    f"ordinance, if possible:\n{url}"
                ),
                usage_sub_label=LLMUsageCategory.DATE_EXTRACTION,
            )
            if response:
                date = _parse_date([response])
                logger.debug("Parsed date from URL: %s", date)
                return date

        if not doc.raw_pages:
            return None, None, None

        all_years = []
        for text in doc.raw_pages:
            if not text:
                continue

            response = await self.slc.call(
                sys_msg=self.SYSTEM_MESSAGE,
                content=f"Please extract the date for this ordinance:\n{text}",
                usage_sub_label=LLMUsageCategory.DATE_EXTRACTION,
            )
            if not response:
                continue
            all_years.append(response)

        return _parse_date(all_years)


def _parse_date(json_list):
    """Parse all date elements

    True date is determined to be the most frequent date. In the case of
    a tie, the latest date is chosen.
    """
    if not json_list:
        return None, None, None

    years = _parse_date_element(
        json_list,
        key="year",
        max_len=4,
        min_val=2000,
        max_val=datetime.now().year,
    )
    months = _parse_date_element(
        json_list, key="month", max_len=2, min_val=1, max_val=12
    )
    days = _parse_date_element(
        json_list, key="day", max_len=2, min_val=1, max_val=31
    )

    date_elements = Counter(zip(years, months, days, strict=False))
    date = max(date_elements, key=lambda date: (date_elements[date], date))
    return tuple(None if d < 0 else d for d in date)


def _parse_date_element(json_list, key, max_len, min_val, max_val):
    """Parse out a single date element"""
    date_elements = [info.get(key) for info in json_list]
    logger.debug("key=%r, date_elements=%r", key, date_elements)
    return [
        int(y)
        if y is not None
        and len(str(y)) <= max_len
        and (min_val <= int(y) <= max_val)
        else -1 * float("inf")
        for y in date_elements
    ]

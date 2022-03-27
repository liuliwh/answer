"""instant search and retreive the coding answer online

How does it work:
1. Giving a query and num_answer, search possible links on site
    stackoverflow.com from Google.
2. Find all links starts with https://stackoverflow.com/questions/{id}/
    as question links.
3. Get the first num_answer entries of the question links,
    as the working question links.
3. For each working quesiton link, retrieve the page content, get top rated answer,
then extract the code block or text.

Available high level functions:
- answer: Search num_answer of the code answers for a query string.

Available low level functions:
- get_question_links: Search from google, return the links of the search results.
- get_answer: Get the top rated stackoverflows codeblock from the question link.
"""
import argparse
import logging
import re
from collections import namedtuple
from typing import List, Optional
from urllib import parse as urlparse

import requests
from lxml import html
from lxml.etree import Element as EtreeElement
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError as RequestsHTTPError
from requests.exceptions import RequestException

logging.basicConfig(format="%(levelname)s: %(message)s")


NO_RESULTS_MESSAGE = "Sorry, couldn't find any answers with that query"
TECHNICAL_DIFFICULTY_MESSAGE = "Sorry, there is some technical difficulty"
CONNECTION_ERROR_MESSAGE = "Sorry, cannot connect to "


Answer = namedtuple("Answer", ("link", "result"))


class CodeAnswerError(Exception):
    """Base-class for all exceptions raised by this module.
    There was an ambiguous exception that occurred while handling your
    request.
    """


class ConnectionError(CodeAnswerError):
    """Error raised by requests ConnectionError"""


class GetQuestionLinksError(CodeAnswerError):
    """Ambiguous error happens during get question links phase"""


class GetAnswerError(CodeAnswerError):
    """Ambiguous error happens during get answer phase"""


def answer(query: str, num_answer: int = 1) -> List[Answer]:
    """Search num_answer of the code answers for a query string
    Raises:
    CodeAnswerError: Generic base error in this module.
    Derived Errors of CodeAnswerError:
    - ConnectionError: Error caused by requests ConnectionError
    - RequestsError: Ambiguous error raised by requests lib
    - GetQuestionLinksError: Error happens during get question links from query.
    - GetAnswerError: Error happens during get answer from the answer url.
    """
    links = get_question_links(query)
    links_request = links[:num_answer]
    results: List[Answer] = []
    for _, link in enumerate(links_request):
        if result := get_answer(link):
            results.append(Answer(link, result))
    return results


def get_answer(url: str) -> Optional[str]:
    """Get the top rated stackoverflows codeblock from the url.
    Raises:
    ConnectionError: failed to request url due to connection error
    GetAnswerError when failed to request url"""
    url = _get_stackoverflow_scoredesc_url(url)
    try:
        text = _get_url_content(url)
    except RequestsHTTPError:
        return None
    except RequestsConnectionError as e:
        raise ConnectionError(url) from e
    except RequestException as e:
        raise GetAnswerError(url) from e
    return _extract_answer(text)


def _get_stackoverflow_scoredesc_url(url: str) -> str:
    """Add query answertab=scoredesc to the url, to make sure the
    answer from stackoverflow url is sorted by score desc"""
    _append = "answertab=scoredesc"
    parsed = urlparse.urlparse(url)
    queries = f"{parsed.query}&{_append}" if parsed.query else _append
    replaced: List[str] = []
    for _field in parsed._fields:
        if _field == "query":
            replaced.append(queries)
        else:
            replaced.append(getattr(parsed, _field))

    return urlparse.urlunparse(replaced)


def _extract_answer(htmldoc: str) -> Optional[str]:
    """Extract codeblock from the answer page content"""
    try:
        answers = html.document_fromstring(htmldoc).get_element_by_id("answers")
        top_answer = answers.find_class("answercell")[0]
    except (KeyError, IndexError):
        return None
    else:
        return _extract_answer_content(top_answer)


def _extract_answer_content(top_answer: EtreeElement) -> str:
    """Extract code or codetext from the element. The order is:
    1. if <pre><code> exist, return code.
    2. if <pre> doesn't exist, return js-post-body text.
    3. otherwise, return all text content of the element
    """
    if (pre := top_answer.find(".//pre")) is not None:
        code = pre.find(".//code")
    elif len(postbody := top_answer.find_class("js-post-body")) > 0:
        code = postbody[0]
    else:
        code = top_answer
    return code.text_content()


def _get_url_content(url: str) -> str:
    """Return page content of the url in text.
    Raises: HTTPError"""
    logging.debug(f"get_url_content from {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text


def get_question_links(query: str) -> List[str]:
    """Search from google, return the links of the search results.
    Raises:
    ConnectionError: when requests occures connection error
    GetQuestionLinksError:"""
    url = urlencode_search_url(query)
    try:
        text = _get_url_content(url)
    except RequestsHTTPError:
        return []
    except RequestsConnectionError as e:
        raise ConnectionError(url, query) from e
    except RequestException as e:
        raise GetQuestionLinksError(url, query) from e
    return _extract_question_links(text)


def urlencode_search_url(query: str) -> str:
    """Return the encoded query based on the google,
    hardcoded the site:stackoverflow.com"""
    queries = urlparse.urlencode({"q": f"site:stackoverflow.com {query}", "hl": "en"})
    return f"https://www.google.com/search?{queries}"


def _extract_question_links(text: str) -> List[str]:
    """Giving the search result text from the search engine,
    return the links containing https://stackoverflow.com/questions/"""
    pat = re.compile(r"https://stackoverflow.com/questions/\d+/[a-z0-9-]+")
    return pat.findall(text)


def command_line_runner() -> None:
    parser = _get_parser()
    args = vars(parser.parse_args())
    logging.getLogger().setLevel(args["log_level"].upper())
    if not args["query"]:
        parser.print_help()
        return

    qstring = " ".join(args["query"])
    try:
        result = answer(qstring, args["num_answers"])
    except ConnectionError as e:
        logging.exception(e)
        print(f"{CONNECTION_ERROR_MESSAGE} {e}")
    except CodeAnswerError as e:
        logging.exception(e)
        print(f"{TECHNICAL_DIFFICULTY_MESSAGE} {e}")
    else:
        _print_answers(result)


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="The code answer utility")
    parser.add_argument(
        "query", help="the question to answer", nargs="*", metavar="QUERY"
    )
    parser.add_argument(
        "-n",
        "--num",
        help="number of answers to return, shoulbe among [1,10]",
        default=1,
        type=int,
        metavar="NUM",
        dest="num_answers",
        choices=range(1, 11),
    )
    parser.add_argument(
        "-v",
        help="Log level",
        type=str,
        dest="log_level",
        nargs="?",
        choices=("debug", "info", "warning", "error", "critical"),
        default="warning",
    )

    return parser


def _print_answers(answers: List[Answer]):
    if len(answers) == 0:
        print(NO_RESULTS_MESSAGE)
    elif len(answers) == 1:
        print(answers[0].result)
    else:
        for answer in answers:
            print("==" * 30)
            print(f"Answer from: {answer.link} as: \n{answer.result}")


if __name__ == "__main__":
    command_line_runner()

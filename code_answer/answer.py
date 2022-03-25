"""instant search and retreive the coding answer online"""
import argparse
import logging
import re
from collections import namedtuple
from typing import List, Optional
from urllib import parse as urlparse

import requests
from lxml import html
from lxml.etree import Element as EtreeElement

logging.basicConfig(format="%(levelname)s: %(message)s")


NO_RESULTS_MESSAGE = "Sorry, couldn't find any answers with that query"

Answer = namedtuple("Answer", ("link", "result"))


def answer(query: str, num_answer: int = 1) -> List[Answer]:
    """Search code answer for a query string"""
    links = get_question_links(query)
    links_request = links[:num_answer]
    results: List[Answer] = []
    for _, link in enumerate(links_request):
        if result := get_answer(link):
            results.append(Answer(link, result))
    return results


def get_answer(url: str) -> Optional[str]:
    """Get the top rated stackoverflows codeblock from the url"""
    url = _get_stackoverflow_scoredesc_url(url)
    text = _get_url_content(url)
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
    """Return page content of the url.
    Extracting this function is for the testability"""
    logging.debug(f"get_url_content from {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text


def get_question_links(query: str) -> List[str]:
    """Search from google, return the links of the search results"""
    url = urlencode_search_url(query)
    text = _get_url_content(url)
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
    logging.getLogger().setLevel(args["loglevel"])
    if query := args["query"]:
        qstring = " ".join(query)
        result = answer(qstring, args["num_answers"])
        _print_answers(result)
    else:
        parser.print_help()


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
    verbose_group = parser.add_mutually_exclusive_group()
    verbose_group.add_argument(
        "-d",
        "--debug",
        help="Print lots of debugging statements",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    verbose_group.add_argument(
        "-v",
        "--verbose",
        help="Be verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
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

import gzip
from functools import partial
from pathlib import Path
from typing import List
from unittest.mock import Mock, PropertyMock, patch

import pytest
import yaml

from code_answer import answer


@pytest.fixture
def monkeypatch_get_url_content(data_dir, monkeypatch):
    patched_get_url_content = partial(_get_cached_url_content, data_dir=data_dir)
    monkeypatch.setattr(answer, "_get_url_content", patched_get_url_content)


@pytest.fixture(scope="module")
def data_answer(data_dir) -> dict:
    """test data for test_answer"""
    return _from_yaml(Path(data_dir / "queries.yaml"))


@pytest.fixture(scope="module")
def data_extract_answer(data_dir) -> dict:
    """test data for test_extract_answer"""
    return _from_yaml(Path(data_dir / "extract_answer.yaml"))


@pytest.fixture(scope="module")
def data_question_links(data_dir) -> dict:
    """test data for test_question_links"""
    return _from_yaml(Path(data_dir / "question_links.yaml"))


def _from_yaml(filepath: Path):
    with filepath.open("rt") as f:
        result = yaml.safe_load(f.read())
    return result


def _format_url_to_filename(url: str, ext: str = ".html") -> str:
    """Return the alnum char of url as filename, extention with ext.
    The result string (exclude ext) is <= 240"""
    filename = "".join(c for c in url.lower() if c.isalnum())
    return f"{filename[:240]}{ext}"


def _get_cached_url_content(url: str, data_dir: Path):
    """Given url, format the url to filename, then read the content from file"""
    filename = _format_url_to_filename(url, ".html.gz")
    filepath = data_dir / f"{filename}"
    with gzip.open(filepath, "rt") as f:
        return f.read()


def test_get_url_content():
    url, text = "https://www.google.com/search", "text"
    mock_resp = Mock()
    # Because of the way mock attributes are stored you can’t directly attach a
    # PropertyMock to a mock object.
    # Instead you can attach it to the mock type object:
    mock_text_property = PropertyMock(return_value=text)
    type(mock_resp).text = mock_text_property
    with patch("requests.get") as patcher:
        patcher.return_value = mock_resp
        result = answer._get_url_content(url)
        patcher.assert_called_once_with(url)
        mock_resp.raise_for_status.assert_called_once()
        assert result == text


def test_no_answers(data_extract_answer):
    data = data_extract_answer["no_answer_id"]
    _test_extract_answer(data["text"], data["expected"])


def test_no_pre_no_code_return_text(data_extract_answer):
    data = data_extract_answer["no_pre_no_code_return_text"]
    _test_extract_answer(data["text"], data["expected"])


def test_code_under_pre_return_code(data_extract_answer):
    data = data_extract_answer["code_under_pre_return_code"]
    _test_extract_answer(data["text"], data["expected"])


def _test_extract_answer(text: str, expected: str):
    result = answer._extract_answer(text)
    if result:
        result = result.strip()
    assert result == expected


def test_get_question_links(monkeypatch_get_url_content, data_question_links):
    data = data_question_links["stack_trace_python"]
    _test_get_question_links(data["query"], data["question_links"])


def test_get_question_links_no_link(monkeypatch_get_url_content):
    _test_get_question_links("cook", [])


def _test_get_question_links(query: str, expected: List[str]):
    got = answer.get_question_links(query)
    assert got == expected


def test_answer_should_throw_connection_error(monkeypatch):
    query = "any"
    resp = Mock(side_effect=answer.ConnectionError(query))
    monkeypatch.setattr(answer, "_get_url_content", resp)
    with pytest.raises(answer.ConnectionError) as e:
        answer.answer(query)
    assert query in str(e.value)


def test_answer_GetQuestionLinksError(monkeypatch):
    url, query = "any_url", "any"
    resp = Mock(side_effect=answer.RequestException(url, query))
    monkeypatch.setattr(answer, "_get_url_content", resp)
    with pytest.raises(answer.GetQuestionLinksError) as e:
        answer.answer(query)
    assert url, query in str(e.value)


def test_answer_GetAnswerError(monkeypatch):
    url, query = "any_url", "any"
    resp = Mock(side_effect=answer.RequestException(url, query))
    monkeypatch.setattr(answer, "_get_url_content", resp)
    with pytest.raises(answer.GetAnswerError) as e:
        answer.get_answer(query)
    assert url, query in str(e.value)


def test_answer(monkeypatch_get_url_content, data_answer):
    query = data_answer["stack_trace_python_1"]
    _test_answer(query)


def test_answer_return_text_when_no_code(monkeypatch_get_url_content, data_answer):
    query = data_answer["hello_world"]
    _test_answer(query)


def test_answer_num_answers(monkeypatch_get_url_content, data_answer):
    query = data_answer["stack_trace_python_2"]
    _test_answer(query)


def test_answer_no_question_links(monkeypatch_get_url_content, data_answer):
    query = data_answer["cook"]
    _test_answer(query)


def _test_answer(query):
    got = answer.answer(query["query"], query["num_answer"])
    _validate_answers(got, query["answers"])


def _validate_answer(tuple_form: answer.Answer, dict_form: dict):
    for key in tuple_form._fields:
        assert getattr(tuple_form, key) == dict_form[key]


def _validate_answers(tuples: List[answer.Answer], dicts: List[dict]):
    assert len(tuples) == len(dicts)
    for tuple_form, dict_form in zip(tuples, dicts):
        _validate_answer(tuple_form, dict_form)

from snes.data.preprocess import split_paragraphs


def test_split_paragraphs_blank_lines():
    text = "Para1\n\nPara2\n\n\nPara3\n"
    parts = split_paragraphs(text)
    assert parts == ["Para1", "Para2", "Para3"]


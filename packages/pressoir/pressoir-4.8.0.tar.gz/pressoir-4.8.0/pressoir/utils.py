import hashlib
import re
from pathlib import Path

from . import ROOT_DIR

html_comments_re = re.compile(r"<!--.*?-->")
html_tags_re = re.compile(r"<[^>]*>")


def strip_html_comments(value):
    if not value:
        return ""
    return html_comments_re.sub("", value)


def strip_html_tags(value):
    if not value:
        return ""
    return html_tags_re.sub("", value)


def get_template_path(repository_path, name):
    """Try to find it within the book folder, fallback on pressoir one."""
    template_path = repository_path / "templates" / name
    if not template_path.exists():
        template_path = ROOT_DIR / "templates" / name
    return template_path


def each_file_from(source_dir, pattern="*.html", exclude=None):
    """Walk across the `source_dir` and return the html file paths."""
    for path in _each_path_from(source_dir, pattern=pattern, exclude=exclude):
        if path.is_file():
            yield path


def each_folder_from(source_dir, exclude=None):
    """Walk across the `source_dir` and return the folder paths."""
    for path in _each_path_from(source_dir, exclude=exclude):
        if path.is_dir():
            yield path


def _each_path_from(source_dir, pattern="*", exclude=None):
    for path in sorted(Path(source_dir).glob(pattern)):
        if exclude is not None and path.name in exclude:
            continue
        yield path


def generate_md5(content):
    return hashlib.md5(content.encode()).hexdigest()


def neighborhood(iterable, first=None, last=None):
    """
    Yield the (index, previous, current, next) items given an iterable.

    You can specify a `first` and/or `last` item for bounds.
    """
    index = 1
    iterator = iter(iterable)
    previous = first
    current = next(iterator)  # Throws StopIteration if empty.
    for next_ in iterator:
        yield (index, previous, current, next_)
        previous = current
        index += 1
        current = next_
    yield (index, previous, current, last)

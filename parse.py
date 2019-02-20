

import click
import lxml.html
import re
import pandas as pd

from lxml.html.clean import Cleaner
from tqdm import tqdm


def close_tag_line(line, tags):
    """<tag>XXX --> <tag>XXX</tag>

    Args:
        line (str)
        tags (set<str>)
    """
    tag_pat = '|'.join(tags)

    match = re.match(f'<(?P<tag>[{tag_pat}]*)>[^<]*$', line, re.I)

    if match:
        tag = match.group('tag')
        line += f'</{tag}>'

    return line


def rows_iter(tree):
    """Assemble (age, region, author, title) from tag order.
    """
    age, region, author = None, None, None

    for el in tqdm(tree.iter()):

        if el.tag == 'h2':
            age = el.text_content()

        elif el.tag == 'h3':
            region = el.text_content()

        elif el.tag == 'li':

            next_el = el.getnext()

            if next_el.tag == 'dd':
                author = el.text_content()

            else:
                author = None
                yield (age, region, author, el.text_content())

        elif el.tag == 'dd':
            yield (age, region, author, el.text_content())


# TODO: Be smarter here. Breaks on:
# Diego de San Pedro
# Alfred, Lord Tennyson

# TODO: Parse middle names? Eg:
# Frederick Goddard Tuckerman

def split_given_surname(name):
    """Split out the author surname.
    """
    name = name or ''

    parts = name.split(' ')
    given_name = ' '.join(parts[:-1]) or None
    surname = parts[-1] or None

    return given_name, surname


@click.command()
@click.argument('src', type=click.Path(), default='bloom.html')
def parse(src):
    """Parse HTML, dump formats.
    """
    with open(src) as fh:
        lines = fh.read().replace('\t', '').splitlines()

    # Close un-closed li/dd.
    lines = [close_tag_line(line, {'li', 'dd'}) for line in lines]

    # Parse HTML.
    html = '\n'.join(lines)
    tree = lxml.html.document_fromstring(html)

    rows = list(rows_iter(tree))

    columns = ('age', 'region', 'author', 'title')
    df = pd.DataFrame(rows, columns=columns)

    # Strip field values.
    for c in df.columns:
        df[c] = df[c].str.strip()

    given_name, surname = zip(*df.author.apply(split_given_surname))
    df['given_name'] = given_name
    df['surname'] = surname

    df['id'] = df.index

    df.to_json('canon.json', orient='records', lines=True)
    df.to_csv('canon.csv')


if __name__ == '__main__':
    parse()

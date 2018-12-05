

import click
import lxml.html
import re
import pandas as pd

from lxml.html.clean import Cleaner
from tqdm import tqdm


def close_li(line):
    """Close an open <li>.
    """
    if re.match('<li>[^<]*$', line):
        line += '</li>'

    return line


@click.command()
@click.argument('src', type=click.Path(), default='bloom.html')
def parse(src):
    """Parse HTML, dump formats.
    """
    with open(src) as fh:
        lines = fh.read().replace('\t', '').splitlines()

    # Close un-closed <li> tags.'
    lines = list(map(close_li, lines))

    # Parse HTML.
    html = '\n'.join(lines)
    tree = lxml.html.document_fromstring(html)

    # Stip <cite> tags.
    cleaner = Cleaner(remove_tags=['cite'])
    tree = cleaner.clean_html(tree)

    rows = []
    age, region, author = None, None, None

    for el in tqdm(tree.iter()):

        if el.tag == 'h2':
            age = el.text

        elif el.tag == 'h3':
            region = el.text

        elif el.tag == 'li':

            next_el = el.getnext()

            if next_el.tag == 'dd':
                author = el.text

            else:
                author = None
                rows.append((age, region, author, el.text))

        elif el.tag == 'dd':
            rows.append((age, region, author, el.text))

    df = pd.DataFrame(rows, columns=('age', 'region', 'author', 'title'))

    for c in df.columns:
        df[c] = df[c].str.strip()

    df.to_json('canon.json', orient='records', lines=True)
    df.to_csv('canon.csv')


if __name__ == '__main__':
    parse()

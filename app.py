from flask import Flask, render_template
from werkzeug.contrib.cache import MemcachedCache
from rodong import RodongSinmun
from dissoc import Dissoc
from time import time
import logging
import os

CACHE_LIFETIME_S = 604800 # One week
MIN_LENGTH_TO_AVG_RATIO = 0.5

app = Flask('continuous-revolution')

# Set up logging before anything else
handler = logging.StreamHandler()
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
)

# Connect to memcached
app.cache = MemcachedCache(
    [os.environ['MEMCACHE_PORT'].lstrip('tcp://')],
    key_prefix='crev::',
    default_timeout=CACHE_LIFETIME_S
)

SECTIONS = {
    'editorial': 'Editorial'
}

@app.route('/')
def test():
    update_corpus()
    return render_template(
        'page.html',
        text=generate_text('editorial')
    )

def update_corpus():
    """ Updates the corpus if it has expired. """
    scraper = RodongSinmun()

    for section_key in SECTIONS.keys():
        if app.cache.get('corpora/' + section_key) is None:
            app.logger.info("Rebuilding corpus for key '{0}'".format(section_key))
            app.cache.set(
                'corpora/' + section_key,
                [article.text for article in scraper[section_key]]
            )
            app.logger.info('Corpus updated.')

def generate_text(section_key):
    """ Grab the corpus and use it to produce some nonsense. """
    corpus = app.cache.get('corpora/' + section_key)
    article_lengths = [len(a) for a in corpus]
    avg_article_length = sum(article_lengths) / len(article_lengths)
    min_length = MIN_LENGTH_TO_AVG_RATIO * avg_article_length

    dissoc = Dissoc(n=3)
    dissoc.train([a.replace(u'\xa0', ' ') for a in corpus])

    result = ''
    while len(result) < min_length:
        result += dissoc.produce() + "\n"

    return result

if __name__ == '__main__':
    app.run()

from flask import Flask, render_template
from werkzeug.contrib.cache import MemcachedCache
from rodong import RodongSinmun
from dissoc import Dissoc
from time import time
import logging
import os

CACHE_LIFETIME_S = 21600 # Six hours
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
    key_prefix='crev::'
)

SECTIONS = {
    'editorial': 'Editorial'
}

@app.route('/')
def test():
    return render_template(
        'page.html',
        text=generate_text('editorial')
    )

def update_corpus():
    """ Updates the corpus if it has expired. """
    scraper = RodongSinmun()

    for section_key in SECTIONS.keys():
        expiry_key = 'expiry/' + section_key
        expiry = app.cache.get(expiry_key)
        if expiry < time():
            app.logger.info("Rebuilding corpus for key '{0}'".format(section_key))
            app.cache.set(
                'corpora/' + section_key,
                [article.text for article in scraper[section_key]]
            )
            app.cache.set(expiry_key, int(time() + CACHE_LIFETIME_S))

    app.logger.info('Corpus updated.')

def generate_text(section_key):
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

# Build our corpus before anything runs
update_corpus()

if __name__ == '__main__':
    app.run()

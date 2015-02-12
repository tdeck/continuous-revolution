from flask import Flask, render_template
from werkzeug.contrib.cache import MemcachedCache
#from logging.handlers import FileHandler
#from logging import Formatter
from rodong import RodongSinmun
from dissoc import Dissoc

CACHE_LIFETIME_S = 21600 # Six hours
MIN_LENGTH_TO_AVG_RATIO = 0.5

app = Flask('continuous-revolution')
cache = MemcachedCache(['127.0.0.1:11211'], key_prefix='crev::')
scraper = RodongSinmun()

'''
app.logger = FileHandler('crev.log')
app.logger.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
'''
app.debug = True

SECTIONS = {
    'editorial': 'Editorial'
}

@app.route('/')
def test():
    return render_template(
        'page.html',
        text=generate_text('editorial')
    )

@app.route('/_update')
def update_corpus():
    """ Updates the corpus if it has expired. """
    for section_key in SECTIONS.keys():
        cache_key = 'corpora/' + section_key

        corpus = cache.get(cache_key)
        if corpus is None:
            print "Reloading corpus for key {0}".format(key)
            cache.set(
                cache_key,
                [article.text for article in scraper[section_key]],
                timeout=CACHE_LIFETIME_S
            )

    return 'Ok.'

def generate_text(section_key):
    corpus = cache.get('corpora/' + section_key)
    article_lengths = [len(a) for a in corpus]
    avg_article_length = sum(article_lengths) / len(article_lengths)
    min_length = MIN_LENGTH_TO_AVG_RATIO * avg_article_length

    dissoc = Dissoc(n=3)
    dissoc.train(cache.get('corpora/' + section_key))

    result = ''
    while len(result) < min_length:
        result += dissoc.produce() + "\n"

    return result

if __name__ == '__main__':
    update_corpus()
    app.run()

from common import config
import argparse
import logging
import news_page_objects as news
import re
import datetime
import csv

from requests import HTTPError
from urllib3.exceptions import MaxRetryError

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
is_well_formed_link = re.compile(r'^https?://.+/.+$')
is_root_path = re.compile(r'^/.+$')


def _news_scraper(news_site_uid):
    host = config()['news_sites'][news_site_uid]['url']
    logging.info(f'==== Beginning scraper for {host} ====')

    homepage = news.HomePage(news_site_uid, host)

    articles = []
    for link in homepage.article_links:
        article = _fetch_article(news_site_uid, host, link)

        if article:
            logger.info('Article fetched!!!')
            articles.append(article)

    _save_articles(news_site_uid, articles)


def _save_articles(news_site_uid, articles):
    now = datetime.datetime.now()
    out_file_name = f'{news_site_uid}_{now.strftime(r"%Y_%m_%d")}_articles.csv'
    csv_headers = list(filter(lambda property: not property.startswith('_'), dir(articles[0])))

    with open(out_file_name, mode='w+') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

        for article in articles:
            row = [getattr(article, prop) for prop in csv_headers]
            writer.writerow(row)


def _fetch_article(news_site_uid, host, link):
    logger.info(f'Start fetching article at {link}')

    article = None
    try:
        article = news.ArticlePage(news_site_uid, _build_link(host, link))
    except (HTTPError, MaxRetryError) as e:
        logger.warning(f'While while fetching the article', exc_info=False)

    if article and not article.body:
        logger.warn('Invalid article. There is no body')
        return None

    return article


def _build_link(host, link):
    if is_well_formed_link.match(link):
        return link
    if is_root_path.match(link):
        return f'{host}{link}'
    else:
        return f'{host}/{link}'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    news_site_choices = list(config()['news_sites'].keys())
    parser.add_argument('news_site',
                        help='The news site that you want to scrape',
                        type=str,
                        choices=news_site_choices)

    args = parser.parse_args()
    _news_scraper(args.news_site)

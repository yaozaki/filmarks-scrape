#!/usr/bin/env python3

import csv
import sys
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Constants
BASE_URL = "https://filmarks.com"
RATING_CLASS = 'c-rating__score'
TITLE_CLASS = 'c-content-card__title'
REVIEW_LINK_CLASS = 'c-content-card__readmore-review'
REVIEW_DATE_CLASS = 'c-media__date'
MOVIE_DATE_CLASS = 'p-content-detail__other-info-title'

def help():
    HELP = """
    使用方法: python getreview.py {filmarks_username}
    
    説明:
    指定されたFilmarksのユーザー名に基づいてレビューを取得します。
    
    引数:
    {filmarks_username} : レビューを取得したいFilmarks（https://filmarks.com/）のユーザー名
    """
    print(HELP)
    sys.exit()

def clean_title(title):
    return re.sub(r'\(\d{4}年製作の映画\)', '', title).strip()

def get_soup(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_review_date(review_soup):
    date_element = review_soup.find('time', class_=REVIEW_DATE_CLASS)
    if date_element:
        return date_element.text.strip().split(' ')[0]
    return None

def extract_release_year(movie_soup):
    date_element = movie_soup.find('h3', class_=MOVIE_DATE_CLASS, string=re.compile('上映日：'))
    if date_element:
        match = re.search(r'(\d{4})年', date_element.text)
        return match.group(1) if match else None
    return None

def process_card(card, base_url, current_year):
    rating = card.find('div', class_=RATING_CLASS)
    title = card.find('h3', class_=TITLE_CLASS)
    review_link = card.find('span', class_=REVIEW_LINK_CLASS)

    if not all([rating, title, review_link]):
        return None

    rating_score = rating.text.strip()
    movie_title = clean_title(title.text.strip())
    review_a = review_link.find('a')
    title_a = title.find('a')

    if not all([review_a, title_a]) or 'href' not in review_a.attrs or 'href' not in title_a.attrs:
        return None

    review_url = f"{base_url}{review_a['href']}"
    movie_url = f"{base_url}{title_a['href']}"

    review_soup = get_soup(review_url)
    movie_soup = get_soup(movie_url)

    if not review_soup or not movie_soup:
        return None

    review_date = extract_review_date(review_soup)
    released_year = extract_release_year(movie_soup)

    if review_date and review_date.startswith(current_year):
        if released_year == current_year:
            return [rating_score, review_date, review_url, movie_title]
    else:
        # If the review date is not from the current year, signal to stop scraping
        return 'STOP'


def scrape_filmarks(username):
    user_url = f"{BASE_URL}/users/{username}"
    results = []
    current_year = str(datetime.now().year)

    page = 1
    while True:
        url = f"{user_url}?page={page}"
        soup = get_soup(url)
        
        if not soup:
            break

        cards = soup.find_all('div', class_='c-content-card')
        if not cards:
            break

        stop_scraping = False
        for card in cards:
            result = process_card(card, BASE_URL, current_year)
            if result == 'STOP':
                stop_scraping = True
                break
            elif result:
                results.append(result)
        
        if stop_scraping:
            break
        page += 1

    return results

def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Rating', 'Review Date', 'Review URL', 'Movie Title'])
        writer.writerows(data)

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in ['-h', '--help']:
        help()

    username = sys.argv[1]
    results = scrape_filmarks(username)
    import pdb; pdb.set_trace()
    if results != []:
        save_to_csv(results, f"{username}_reviews.csv")
        print(f"Data saved to {username}_reviews.csv")
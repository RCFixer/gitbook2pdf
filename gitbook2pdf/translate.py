import json
import string
import random
import requests
from bs4 import BeautifulSoup

from .config import TARGET_ALPHABET, SOURCE_LANG, TARGET_LANG, API_KEY, TRANSLATOR_ADRESS

IGNORE_TAGS = ['pre', 'code']
ORIGINAL_AND_TRANSLATE_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
INNER_TRANSLATE_TAGS = ['div', 'li']
TAG_WITH_CODE = ['p', 'li']
TAG_WITH_TEXT = ['p', 'li']

ALLOW_INNER_TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'ul', 'ol', 'img']


def check_alphabet(text, alphabet=TARGET_ALPHABET):
    return not alphabet.isdisjoint(text.lower())


def translate_text(text):
    if check_alphabet(text): # in case the text has already been translated
        return text
    url = TRANSLATOR_ADRESS
    data = {
        "q": text,
        "source": SOURCE_LANG,
        "target": TARGET_LANG,
        "format": "text",
        "api_key": API_KEY
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(data), headers=headers)
    result = response.json()
    return result['translatedText']


def transform_text(tag):
    if tag.name in INNER_TRANSLATE_TAGS and len(tag.contents) > 1:
        search_forward = False
        inner_tags = tag.find_all(recursive=False)
        if inner_tags:
            for inner_tag in inner_tags:
                if inner_tag.name not in ALLOW_INNER_TAGS:
                    search_forward = True
                    break
            if not search_forward:
                for inner_tag in inner_tags:
                    transform_text(inner_tag)
                return
    if tag.name in IGNORE_TAGS:
        pass
    elif tag.name in ORIGINAL_AND_TRANSLATE_TAGS and tag.string:
        tag.string = tag.string + f' ({translate_text(tag.string)})'
    elif tag.name in TAG_WITH_CODE and len(tag.contents) > 1 and tag.string is None:
        tag_text_list = [str(tag_part) for tag_part in tag.contents]
        code_blocks = {}
        for index, tag_text in enumerate(tag_text_list):
            if '<code>' in tag_text or '<img' in tag_text or '<a' in tag_text:
                id_element = ''.join(random.choices(string.digits, k=6))
                current_id = f' {id_element} '
                code_blocks[current_id] = tag_text
                tag_text_list[index] = current_id
        tag_text = ''.join(tag_text_list)
        tag_text = translate_text(tag_text)
        for key_uuid, value_code in code_blocks.items():
            tag_text = tag_text.replace(key_uuid.strip(), value_code)
        tag_text = f'<{tag.name}>{tag_text}</{tag.name}>'
        new_tag = BeautifulSoup(tag_text, 'html.parser')
        try:
            tag.replace_with(new_tag)
        except ValueError: # in case the tag has already been translated and replaced in the tree
            return
    elif tag.name in TAG_WITH_TEXT and len(tag.contents) == 1 and tag.string:
        tag.string = translate_text(tag.string)


def translate_main(html_doc):
    soup = BeautifulSoup(html_doc, 'lxml')
    tags = soup.find_all()
    for tag in tags:
        transform_text(tag)
    many_li = soup.find_all('li')
    for li in many_li:
        transform_text(li)

    return str(soup)

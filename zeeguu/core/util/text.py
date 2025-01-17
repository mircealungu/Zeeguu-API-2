import math

import nltk
import pyphen
import regex
from collections import Counter
from nltk import SnowballStemmer
from zeeguu.core.model.language import Language
from logging import log
from string import punctuation
import re


AVERAGE_SYLLABLE_LENGTH = 2.5

"""
    Collection of simple text processing functions
"""
NLTK_SUPPORTED_LANGUAGES = set(
    [
        "czech",
        "danish",
        "dutch",
        "english",
        "estonian",
        "finnish",
        "french",
        "german",
        "greek",
        "italian",
        "norwegian",
        "polish",
        "portuguese",
        "russian",
        "slovene",
        "spanish",
        "swedish",
        "turkish",
    ]
)


class Token:
    PUNCTUATION = "»«" + punctuation + "–—“‘”“’„¿"
    LEFT_PUNCTUATION = "«<({#„¿["
    RIGHT_PUNCTUATION = "»>)}“]"
    NUM_REGEX = re.compile(r"[0-9]+(\.|,)*[0-9]*")

    # I started from a generated Regex from Co-Pilot and then tested it
    # against a variety of reandom generated links. Generally it seems to work fine,
    # but not likely to be perfect in all situations.
    EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
    URL_REGEX = re.compile(
        r"(((http|https)://)?(www\.)?([a-zA-Z0-9@\-/\.]+\.[a-z]{1,4}/([a-zA-Z0-9?=\.&#/]+)?)+)"
    )

    @classmethod
    def is_like_email(cls, text):
        return Token.EMAIL_REGEX.match(text) is not None

    @classmethod
    def is_like_url(cls, text):
        return Token.URL_REGEX.match(text) is not None

    @classmethod
    def is_punctuation(cls, text):
        return text in Token.PUNCTUATION or text == "..."

    @classmethod
    def _token_punctuation_processing(cls, text):
        """
        The tokenizer alters the text, so we need to revert some of the changes
        to allow the frontend an easier time to render the text.
        """
        text = text.replace("``", '"')
        text = text.replace("''", '"')
        return text

    def __init__(self, text, par_i=None, sent_i=None, token_i=None):
        """
        sent_i - the sentence in the overall text.
        token_i - the index of the token in the original sentence.
        """
        self.text = Token._token_punctuation_processing(text)
        self.is_sent_start = token_i == 0
        self.is_punct = Token.is_punctuation(self.text)
        self.is_left_punct = text in Token.LEFT_PUNCTUATION
        self.is_right_punct = text in Token.RIGHT_PUNCTUATION
        self.par_i = par_i
        self.sent_i = sent_i
        self.token_i = token_i
        self.is_like_email = Token.is_like_email(text)
        self.is_like_url = Token.is_like_url(text)
        self.is_like_num = Token.NUM_REGEX.match(text) is not None

    def __repr__(self):
        return self.text

    def as_serializable_dictionary(self):
        return {
            "text": self.text,
            "is_sent_start": self.is_sent_start,
            "is_punct": self.is_punct,
            "is_left_punct": self.is_left_punct,
            "is_right_punct": self.is_right_punct,
            "is_like_num": self.is_like_num,
            "sent_i": self.sent_i,
            "token_i": self.token_i,
            "paragraph_i": self.par_i,
            "is_like_email": self.is_like_email,
            "is_like_url": self.is_like_url,
        }


def split_into_paragraphs(text):
    paragraph_delimiter = re.compile(r"\n\n")
    return paragraph_delimiter.split(text)


def split_words_from_text(text):
    words = regex.findall(r"(\b\p{L}+\b)", text)
    return words


def text_preprocessing(text: str):
    """
    Preprocesses the text by replacing some apostraphe characters to a standard one.
    """
    # For French & Italian, the tokenizer doesn't recognize ’, but it works
    # if ' is used.
    text = text.replace("’", "'")
    # For Spanish "¿" is attached to the first word, so we need to add a space
    text = text.replace("¿", "¿ ")
    # For cases where the tick is attached to the word
    apostrophe_before_word = re.compile(r"(')([\w]+)")
    text, total_subs = apostrophe_before_word.subn(
        lambda m: f"{m.group(1)} {m.group(2)}", text
    )
    return text


def replace_email_url_with_placeholder(text: str):
    """
    The tokenizer has issues tokenizing emails and urls.
    To avoid this, we replace them with a placeholder:
    _EMAIL_ and _URL_
    """

    def _has_protocol(url_match):
        return url_match[2] != ""

    urls = Token.URL_REGEX.findall(text)
    for url in urls:
        text = text.replace(url[0], "_URL_ ")
    emails = Token.EMAIL_REGEX.findall(text)
    for email in emails:
        text = text.replace(email, "_EMAIL_ ")

    url_links = [url[0] if _has_protocol(url) else "https://" + url[0] for url in urls]

    return (
        text,
        emails,
        url_links,
    )


def is_nltk_supported_language(language: Language):
    return language.name.lower() in NLTK_SUPPORTED_LANGUAGES


def _get_token(t, par_i, sent_i, w_i, email, url, as_serializable_dictionary):
    if t == "_EMAIL_":
        t = email.pop(0)
    if t == "_URL_":
        t = url.pop(0)

    token = Token(t, par_i, sent_i, w_i)
    return token.as_serializable_dictionary() if as_serializable_dictionary else token


def tokenize_text(text: str, language: Language, as_serializable_dictionary=True):

    if not is_nltk_supported_language(language):
        print(
            f"Failed 'tokenize_text' for language: '{language.name.lower()}', defaulted to 'english'"
        )
        language = Language.find("en")

    text = text_preprocessing(text)
    text, email, url = replace_email_url_with_placeholder(text)

    tokens = [
        [
            [
                (
                    _get_token(
                        w, par_i, sent_i, w_i, email, url, as_serializable_dictionary
                    )
                )
                for w_i, w in enumerate(
                    nltk.tokenize.word_tokenize(sent, language=language.name.lower())
                )
            ]
            for sent_i, sent in enumerate(
                sent_tokenizer_text(paragraph, language=language)
            )
        ]
        for par_i, paragraph in enumerate(split_into_paragraphs(text))
    ]
    return tokens


def tokenize_text_flat_array(
    text: str, language: Language, as_serializable_dictionary=True
):
    if not is_nltk_supported_language(language):
        print(
            f"Failed 'tokenize_text_flat_array' for language: '{language.name.lower()}', defaulted to 'english'"
        )
        language = Language.find("en")

    text = text_preprocessing(text)
    text, email, url = replace_email_url_with_placeholder(text)

    tokens = [
        _get_token(w, par_i, sent_i, w_i, email, url, as_serializable_dictionary)
        for par_i, paragraph in enumerate(split_into_paragraphs(text))
        for sent_i, sent in enumerate(sent_tokenizer_text(paragraph, language=language))
        for w_i, w in enumerate(
            nltk.tokenize.word_tokenize(sent, language=language.name.lower())
        )
    ]
    return tokens


def sent_tokenizer_text(text: str, language: Language):
    if not is_nltk_supported_language(language):
        print(
            f"Failed 'sent_tokenize' for language: '{language.name.lower()}', defaulted to 'english'",
        )
        language = Language.find("en")
    return nltk.tokenize.sent_tokenize(text, language=language.name.lower())


def number_of_sentences(text):
    return len(nltk.sent_tokenize(text))


def split_unique_words_from_text(text, language: Language):
    words = split_words_from_text(text)
    stemmer = SnowballStemmer(language.name.lower())
    return set([stemmer.stem(w.lower()) for w in words])


def length(text):
    return len(split_words_from_text(text))


def unique_length(text, language: Language):
    words_unique = split_unique_words_from_text(text, language)
    return len(words_unique)


def average_sentence_length(text):
    return length(text) / number_of_sentences(text)


def median_sentence_length(text):
    sentence_lengths = [length(s) for s in nltk.sent_tokenize(text)]
    sentence_lengths = sorted(sentence_lengths)

    return sentence_lengths[int(len(sentence_lengths) / 2)]


def number_of_syllables(text, language: Language):
    words = [w.lower() for w in split_words_from_text(text)]

    number_of_syllables = 0
    for word, freq in Counter(words).items():
        if language.code == "zh-CN":
            syllables = int(math.floor(max(len(word) / AVERAGE_SYLLABLE_LENGTH, 1)))
        else:
            dic = pyphen.Pyphen(lang=language.code)
            syllables = len(dic.positions(word)) + 1

        number_of_syllables += syllables * freq

    return number_of_syllables


def average_word_length(text, language: Language):
    return number_of_syllables(text, language) / length(text)


def median_word_length(text, language: Language):
    word_lengths = [
        number_of_syllables(w, language) for w in split_words_from_text(text)
    ]
    return word_lengths[int(len(word_lengths) / 2)]

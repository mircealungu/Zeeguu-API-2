from . import api

from zeeguu.api.utils.route_wrappers import cross_domain, requires_session
from zeeguu.api.utils.json_result import json_result
from flask import request

from zeeguu.core.nlp_pipeline import SpacyWrappers, NoiseWordsGenerator
from zeeguu.core.nlp_pipeline import AutoGECTagging, ContextReducer
from zeeguu.core.model.language import Language
from zeeguu.core.util.text import (
    tokenize_text,
    sent_tokenizer_text,
    split_into_paragraphs,
)


# ---------------------------------------------------------------------------
@api.route("/do_some_spacy", methods=("POST",))
# ---------------------------------------------------------------------------
@cross_domain
@requires_session
def do_some_spacy():
    phrase = request.form.get("phrase", "")
    language = request.form.get("language")

    if language not in SpacyWrappers.keys():
        return "Language not supported"

    tokens = SpacyWrappers[language].tokenize_sentence(phrase)

    return json_result(tokens)


# ---------------------------------------------------------------------------
@api.route("/create_confusion_words", methods=("POST",))
# ---------------------------------------------------------------------------
@cross_domain
@requires_session
def create_confusion_words():
    original_sent = request.form.get("original_sent", "")
    language = request.form.get("language")

    if language not in SpacyWrappers.keys():
        return "Language not supported"

    # We should pass the student bookmark words as a fallback when no words are found.
    noise_words = NoiseWordsGenerator[language].generate_confusion_words(original_sent)
    return json_result(noise_words)


# ---------------------------------------------------------------------------
@api.route("/annotate_clues", methods=("POST",))
# ---------------------------------------------------------------------------
@cross_domain
@requires_session
def annotate_clues():
    word_with_props = request.form.get("word_with_props", "")
    original_sentence = request.form.get("original_sentence", "")
    language = request.form.get("language")

    if language not in SpacyWrappers.keys():
        return "Language not supported"

    updated_words = AutoGECTagging(SpacyWrappers[language], language).anottate_clues(
        word_with_props, original_sentence
    )

    return json_result(updated_words)


# ---------------------------------------------------------------------------
@api.route("/get_shorter_similar_sents_in_article", methods=("POST",))
# ---------------------------------------------------------------------------
@cross_domain
@requires_session
def get_shorter_similar_sents_in_article():
    article_text = request.form.get("article_text", "")
    bookmark_context = request.form.get("bookmark_context", "")
    language = request.form.get("language")

    if language not in SpacyWrappers.keys():
        return "Language not supported"

    nlp_pipe = SpacyWrappers[language]

    result_json = ContextReducer.get_similar_sentences(
        nlp_pipe, article_text, bookmark_context
    )

    return json_result(result_json)


# ---------------------------------------------------------------------------
@api.route("/get_smaller_context", methods=("POST",))
# ---------------------------------------------------------------------------
@cross_domain
@requires_session
def get_smaller_context():
    bookmark_context = request.form.get("bookmark_context", "")
    bookmark_word = request.form.get("bookmark_word", "")
    language = request.form.get("language")
    max_context = int(request.form.get("max_context_len"))

    if language not in SpacyWrappers.keys():
        return "Language not supported"

    nlp_pipe = SpacyWrappers[language]
    new_context_max_len = max_context
    shorter_context = ContextReducer.reduce_context_for_bookmark(
        nlp_pipe, bookmark_context, bookmark_word, new_context_max_len
    )

    return json_result(shorter_context)


# ---------------------------------------------------------------------------
@api.route("/tokenize_text", methods=("POST",))
# ---------------------------------------------------------------------------
@cross_domain
@requires_session
def get_tokenize_text():
    """
    Used by the front-end to tokenize texts. Receives a string of text, and a
    language of the text and returns the tokenized version, cosisting of a
    list of Paragraphs composed of tokens.
    """
    text = request.form.get("text", "")
    lang_code = request.form.get("language", "")
    language = Language.find(lang_code)
    result = tokenize_text(text, language)
    return json_result(result)


# ---------------------------------------------------------------------------
@api.route("/tokenize_sents", methods=("POST",))
# ---------------------------------------------------------------------------
@cross_domain
@requires_session
def get_tokenize_sents():
    """
    Used by the front-end to tokenize sentences in texts. Receives a string of text, and
    a language of the text and returns the tokenized version.
    """
    text = request.form.get("text", "")
    lang_code = request.form.get("language", "")
    language = Language.find(lang_code)
    result = sent_tokenizer_text(text, language)
    return json_result(result)


# ---------------------------------------------------------------------------
@api.route("/get_paragraphs", methods=("POST",))
# ---------------------------------------------------------------------------
@cross_domain
@requires_session
def get_paragraphs():
    """
    Returns the pagraphs of a text.
    """
    text = request.form.get("text", "")
    result = split_into_paragraphs(text)
    return json_result(result)

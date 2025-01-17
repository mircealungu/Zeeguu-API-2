from string import punctuation
from urllib.parse import unquote_plus
import os

import flask
from flask import request

from zeeguu.api.utils.translator import (
    get_next_results,
    contribute_trans,
)

from python_translators.translation_query import TranslationQuery

from zeeguu.core.crowd_translations import (
    get_own_past_translation,
)
from zeeguu.core.model import Bookmark, Article, Text, User
from zeeguu.core.model.user_word import UserWord
from . import api, db_session
from zeeguu.api.utils.json_result import json_result
from zeeguu.api.utils.route_wrappers import cross_domain, requires_session
from zeeguu.api.utils.parse_json_boolean import parse_json_boolean

punctuation_extended = "»«" + punctuation
IS_DEV_SKIP_TRANSLATION = int(os.environ.get("DEV_SKIP_TRANSLATION", 0)) == 1


@api.route("/get_one_translation/<from_lang_code>/<to_lang_code>", methods=["POST"])
@cross_domain
@requires_session
def get_one_translation(from_lang_code, to_lang_code):
    """

    To think about:
    - it would also make sense to separate translation from
    "logging"; or at least, allow for situations where a translation
    is not associated with an url... or?
    - jul 2021 - Bjorn would like to have the possibility of getting
    a translation without an article; can be done; allow for the
    articleID to be empty; what would be the downside of that?
    - hmm. maybe he can simply work with get_multiple_translations

    :return: json array with translations
    """

    word_str = request.form["word"].strip(punctuation_extended)
    w_sent_i = request.form.get("w_sent_i", None)
    w_token_i = request.form.get("w_token_i", None)
    w_total_tokens = request.form.get("w_total_tokens", None)
    context = request.form.get("context", "").strip()
    c_paragraph_i = request.form.get("c_paragraph_i", None)
    c_sent_i = request.form.get("c_sent_i", None)
    c_token_i = request.form.get("c_token_i", None)
    article_id = request.form.get("articleID", None)
    in_content = parse_json_boolean(request.form.get("in_content", None))
    query = TranslationQuery.for_word_occurrence(word_str, context, 1, 7)

    # if we have an own translation that is our first "best guess"
    # ML: TODO:
    # - word translated in the same text / articleID / url should still be considered
    # even if not exactly this context
    # - a teacher's translation or a senior user's should still
    # be considered here
    print("getting own past translation....")
    user = User.find_by_id(flask.g.user_id)
    bookmark = get_own_past_translation(
        user, word_str, from_lang_code, to_lang_code, context
    )
    if bookmark:
        best_guess = bookmark.translation.word
        likelihood = 1
        source = "Own past translation"
        print(f"about to return {bookmark}")
    else:
        # TODO: must remove theurl, and title - they are not used in the calling method.
        if IS_DEV_SKIP_TRANSLATION:
            print("Dev Skipping Translation")
            best_guess = f"T-({to_lang_code})-'{word_str}'"
            likelihood = None
            source = "DEV_SKIP"
        else:
            translations = get_next_results(
                {
                    "from_lang_code": from_lang_code,
                    "to_lang_code": to_lang_code,
                    "word": word_str,
                    "query": query,
                    "context": context,
                },
                number_of_results=3,
            ).translations
            best_guess = translations[0]["translation"]
            likelihood = translations[0].pop("quality")
            source = translations[0].pop("service_name")
        user = User.find_by_id(flask.g.user_id)
        bookmark = Bookmark.find_or_create(
            db_session,
            user,
            word_str,
            from_lang_code,
            best_guess,
            to_lang_code,
            context,
            article_id,
            c_paragraph_i=c_paragraph_i,
            c_sentence_i=c_sent_i,
            c_token_i=c_token_i,
            in_content=in_content,
            sentence_i=w_sent_i,
            token_i=w_token_i,
            total_tokens=w_total_tokens,
        )

    return json_result(
        {
            "translation": best_guess,
            "bookmark_id": bookmark.id,
            "source": source,
            "likelihood": likelihood,
        }
    )


@api.route(
    "/get_multiple_translations/<from_lang_code>/<to_lang_code>", methods=["POST"]
)
@cross_domain
@requires_session
def get_multiple_translations(from_lang_code, to_lang_code):
    """
    Returns a list of possible translations in :param to_lang_code
    for :param word in :param from_lang_code except a translation
    from :service

    You must also specify the :param context, :param url, and :param title
     of the page where the word was found.

    The context is the sentence.

    :return: json array with translations
    """

    word_str = request.form["word"].strip(punctuation_extended)
    context = request.form.get("context", "").strip()
    number_of_results = int(request.form.get("numberOfResults", -1))
    translation_to_exclude = request.form.get("translationToExclude", "")
    service_to_exclude = request.form.get("serviceToExclude", "")

    exclude_services = [] if service_to_exclude == "" else [service_to_exclude]
    exclude_results = (
        [] if translation_to_exclude == "" else [translation_to_exclude.lower()]
    )

    query = TranslationQuery.for_word_occurrence(word_str, context, 1, 7)

    data = {
        "from_lang_code": from_lang_code,
        "to_lang_code": to_lang_code,
        "word": word_str,
        "query": query,
        "context": context,
    }

    translations = get_next_results(
        data,
        exclude_services=exclude_services,
        exclude_results=exclude_results,
        number_of_results=number_of_results,
    ).translations

    # translators talk about quality, but our users expect likelihood.
    # rename the key in the dictionary
    for t in translations:
        t["likelihood"] = t.pop("quality")
        t["source"] = t["service_name"]

    # ML: Note: We used to save the first bookmark here;
    # but that does not make sense; this is used to show all
    # alternatives; why save the first to the DB?
    # But leaving this note here just in case...

    return json_result(dict(translations=translations))


@api.route("/update_bookmark/<bookmark_id>", methods=["POST"])
@cross_domain
@requires_session
def update_translation(bookmark_id):
    """

        User updates a bookmark

    :return: in case of success, the bookmark_id

    """

    # All these POST params are mandatory
    word_str = unquote_plus(request.form["word"]).strip(punctuation_extended)
    translation_str = request.form["translation"]
    context_str = request.form.get("context", "").strip()

    bookmark = Bookmark.find(bookmark_id)

    origin = UserWord.find_or_create(db_session, word_str, bookmark.origin.language)
    translation = UserWord.find_or_create(
        db_session, translation_str, bookmark.translation.language
    )
    prev_text = Text.find_by_id(bookmark.text_id)
    is_same_context = prev_text.content == context_str
    text = Text.find_or_create(
        db_session,
        context_str,
        bookmark.origin.language,
        bookmark.text.url,
        bookmark.text.article if is_same_context else None,
        prev_text.paragraph_i if is_same_context else None,
        prev_text.sentence_i if is_same_context else None,
        prev_text.token_i if is_same_context else None,
        prev_text.in_content if is_same_context else None,
    )

    bookmark.origin = origin
    bookmark.translation = translation
    bookmark.text = text

    if not is_same_context or bookmark.origin.word != word_str:
        # In the frontend it's mandatory that the bookmark is in the text,
        # so we update the pointer.
        from zeeguu.core.util.text import tokenize_text_flat_array

        # Tokenized text returns paragraph, sents, token
        # Since we know there is not multiple paragraphs, we take the first
        tokenized_text = tokenize_text_flat_array(
            text.content, bookmark.origin.language, False
        )
        tokenized_bookmark = tokenize_text_flat_array(
            word_str, bookmark.origin.language, False
        )
        first_token_ocurrence = next(
            filter(lambda t: t.text == tokenized_bookmark[0].text, tokenized_text)
        )

        bookmark.sentence_i = first_token_ocurrence.sent_i
        bookmark.token_i = first_token_ocurrence.token_i
        bookmark.total_tokens = len(tokenized_bookmark)

    db_session.add(bookmark)
    db_session.commit()

    return bookmark_id


@api.route("/contribute_translation/<from_lang_code>/<to_lang_code>", methods=["POST"])
@cross_domain
@requires_session
def contribute_translation(from_lang_code, to_lang_code):
    """

        User contributes a translation they think is appropriate for
         a given :param word in :param from_lang_code in a given :param context

        The :param translation is in :param to_lang_code

        Together with the two words and the textual context, you must submit
         also the :param url, :param title of the page where the original
         word and context occurred.

    :return: in case of success, the bookmark_id and main translation

    """

    # All these POST params are mandatory
    word_str = unquote_plus(request.form["word"])
    translation_str = request.form["translation"]
    url = request.form.get("url", "")
    context_str = request.form.get("context", "")
    title_str = request.form.get("title", "")
    # when a translation is added by hand, the servicename_translation is None
    # thus we set it to MANUAL
    service_name = request.form.get("servicename_translation", "MANUAL")
    article_id = None
    if "articleID" in url:
        article_id = url.split("articleID=")[-1]
        url = Article.query.filter_by(id=article_id).one().url.as_canonical_string()
    elif "articleURL" in url:
        url = url.split("articleURL=")[-1]
    elif "article?id=" in url:
        article_id = url.split("article?id=")[-1]
        url = Article.query.filter_by(id=article_id).one().url.as_canonical_string()
    else:
        # the url comes from elsewhere not from the reader, so we find or create the article
        article = Article.find_or_create(db_session, url)
        article_id = article.id

    # Optional POST param
    selected_from_predefined_choices = request.form.get(
        "selected_from_predefined_choices", ""
    )
    user = User.find_by_id(flask.g.user_id)
    bookmark = Bookmark.find_or_create(
        db_session,
        user,
        word_str,
        from_lang_code,
        translation_str,
        to_lang_code,
        context_str,
        article_id,
    )

    # Inform apimux about translation selection
    data = {
        "word_str": word_str,
        "translation_str": translation_str,
        "url": url,
        "context_size": len(context_str),
        "service_name": service_name,
    }
    contribute_trans(data)

    return json_result(dict(bookmark_id=bookmark.id))


@api.route("/basic_translate/<from_lang_code>/<to_lang_code>", methods=["POST"])
@cross_domain
@requires_session
def basic_translate(from_lang_code, to_lang_code):
    phrase = request.form["phrase"].strip(punctuation_extended)

    query = TranslationQuery.for_word_occurrence(phrase, "", 1, 7)

    payload = {
        "from_lang_code": from_lang_code,
        "to_lang_code": to_lang_code,
        "word": phrase,
        "query": query,
        "context": "",
    }

    translations = get_next_results(
        payload,
        number_of_results=1,
    ).translations

    best_guess = translations[0]["translation"]
    likelihood = translations[0].pop("quality")
    source = translations[0].pop("service_name")

    return json_result(
        {
            "translation": best_guess,
            "source": source,
            "likelihood": likelihood,
        }
    )

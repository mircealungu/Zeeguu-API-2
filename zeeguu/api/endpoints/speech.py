import os.path
import re

from flask import request

from zeeguu.api.endpoints import api
from zeeguu.api.utils import cross_domain, requires_session
from zeeguu.core.model import Article

DATA_FOLDER = os.environ.get("ZEEGUU_DATA_FOLDER")

# See: https://cloud.google.com/text-to-speech/docs/voices
PREFERRED_VOICES = {
    "da": "da-DK-Wavenet-D",
    "fr": "fr-FR-Neural2-C",
    "en": "en-US",
    "nl": "nl-NL-Wavenet-B",
    "de": "de-DE-Neural2-C",
    "it": "it-IT-Neural2-A",
    "pt": "pt-PT-Wavenet-A",
}


def voice_for_language(language_id):
    if PREFERRED_VOICES.get(language_id):
        return PREFERRED_VOICES[language_id]
    return _code_from_id(language_id) + "-Standard-A"


@api.route("/text_to_speech", methods=("POST",))
@cross_domain
@requires_session
def tts():
    import zeeguu.core
    from zeeguu.core.model import UserWord, Language

    db_session = zeeguu.core.model.db.session

    text_to_pronounce = request.form.get("text", "")
    language_id = request.form.get("language_id", "")

    if not text_to_pronounce:
        return ""

    user_word = UserWord.find_or_create(
        db_session, text_to_pronounce, Language.find_or_create(language_id)
    )

    audio_file_path = _file_name_for_user_word(user_word, language_id)

    if not os.path.isfile(DATA_FOLDER + audio_file_path):
        _save_speech_to_file(user_word.word, language_id, audio_file_path)

    print(audio_file_path)
    return audio_file_path


@api.route("/mp3_of_full_article", methods=("POST",))
@cross_domain
@requires_session
def mp3_of_full_article():
    print("in mp3_of_full_article")
    import zeeguu.core

    db_session = zeeguu.core.model.db.session

    # TR: Get this from the database, rather than the front end.
    # Otherwise, it should be more generic.
    # text_to_pronounce = request.form.get("text", "")
    # language_id = request.form.get("language_id", "")
    article_id = request.form.get("article_id", "")

    print("ID:" + article_id)
    if not article_id:
        return ""

    article = Article.find_by_id(article_id)
    text_to_pronounce = article.content
    language_id = article.language_id

    if (not text_to_pronounce) or (not article_id) or (not language_id):
        return ""

    audio_file_path = _file_name_for_full_article(
        text_to_pronounce, language_id, article_id
    )

    if not os.path.isfile(DATA_FOLDER + audio_file_path):
        _save_speech_to_file(text_to_pronounce, language_id, audio_file_path)

    print(audio_file_path)
    return audio_file_path


def _save_speech_to_file(text_to_speak, language_id, audio_file_path):
    from google.cloud import texttospeech

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text_to_speak)

    # Build the voice request
    voice = texttospeech.VoiceSelectionParams(
        language_code=_code_from_id(language_id), name=voice_for_language(language_id)
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(DATA_FOLDER + audio_file_path, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)


def _file_name_for_user_word(user_word, language_id):
    word_without_special_chars = re.sub("[^A-Za-z0-9]+", "_", user_word.word)
    return f"/speech/{language_id}_{user_word.id}_{word_without_special_chars}.mp3"


def _file_name_for_full_article(full_article_text, language_id, article_id):
    # create md5 hash of the user_word and return it
    import hashlib

    m = hashlib.md5()
    m.update(full_article_text.encode("utf-8"))
    return f"/speech/art_{article_id}_{language_id}_{m.hexdigest()}.mp3"


def _code_from_id(language_id):
    # If they're not here, we assume the xy-XY form
    irregular_language_codes = {
        "da": "da-DK",
        "en": "en-US",
    }
    if irregular_language_codes.get(language_id):
        return irregular_language_codes[language_id]
    return f"{language_id}-{language_id.upper()}"

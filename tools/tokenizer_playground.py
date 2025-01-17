from zeeguu.core.model.language import Language
from zeeguu.core.util.text import tokenize_text_flat_array
from zeeguu.api.app import create_app

from pprint import pprint
import os


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


app = create_app()
app.app_context().push()

while True:
    clear_terminal()
    print("Welcome to the Zeeguu Tokenizer")
    language = Language.find(input("Enter language code (ex. 'en'): ").lower())
    text = input("Enter text: ")

    print("Got the following text: ", text)
    tokens = tokenize_text_flat_array(text, language, False)
    for token in tokens:
        print(token.text)
        pprint(token.as_serializable_dictionary())
        print("####")
    if input("Press 'q' to quit, any other key to continue: ") == "q":
        break

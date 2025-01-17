import zeeguu
from zeeguu.core.model import Bookmark, Article
from zeeguu.api.app import create_app
from tqdm import tqdm
from zeeguu.core.util.text import tokenize_text_flat_array
from time import time


def update_bookmark_pointer(bookmark):
    # Tokenized text returns paragraph, sents, token
    # Since we know there is not multiple paragraphs, we take the first
    text = bookmark.text
    if text:
        if not text.article_id:
            # There is no article id.
            return False
    article = Article.find_by_id(text.article_id)
    if not article:
        return False
    tokenize_article_content = tokenize_text_flat_array(
        article.content, article.language, False
    )
    tokenized_text = tokenize_text_flat_array(
        text.content, bookmark.origin.language, False
    )
    tokenized_bookmark = tokenize_text_flat_array(
        bookmark.origin.word, bookmark.origin.language, False
    )

    # Find the first token of the context
    context_found = False
    context_current_start = None
    for article_token_i in range(len(tokenize_article_content)):
        context_current_start = tokenize_article_content[article_token_i]
        for i in range(len(tokenized_text)):
            if article_token_i + i >= len(tokenize_article_content):
                context_found = False
                break
            candidate_token = tokenize_article_content[article_token_i + i]
            context_token = tokenized_text[i]
            if candidate_token.text == context_token.text:
                context_found = True
            else:
                context_found = False
                break
        if context_found:
            break
    if not context_found:
        return False
    text.paragraph_i = context_current_start.par_i
    text.sentence_i = context_current_start.sent_i
    text.token_i = context_current_start.token_i
    text.in_content = True
    try:
        first_token_ocurrence = next(
            filter(lambda t: t.text == tokenized_bookmark[0].text, tokenized_text)
        )

        bookmark.sentence_i = first_token_ocurrence.sent_i
        bookmark.token_i = first_token_ocurrence.token_i
        bookmark.total_tokens = len(tokenized_bookmark)
    except StopIteration:
        # print(tokenized_text)
        # print(tokenized_bookmark)
        print(f"Couldn't find bookmark {bookmark.id} in text {text.id}.")
        print(f"Bookmark is substring of text: {bookmark.origin.word in text.content}")
        print(
            "------------------------------------------------------------------------"
        )
        return False

    db_session.add(text)
    db_session.add(bookmark)
    return True


app = create_app()
app.app_context().push()

db_session = zeeguu.core.model.db.session


start = time()
all_bookmarks = db_session.query(Bookmark).all()
counter_total_updated_bookmarks = 0
for i, b in tqdm(enumerate(all_bookmarks[::-1]), total=len(all_bookmarks)):
    if update_bookmark_pointer(b):
        counter_total_updated_bookmarks += 1

    if (i + 1) % 1000 == 0:
        print("Completed 1000, saving progress...")
        db_session.commit()

end = time() - start
print(
    f"Total updated bookmarks: {counter_total_updated_bookmarks} out of {len(all_bookmarks)}, time taken: {end:.2f}"
)

import sys
import zeeguu
from zeeguu.core.model import Article

session = zeeguu.core.db.session


def update_article(id):
    a = Article.find_by_id(id)
    print(">>>>>> BEFORE <<<<<<")
    print(a.content)
    a.update_content(session)
    print("\n\n>>>>>> AFTER <<<<<<\n")
    print(a.content)


if __name__ == '__main__':
    id = int(sys.argv[1])
    update_article(id)
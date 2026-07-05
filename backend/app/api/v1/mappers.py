from models.domain import Word

from .schemas import WordAPI


def word_domain_to_api(w: Word) -> WordAPI:
    return WordAPI(
        en=w.en,
        ru=w.ru,
        transcription=w.transcription,
        examples=w.examples,
        in_jar=w.in_jar,
    )

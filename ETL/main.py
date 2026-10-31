import csv
import signal
import time

import bs4
import requests

skipped_words = []

def signal_handler(sig, frame):
    print("Got signal. Exiting...")
    save_skipped_words()
    print("Skipped words have saved")
    exit(0)


def save_skipped_words():
    with open("skipped_words.txt", mode="a", encoding="utf8") as file:
        file.writelines(w+"\n" for w in skipped_words)


def get_next_word():
    try:
        with open('current_row', mode='r', encoding="utf-8") as checkpoint:
            curr_str = checkpoint.read().strip()
            # Проверяем на пустой файл или скрытый мусор
            target_line = int(curr_str) if curr_str.isdigit() else 1
    except FileNotFoundError:
        target_line = 1

    with open('unigram_freq.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for _ in range(target_line - 1):
            next(reader, None)

        for row in reader:
            if int(row['count']) > 200_000:
                yield row['word']
            else:
                raise StopIteration("Word count < 200 000")
            # 3. Перезаписываем чекпоинт: 'w' автоматически очищает файл без багов
            with open('current_row', mode='w', encoding="utf-8") as checkpoint:
                checkpoint.write(str(reader.line_num))


def get_html(w: str) -> bytes | None:
    URL = "https://wooordhunt.ru/word/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://wooordhunt.ru/',
        'Connection': 'keep-alive',
    }

    with requests.get(URL+w, headers=headers) as resp:
        if resp.status_code != 200:
            if resp.status_code != 404:
                print("Status code not 200: ", resp.status_code)
                print("Details: ", resp.content)
            return
        return resp.content



def get_data(html: bytes):
    soup = bs4.BeautifulSoup(html, features="html.parser")

    tr_tag = soup.select_one("span.transcription")
    if tr_tag is None:
        return
    tr = tr_tag.text.strip("| ")

    translations_tag = soup.select_one("div.t_inline_en")
    if translations_tag is None:
        return
    translations = translations_tag.text.split(", ")
    translations = [tr.strip(", ") for tr in translations if tr]

    example_tags = soup.select(".ex_o, .ex_t")
    examples = []
    for t in example_tags:
        ex = t.text.strip("\u2002 ").strip(",")
        examples.append(ex)
        if len(examples) >= 8:
            break

    return {
        "transcription": tr,
        "translations": translations,
        "examples": examples,
    }


class SQLArrayDictWriter(csv.DictWriter):
    def _format_sql_array(self, value):
        if isinstance(value, list):
            formatted_elements = []
            for item in value:
                item_str = str(item)
                if ',' in item_str or ' ' in item_str:
                    item_str = item_str.replace('"', '\\"')
                    formatted_elements.append(f'"{item_str}"')
                else:
                    formatted_elements.append(item_str)
            return f"{{{','.join(formatted_elements)}}}"
        return value

    def _convert_row(self, row):
        return {k: self._format_sql_array(v) for k, v in row.items()}

    def writerow(self, rowdict):
        return super().writerow(self._convert_row(rowdict))

    def writerows(self, rowdicts):
        return super().writerows(self._convert_row(row) for row in rowdicts)
    

def save():
    with open('words.csv', mode='a', newline='', encoding='utf-8') as file:
        wr = SQLArrayDictWriter(file, fieldnames=["word", "translations", "transcription", "examples"])
        while row := (yield):
            wr.writerow(row)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    scrapping_interval = 0.5

    for w in get_next_word():
        try:
            time.sleep(scrapping_interval)
            raw = get_html(w)
            if raw is None:
                # print("Word completely skipped: ", w)
                continue

            data = get_data(raw)
            if data is None:
                # skipped_words.append(w)
                continue
            data["word"] = w

            saver = save()
            next(saver)

            saver.send(data)
        except Exception:
            print("failed to parse word: ", w)
            skipped_words.append(w)
            raise
    try:
        saver.send(None)
    except StopIteration:
            return


if __name__ == "__main__":
    main()

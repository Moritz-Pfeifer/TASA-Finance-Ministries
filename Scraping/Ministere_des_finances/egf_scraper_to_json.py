import os
import re

import fitz
import sqlite3
import json


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn


def get_records_from_db(conn):
    cursor = conn.cursor()
    sql = 'SELECT * FROM main.economie_gouv_fr where extract_to_json = 1 '
    cursor.execute(sql)
    records = cursor.fetchall()
    return records


def parse_records(records, conn, cursor):
    print('Parsing records')
    for record in records:
        id = record[0]
        url = record[1]
        author = record[2]
        title = record[3]
        published_date = record[5]
        section = record[6]
        pdf_filename = re.sub(r'[\\/*?:"<>|]', "_", title)
        if len(pdf_filename) > 251:
            pdf_filename = pdf_filename[:250]
        pdf_filename += '.pdf'
        if not os.path.exists('Json'):
            os.makedirs('Json')
        pdf_text = parse_pdf(pdf_filename,section)
        data_to_json = {'id': id, 'url': url, 'author': author, 'title': title, 'text': pdf_text,
                            'published_date': published_date, 'section': section}
        json_filename = f'egf_{published_date}_{id}.json'
        with open(f'Json/{json_filename}', 'w', encoding='utf8') as json_file:
            json.dump(data_to_json, json_file, ensure_ascii=False)

        sql = f'UPDATE main.economie_gouv_fr SET extract_to_json = 0 where id = {id}'
        cursor.execute(sql)
        conn.commit()


def parse_pdf(file,section):
    try:
        doc = fitz.open(f'{section}/{file}')
    except RuntimeError:
        print(f'No file {file}')
    try:
        text = '\n'.join(page.getText() for page in doc)
    except:
        print(file)
        text = 'ERROR - BAD PDF'
    return text


if __name__ == '__main__':
    conn = create_connection('economie.gouv.fr.db')
    cursor = conn.cursor()

    records = get_records_from_db(conn)
    parse_records(records, conn, cursor)

    conn.close()
    print('*' * 100)
    print('Done')
    print('*' * 100)

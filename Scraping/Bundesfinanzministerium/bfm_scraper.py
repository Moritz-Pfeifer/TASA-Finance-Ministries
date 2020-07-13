import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup as bs
import re
import sqlite3


def get_page(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
    }
    while True:
        try:
            r = requests.get(link, headers=headers, timeout=30)
            return r
        except Exception as exp:
            time.sleep(5)
            print(exp)
            print(link)
            print('Trying request one more time')


def parse_url_list(section, soup_object):
    if section == 'Monatsberichte':
        urls = re.findall(
            r'https:\/\/www\.bundesfinanzministerium\.de\/Monatsberichte\/\d{4}\/\d{2}\/monatsbericht-\d{2}-\d{4}.html',
            soup_object.text)
        print(urls)
    else:
        urls = re.findall(
            fr'https:\/\/www\.bundesfinanzministerium\.de\/Content\/DE\/{section}\/.*?\.html',
            soup_object.text)
    print(f'{str(len(urls))} {section}')
    return urls


def parse_page(link, conn, cursor):
    print(link)
    soup = bs(get_page(link).text, 'lxml')
    try:
        title = soup.select_one('h1.isFirstInSlot').text.replace("\xad", "").strip().replace('"', '').replace('“',
                                                                                                              '').replace(
            '„', '')
    except AttributeError:
        return

    print(title)
    if '/Interviews/' in link:
        section = 'Interview'
    elif '/Reden/' in link:
        section = 'Rede'
    elif '/Pressemitteilungen/' in link:
        section = 'Pressemitteilung'
    else:
        section = None

    try:
        published_date = soup.find(text='Datum').find_next('span').text.strip()
    except AttributeError:
        published_date = soup.select_one('p.date').text.strip()
    published_date = re.findall(r"\d{2}.\d{2}.\d{4}", published_date)[0]
    published_date = datetime.strptime(published_date, '%d.%m.%Y').strftime('%Y-%m-%d')

    try:
        soup.select_one('p.dachzeile').decompose()
    except AttributeError:
        pass
    try:
        soup.select_one('aside.sectionRelated').decompose()
    except AttributeError:
        pass
    try:
        soup.select_one('p.date').decompose()
    except AttributeError:
        pass
    paragraphs = soup.find('div', id="content").select('p')
    text = '\n'.join(list(map(lambda x: x.text, paragraphs))).strip()
    title_lower = title.lower()
    try:
        subtitle_text_lower = soup.find('div', class_="subheadline").text.lower()
    except AttributeError:
        subtitle_text_lower = ''
    if 'oskar lafontaine' in title_lower or 'oskar lafontaine' in subtitle_text_lower:
        author = 'Oskar Lafontaine'
    elif 'werner müller' in title_lower or 'werner müller' in subtitle_text_lower:
        author = 'Werner Müller'
    elif 'hans eichel' in title_lower or 'hans eichel' in subtitle_text_lower:
        author = 'Hans Eichel'
    elif 'peer steinbrück' in title_lower or 'peer steinbrück' in subtitle_text_lower:
        author = 'Peer Steinbrück'
    elif 'wolfgang schäuble' in title_lower or 'wolfgang schäuble' in subtitle_text_lower:
        author = 'Wolfgang Schäuble'
    elif 'peter altmaier' in title_lower or 'peter altmaier' in subtitle_text_lower:
        author = 'Peter Altmaier'
    elif 'olaf scholz' in title_lower or 'olaf scholz' in subtitle_text_lower:
        author = 'Olaf Scholz'
    else:
        author = None
    filetype = 'html'
    write_to_db(conn, cursor, [link, author, title, text, published_date, section, filetype])


def parse_monatsbericht(link, conn, cursor):
    date = re.findall(
        r'\d{4}\/\d{2}',
        link)[0].split('/')
    title = f'BMF-Monatsbericht-{date[0]}-{date[1]}'
    pdf_url = f'https://www.bundesfinanzministerium.de/Monatsberichte/{date[0]}/{date[1]}/Downloads/monatsbericht-{date[0]}-{date[1]}-deutsch.pdf?__blob=publicationFile'
    date = f'{date[0]}-{date[1]}-01'

    author = None
    section = 'Monatsberichte'
    text = None
    filetype = 'pdf'
    filename = title + '.pdf'
    save_monatsbericht_to_file(pdf_url, filename)
    write_to_db(conn, cursor, [pdf_url, author, title, text, date, section, filetype])


def parse_monatsberichte_from_archive(conn, cursor):
    soup = bs(get_page(
        'https://www.bundesfinanzministerium.de/Monatsberichte/2001-2016/Kapitel/kapitel-1-monatsberichte-2001-2016.html').text,
              'lxml')
    pdf_links = list(map(lambda x: 'https://www.bundesfinanzministerium.de' + x.get('href'),
                         soup.select('a.RichTextIntLink.Publication')))
    print(f'{str(len(pdf_links))} Monatsberichte')
    for pdf_link in pdf_links:
        try:
            date = re.findall(r'\d{4}.\d{2}.deutsch', pdf_link)[0].replace('_', '-').split('-')
            year = date[0]
            month = date[1]
        except IndexError:
            date = re.findall(r'-.*-\d{4}.pdf', pdf_link.replace('_', '-'))[0].split('-')
            year = date[-1].replace('.pdf', '')
            month = date[-2]
        month = month.replace('Januar', '01').replace('Februar', '02').replace('September', '09').replace('November',
                                                                                                          '11').replace(
            'Oktober', '10').replace('Dezember', '12').replace('Jan', '01').replace('August', '08').replace('Feb',
                                                                                                            '02').replace(
            'Maerz', '03').replace('April', '04').replace(
            'Mai', '05').replace('Juni', '06').replace('Juli', '07').replace('Aug', '08').replace('Sep', '09').replace(
            'Okt', '10').replace('Nov', '11').replace('Dez', '12')
        title = f'BMF-Monatsbericht-{year}-{month}'
        author = None
        section = 'Monatsberichte'
        text = None
        date = f'{year}-{month}-01'
        filetype = 'pdf'
        filename = title + '.pdf'
        save_monatsbericht_to_file(pdf_link, filename)
        write_to_db(conn, cursor, [pdf_link, author, title, text, date, section, filetype])


def save_monatsbericht_to_file(link, filename):
    if not os.path.exists('Monatsberichte'):
        os.makedirs('Monatsberichte')
    print(f'Downloading {filename}')
    request = get_page(link)
    with open(f'Monatsberichte/{filename}', 'wb') as pdf_file:
        pdf_file.write(request.content)
    print("Done")


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table(conn):
    bundes_fin_table = """ CREATE TABLE IF NOT EXISTS bundes_fin (
                                            id integer PRIMARY KEY,
                                            url varchar(300),
                                            author varchar (200),
                                            title varchar (200),
                                            text text,
                                            published_date date,
                                            section varchar(100),
                                            filetype varchar(20),
                                            extract_to_json INTEGER DEFAULT 0
                                        ); """
    conn.execute(bundes_fin_table)


def write_to_db(conn, cursor, list_to_db):
    sql = 'INSERT INTO bundes_fin(url,author,title,text,published_date,section,filetype) VALUES (?,?,?,?,?,?,?)'
    cursor.execute(sql, (list_to_db))
    conn.commit()


if __name__ == '__main__':
    conn = create_connection('bundesfinanzministerium.db')
    create_table(conn)
    cursor = conn.cursor()

    print('Parsing sitemap')
    soup = bs(get_page('https://www.bundesfinanzministerium.de/sitemap.xml').text, 'lxml')

    interviews = parse_url_list('Interviews', soup)
    reden = parse_url_list('Reden', soup)
    pressemitteilungen = parse_url_list('Pressemitteilungen', soup)

    print('Parsing Interviews')
    for interview in interviews:
        parse_page(interview, conn, cursor)
    print('Done')

    print('Parsing Reden')
    for rede in reden:
        parse_page(rede, conn, cursor)
    print('Done')

    print('Parsing Pressemitteilungen')
    for pressemitteilung in pressemitteilungen:
        parse_page(pressemitteilung, conn, cursor)
    print('Done')

    print('Parsing Monatsberichte')
    monatsberichte = parse_url_list('Monatsberichte', soup)
    for monatsbericht in monatsberichte:
        parse_monatsbericht(monatsbericht, conn, cursor)
    print('Done')
    print('Parsing Monatsberichte from archive')
    parse_monatsberichte_from_archive(conn, cursor)
    print('*' * 100)
    print('Done')
    print('*' * 100)
    conn.close()

import os
import time
import requests
from bs4 import BeautifulSoup as bs
import re
import sqlite3


def get_page(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
    }
    while True:
        try:
            r = requests.get(link, headers=headers, timeout=60).text
            return r
        except Exception as e:
            time.sleep(5)
            print(e)
            print('Trying request one more time')


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table(conn):
    bundes_fin_table = """ CREATE TABLE IF NOT EXISTS economie_gouv_fr (
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
    sql = 'INSERT INTO economie_gouv_fr(url,author,title,text,published_date,section,filetype) VALUES (?,?,?,?,?,?,?)'
    cursor.execute(sql, (list_to_db))
    conn.commit()


def parse_page_with_urls(soup):
    links = soup.find('div', id="block-economie-content").select_one('div.item-list').select('li')
    for link in links:
        date = link.select_one('span.views-field.views-field-created').text.split(' ')
        day = date[0]
        month = date[1].replace('janvier', '01').replace('février', '02').replace('mars', '03').replace('avril',
                                                                                                        '04').replace(
            'mai', '05').replace('juin', '06').replace('juillet', '07').replace('août', '08').replace(
            'septembre', '09').replace('octobre', '10').replace('novembre', '11').replace('décembre', '12')
        year = date[2]
        published_date = '-'.join([year, month, day])

        title = link.select_one('span.views-field.views-field-title').text

        try:
            url = link.find('a').get('href')
        except AttributeError:
            continue
        page_title = soup.title.text
        filetype = 'pdf'
        if 'Discours de presse' in page_title:
            if not os.path.exists('Discours'):
                os.makedirs('Discours')
            folder = 'Discours'
            section = 'Discours'
        if 'Dossiers de presse' in page_title:
            if not os.path.exists('Dossiers'):
                os.makedirs('Dossiers')
            folder = 'Dossiers'
            section = 'Dossiers'
        if 'Communiqués de presse' in page_title:
            if not os.path.exists('Communiques'):
                os.makedirs('Communiques')
            folder = 'Communiques'
            section = 'Communiques'
        if section == 'Communiques' or section == 'Dossiers':
            author = None
        else:
            if 'bruno le maire' in title.lower():
                author = 'Bruno Le Maire'
            elif 'florence parly' in title.lower():
                author = 'Florence Parly'
            elif 'alain lambert' in title.lower():
                author = 'Alain Lambert'
            elif 'axelle lemaire' in title.lower():
                author = 'Axelle Lemaire'
            elif 'dominique bussereau' in title.lower():
                author = 'Dominique Bussereau'
            elif 'jean-françois copé' in title.lower():
                author = 'Jean-François Copé'
            elif 'éric woerth' in title.lower():
                author = 'Éric Woerth'
            elif 'françois baroin' in title.lower():
                author = 'François Baroin'
            elif 'valérie pécresse' in title.lower():
                author = 'Valérie Pécresse'
            elif 'jérôme cahuzac' in title.lower():
                author = 'Jérôme Cahuzac'
            elif 'bernard cazeneuve' in title.lower():
                author = 'Bernard Cazeneuve'
            elif 'gérald darmanin' in title.lower():
                author = 'Gérald Darmanin'
            elif 'olivier dussopt' in title.lower():
                author = 'Olivier Dussopt'
            elif 'dominique strauss-kahn' in title.lower():
                author = 'Dominique Strauss-Kahn'
            elif 'christian sautter' in title.lower():
                author = 'Christian Sautter'
            elif 'laurent fabius' in title.lower():
                author = 'Laurent Fabius'
            elif 'francis mer' in title.lower():
                author = 'Francis Mer'
            elif 'sarkozy' in title.lower():
                author = 'Nicolas Sarkozy'
            elif 'baroin' in title.lower():
                author = 'François Baroin'
            elif 'lagarde' in title.lower():
                author = 'Christine Lagarde'
            elif 'borloo' in title.lower():
                author = 'Jean-Louis Borloo'
            elif 'breton' in title.lower():
                author = 'Thierry Breton'
            elif 'gaymard' in title.lower():
                author = 'Hervé Gaymard'
            elif 'eckert' in title.lower():
                author = 'Christian Eckert'
            elif 'pinville' in title.lower():
                author = 'Martine Pinville'
            elif 'sapin' in title.lower():
                author = 'Michel Sapin'
            elif 'macron' in title.lower():
                author = 'Emmanuel Macron'
            elif 'delga' in title.lower():
                author = 'Carole Delga'
            elif 'moscovici' in title.lower():
                author = 'Pierre Moscovici'
            else:
                author = None
        new_request = requests.get(url)
        filename = re.sub(r'[\\/*?:"<>|]', "_", title)
        if len(filename) > 251:
            filename = filename[:250]
        filename += '.pdf'
        print(f'Downloading {filename}')
        with open(f'{folder}/{filename}', 'wb') as pdf_file:
            pdf_file.write(new_request.content)
        print("Done")
        write_to_db(conn, cursor, [new_request.url, author, title, '', published_date, section, filetype])


def parse_url_list(link):
    soup = bs(get_page(link), 'lxml')
    number_of_pages = soup.select_one('li.pager__item.pager__item--last').find_next('a').get('href').split('=')[-1]
    for i in range(0, int(number_of_pages) + 1):
        print(f'Page number{str(i)}')
        soup = bs(get_page(f'{link}?page={str(i)}'), 'lxml')
        parse_page_with_urls(soup)


def parse_rapports_links(link, conn, cursor):
    soup = bs(get_page(link), 'lxml')
    years_links = soup.find_all('a', role='tab')
    for year_link in years_links:
        year = year_link.text
        published_date = f'{str(year)}-01-01'
        id_ = year_link.get('id').replace('onglet', 'section')
        links = soup.find('div', id=id_).find_all('a')
        for link in links:
            title = link.text
            if link.get('class') == ['pdf']:
                download_rapport_pdf(title, 'https://www.economie.gouv.fr' + link.get('href'), published_date, conn,
                                     cursor)
                continue
            url = link.get('href')
            if '.fr' not in url:
                url = 'https://www.economie.gouv.fr' + url
            try:
                new_request = requests.get(url)
            except requests.exceptions.MissingSchema:
                continue
            except  requests.exceptions.ConnectionError:
                continue
            if new_request.status_code == '404':
                continue
            if '.pdf' in new_request.url:
                download_rapport_pdf(title, new_request.url, published_date, conn, cursor)
                continue
            soup2 = bs(new_request.text, 'lxml')
            try:
                pdf_link = soup2.find('a', href=re.compile('pdf')).get('href')
            except AttributeError:
                try:
                    pdf_link = soup2.find(text=re.compile('pdf')).find_parent('a').get('href')
                except AttributeError:
                    continue
            if '.fr' not in pdf_link:
                pdf_link = 'https://www.economie.gouv.fr' + pdf_link
            download_rapport_pdf(title, pdf_link, published_date, conn, cursor)


def download_rapport_pdf(title, pdf_link, published_date, conn, cursor):
    author = None
    section = 'Rapports'
    filetype = 'pdf'
    try:
        pdf_request = requests.get(pdf_link)
    except requests.exceptions.ConnectionError:
        return
    if pdf_request.status_code == '404':
        return
    if not os.path.exists('Rapports'):
        os.makedirs('Rapports')
    filename = re.sub(r'[\\/*?:"<>|]', "_", title)
    if len(filename) > 251:
        filename = filename[:250]
    filename += '.pdf'
    print(f'Downloading {filename}')
    with open(f'Rapports/{filename}', 'wb') as pdf_file:
        pdf_file.write(pdf_request.content)
    write_to_db(conn, cursor, [pdf_link, author, title, '', published_date, section, filetype])


if __name__ == '__main__':
    conn = create_connection('economie.gouv.fr.db')
    create_table(conn)
    cursor = conn.cursor()
    print('Parsing Communiqués urls')
    parse_url_list('https://www.economie.gouv.fr/presse/communiques')
    print('Parsing Dossiers urls')
    parse_url_list('https://www.economie.gouv.fr/presse/dossiers')
    print('Parsing Discours urls')
    parse_url_list('https://www.economie.gouv.fr/presse/discours')
    print('Parsing Rapports urls')
    parse_rapports_links('https://www.economie.gouv.fr/rapports-activite-ministeres-economiques-financiers', conn,
                         cursor)

    print(100 * '*')
    print('DONE')
    print(100 * '*')

"""
Following Python code shows how to use BeautifulSoup to make webcrawler
which will navigate through Rimi.ee webstore and collect all products of a category
and write them into json file.
"""

import json
import re
import requests
from bs4 import BeautifulSoup


def parse(start_url: str) -> list:
    """
    Webcrawler which collects all products data from a category.

    :param start_url: url of Rimi store category
    :return: list of dictionaries with products data
    """
    page = requests.get(start_url + "?page=1&pageSize=80&query=")
    soup = BeautifulSoup(page.text, 'html.parser')
    links = []
    all_products_data = []
    try:
        num_of_pages = int(soup.find_all("li", class_='pagination__item')[-2].find("a")["data-page"])
        for i in range(1, num_of_pages + 1):
            for product_a in soup.find_all('a', class_='card__url'):
                links.append(product_a['href'])
            page = requests.get(start_url + f"?page={i + 1}&pageSize=80&query=")
            soup = BeautifulSoup(page.text, 'html.parser')
    except IndexError as e:
        for product_a in soup.find_all('a', class_='card__url'):
            links.append(product_a['href'])
    finally:
        for link in links:
            print(link)
            product_data = find_all_parameters(link)
            if product_data:
                all_products_data.append(product_data)
        return all_products_data


def find_all_parameters(href: str):
    """
    Webcrawler which collects all data about a product.

    :param href:
    :return:
    """
    page = requests.get("https://www.rimi.ee" + href)
    soup = BeautifulSoup(page.text, 'html.parser')
    product_name = soup.find('h3', class_='name').text
    product_data = {'Nimi': product_name}

    table = soup.find('div', class_='product__table')
    if table:
        table = table.find('tbody')
        cell_data = []
        for i in table.find_all(['td']):
            cell_data.append(i.text.strip())
        for i in range(0, len(cell_data), 2):
            product_data[cell_data[i]] = cell_data[i+1]
    product_price = soup.find('p', class_='price-per')
    if product_price:
        product_data['Hind'] = product_price.string.strip()
        product_promo_price = soup.find('div', class_='price-wrapper -has-old-price')
        if product_promo_price:
            product_data['Has promo price'] \
                = product_promo_price.find('span').string.strip() + "," + product_promo_price.find(
                'sup').string.strip() + " tk"
    return product_data


def calculate_best_by_param(products: list, param: str, reverse: bool):
    """
    .

    :param reverse:
    :param products:
    :param param:
    :return:
    """
    sorted_products = []
    for i in products:
        if param in i.keys():
            sorted_products.append(i)
    if param == 'energiasisaldus':
        sorted_products = \
            sorted(sorted_products, key=lambda prod: float(re.search(r"\d+ kcal", prod[param]).group()[0: -5]), reverse=reverse)
    elif param == 'Hind':
        sorted_products = \
            sorted(sorted_products, key=lambda prod: float(re.search(r"\d+,\d+", prod[param]).group().replace(',', '.')), reverse=reverse)
    else:
        sorted_products = \
            sorted(sorted_products, key=lambda prod: float(prod[param][0:len(prod[param]) - 2]), reverse=reverse)
    print("\n" + best_string_repr(sorted_products, param))
    return sorted_products


def best_string_repr(sorted_products: list, param: str):
    """
    .

    :param sorted_products:
    :param param:
    :return:
    """
    top = f"Sorted by {param}"
    for i, product in enumerate(sorted_products):
        if i < 30:
            top += f"\n{i+1}. {product['Nimi']} - {product[param]}"
            if param == 'rasvad':
                top += f"\n\t\t{'millest küllastunud rasvhapped'} - {product['millest küllastunud rasvhapped']}"
            elif param == 'süsivesikud':
                top += f"\n\t\t{'millest suhkrud'} - {product['millest suhkrud']}"
            elif param == 'Hind':
                if 'Has promo price' in product.keys():
                    top += f"\n\t\t{'Has promo price'} - {product['Has promo price']}"
    return top


def write_json(start_url: str, json_name: str = ""):
    """
    Method to write json for all products data from a category.

    :param start_url: url of Rimi.ee webstore category
    :return:
    """
    items = parse(start_url)
    with open(f'../docs/data_{json_name}.json', 'w') as f:
        json.dump(items, f, indent=2)


def get_json(json_name: str = ""):
    """
    Method to get json for all products data from a category.

    :return:
    """
    json_data = []
    with open(f'../docs/data_{json_name}.json', 'r') as f:
        json_data = json.load(f)
    return json_data


def calculate_score(data: list, price_bool: bool):
    """
    .

    :param data:
    :param price_bool:
    :return:
    """
    tier_dict = {}
    params = {'energiasisaldus': False, 'rasvad': False, 'süsivesikud': False, 'valgud': True, 'sool': False}
    if price_bool:
        params['Hind'] = False
    for param in params.keys():
        multiplier = 1
        if param == 'energiasisaldus':
            multiplier = 1.2
        elif param == 'valgud':
            multiplier = 1.5
        elif param == 'süsivesikud':
            multiplier = 2.0
        elif param == 'rasvad':
            multiplier = 1.6
        elif param == 'Hind':
            multiplier = 2
        calculated = calculate_best_by_param(data, param, params[param])
        for i, best in enumerate(calculated):
            if best['Nimi'] in tier_dict.keys():
                if i < len(calculated)/4:
                    tier_dict[best['Nimi']] += 2.1 * multiplier
                elif i < len(calculated)/2:
                    tier_dict[best['Nimi']] += 1.8 * multiplier
                elif i < len(calculated) * 3 / 4:
                    tier_dict[best['Nimi']] += 1.4 * multiplier
                else:
                    tier_dict[best['Nimi']] += 1 * multiplier
            else:
                if i < len(calculated)/4:
                    tier_dict[best['Nimi']] = 2.0 * multiplier
                elif i < len(calculated) / 2:
                    tier_dict[best['Nimi']] = 1.7 * multiplier
                elif i < len(calculated) * 3 / 4:
                    tier_dict[best['Nimi']] = 1.3 * multiplier
                else:
                    tier_dict[best['Nimi']] = 1 * multiplier
    tier_list = sorted(tier_dict, key=lambda prod: float(tier_dict[prod]), reverse=True)
    print("\n")
    print("Tier list of hlebushek")
    print("\n")
    for i, name in enumerate(tier_list):
        if i < 30:
            print(f"{i+1}. {name} - {tier_dict[name]}")


if __name__ == '__main__':
    write_json('https://www.rimi.ee/epood/ee/tooted/puuviljad%2C-k%C3%B6%C3%B6giviljad%2C-lilled/juurviljad-ja-k%C3%B6%C3%B6giviljad/c/SH-12-1', '1jkviljad')
    # write_json('https://www.rimi.ee/epood/ee/tooted/puuviljad%2C-k%C3%B6%C3%B6giviljad%2C-lilled/rohelised-salatid/c/SH-12-6', '2rohsalat')
    # write_json('https://www.rimi.ee/epood/ee/tooted/toidukaubad/helbed%2C-hommikus%C3%B6%C3%B6gihelbed%2C-m%C3%BCsli/c/SH-13-2', '3helbed')
    # write_json('https://www.rimi.ee/epood/ee/tooted/leivad%2C-saiad%2C-kondiitritooted/leivad%2C-saiad%2C-sepikud/c/SH-6-3', '4leibsai')
    # write_json('https://www.rimi.ee/epood/ee/tooted/piimatooted%2C-munad%2C-juustud/juust/c/SH-11-3', '5juust')
    # write_json('https://www.rimi.ee/epood/ee/tooted/piimatooted%2C-munad%2C-juustud/piimad/c/SH-11-8', '6piim')
    # write_json('https://www.rimi.ee/epood/ee/tooted/liha--ja-kalatooted/vorstid%2C-singid%2C-peekon/c/SH-8-11', '7vorstsink')
    # write_json('https://www.rimi.ee/epood/ee/tooted/liha--ja-kalatooted/vorstid%2C-singid%2C-peekon/c/SH-8-11', '8maitseained')
    # write_json('https://www.rimi.ee/epood/ee/tooted/liha--ja-kalatooted/muud-lihatooted/c/SH-8-12', '9muuliha')
    # write_json('https://www.rimi.ee/epood/ee/tooted/liha--ja-kalatooted/grill--ja-verivorstid%2C-eelk%C3%BCpsetatud-lihatooted/c/SH-8-1', '10grillliha')
    # write_json('https://www.rimi.ee/epood/ee/tooted/toidukaubad/kastmed%2C-ket%C5%A1upid%2C-sinep-ja-m%C3%A4dar%C3%B5igas/c/SH-13-6', '11kaste')
    # write_json('https://www.rimi.ee/epood/ee/tooted/joogid/mahl-ja-siirup/c/SH-3-8', '12mahljasiirup')
    # write_json('https://www.rimi.ee/epood/ee/tooted/majapidamiskaubad/grilltarvikud/c/SH-15-3', '13grilltarbikud')
    # write_json('https://www.rimi.ee/epood/ee/tooted/majapidamiskaubad/puhastusvahendid/c/SH-10-18', '14puhastus')
    # write_json('https://www.rimi.ee/epood/ee/tooted/alkohol/%C3%B5lu/c/SH-1-6', '15õlu')
    # write_json('https://www.rimi.ee/epood/ee/tooted/vegantooted/c/SH-17', '16vegan')

    # data = get_json("4leibsai")
    # calculate_score(data, True)

    print("\n+++++++++++++++++++++++++++++++++++\nScroll up to get other sorted lists")




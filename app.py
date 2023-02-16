from flask import Flask, request, jsonify, render_template
from flask_cors import cross_origin, CORS
import multiprocessing as mp
from bs4 import BeautifulSoup as BS
import requests as R
import json
import time, os

app = Flask(__name__)
CORS(app)



def get_query(baseurl: str) -> str:

    '''Getting the Query in the search field.'''
    
    if request.method == 'GET':
        query = request.args['query']
    elif request.method == 'POST':
        query = request.json['query']

    return baseurl + query
    


def get_response(url: str):
    try:
        response = R.get(url)
    except ConnectionError:
        return 'Invalid URL'
    
    return response.text

def html_parser(markup: str):
    return BS(markup, 'html.parser')

def html_tag_finder(html_parsed: object, tag_name: str, identifier: dict):
    return html_parsed.findAll(tag_name, identifier)

def extract_links(tags: 'list[str]', baseurl: str, tag_identifier: str):
    return [baseurl + tag[tag_identifier] for tag in tags]

def get_reviews(url: str):
    data = []
    
    page = get_response(url)
    parsed_page = html_parser(page)
    product_name = html_tag_finder(parsed_page, 'span', {'class':'B_NuCI'})
    comments = html_tag_finder(parsed_page, 'div', {'class': '_16PBlm'})


    for comment in comments:
        
        name = html_tag_finder(comment, 'p', {'class': '_2sc7ZR _2V5EHH'})
        rating = html_tag_finder(comment, 'div', {'class': '_3LWZlK _1BLPMq'})
        heading = html_tag_finder(comment, 'p', {'class': '_2-N8zT'})
        description = html_tag_finder(comment, 'div', {'class': 't-ZTKy'})

        try:
            data.append({
                'product' : product_name[0].text, 
                'name' : name[0].text,
                'rating' : rating[0].text,
                'heading' : heading[0].text,
                'comment' : description[0].div.div.text
                })
        except:
            pass

    with open(str(time.time_ns())+'.json', 'w') as file:
        json.dump(data, file)


def all_reviews():
    result = []
    for file in os.listdir('./'):
        if file.endswith('.json'):
            with open(file) as f:
                data = json.load(f)
            os.remove(file)
            result.extend(data)
    
    with open('./result.json', 'w') as file:
        json.dump(result, file)
    return result


@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/review', methods = ['GET', 'POST'])
@cross_origin()
def reviews():
    query = get_query(baseurl = 'https://www.flipkart.com/search?q=')
    page = get_response(query)
    parsed_page = html_parser(page)


    boxes = html_tag_finder(parsed_page, 'a', {'class': "_1fQZEK"})
    product_links = extract_links(boxes, 'https://www.flipkart.com', 'href')

    with mp.Pool() as pool:
        pool.map(get_reviews, product_links)
    
    result = all_reviews()

    if request.method == 'GET':
        return render_template('result.html', reviews = result)
    elif request.method == 'POST':
        return jsonify(json.dumps(result))
        


        











if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 8000, debug = True)
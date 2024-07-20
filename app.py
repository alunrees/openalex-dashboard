from flask import Flask, request, render_template, send_file, jsonify
import requests
import pandas as pd
import os
from functools import lru_cache
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def get_countries():
    base_url = "https://api.openalex.org/institutions"
    params = {
        'group_by': 'country_code',
        'per-page': 200  # Adjust if needed
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        countries = []
        for result in data['group_by']:
            country_code = result['key'][-2:]
            country_name = result.get('key_display_name', country_code)  # Default to country code if name is not available
            count = result['count']
            countries.append({'code': country_code, 'name': country_name, 'count': count})
        return countries
    return []

def get_publications_by_country(country_code, max_results):
    base_url = 'https://api.openalex.org/works'
    params = {
        'filter': f'institutions.country_code:{country_code}',
        'per_page': 200
    }
    all_publications = []
    page = 1

    while len(all_publications) < max_results:
        params['page'] = page
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            break
        data = response.json()
        works = data.get('results', [])
        if not works:
            break
        all_publications.extend(works)
        page += 1
        if len(works) < params['per_page']:
            break

    return all_publications[:max_results]


def get_institutions_by_country(country_code):
    base_url = "https://api.openalex.org/institutions"
    params = {
        'filter': f'country_code:{country_code}',
        'per-page': 200  # Adjust if needed
    }

    institutions = []
    next_page = base_url

    while next_page:
        response = requests.get(next_page, params=params)
        if response.status_code != 200:
            break

        data = response.json()
        institutions.extend(data['results'])

        next_page = data['meta']['next_page'] if 'meta' in data and 'next_page' in data['meta'] else None
        params = None  # Only include params on the first request

    return [{'name': inst['display_name'], 'count': inst['works_count']} for inst in institutions]

def get_institution_id(institution_name):
    base_url = "https://api.openalex.org/institutions"
    params = {
        'filter': f'display_name.search:{institution_name}'
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]['id']
    return None

def get_fields_of_study():
    base_url = 'https://api.openalex.org/concepts'
    params = {'filter': 'level:2', 'per_page': 100}
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    return [{'id': concept['id'], 'name': concept['display_name']} for concept in data['results']]

def fetch_fields_of_study(level):
    base_url = 'https://api.openalex.org/concepts'
    params = {'filter': f'level:{level}', 'per_page': 100}
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    concepts = []
    for concept in data['results']:
        concept_id = concept['id'].split('/')[-1]
        publication_count = concept.get('works_count', 0)
        concepts.append({
            'id': concept_id,
            'name': concept['display_name'],
            'publication_count': publication_count
        })
    return concepts

@cache.cached(timeout=300, query_string=True)
def fetch_level_0_concepts():
    base_url = 'https://api.openalex.org/concepts'
    params = {
        'filter': 'level:0',
        'per_page': 50
    }

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print("Error fetching data:", response.status_code, response.text)
        return []
    
    data = response.json()
    concepts = []
    for concept in data['results']:
        concept_id = concept['id'].split('/')[-1]
        publication_count = concept.get('works_count', 0)
        concepts.append({
            'id': concept_id,
            'name': concept['display_name'],
            'publication_count': publication_count
        })
    return concepts

def fetch_concept_counts():
    concept_counts = {}
    for level in range(5):
        base_url = 'https://api.openalex.org/concepts'
        params = {'filter': f'level:{level}', 'per_page': 1}
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            concept_counts[level] = 0
        else:
            data = response.json()
            concept_counts[level] = data['meta']['count']
    return concept_counts

def fetch_concepts_by_parent(parent_id, level, page=1):
    base_url = 'https://api.openalex.org/concepts'
    params = {
        'filter': f'level:{level}',
        'page': page,
        'per_page': 50  # Limit to 50 results per request
    }
    if parent_id:
        params['filter'] += f',ancestors.id:{parent_id}'

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print("Error fetching data:", response.status_code, response.text)
        return []
    
    data = response.json()
    concepts = []
    for concept in data['results']:
        concept_id = concept['id'].split('/')[-1]
        publication_count = concept.get('works_count', 0)
        concepts.append({
            'id': concept_id,
            'name': concept['display_name'],
            'publication_count': publication_count
        })
    return concepts



def get_institutions():
    base_url = 'https://api.openalex.org/institutions'
    params = {'per_page': 100}
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    return [{'id': institution['id'], 'name': institution['display_name']} for institution in data['results']]

def get_institution_details(institution_id):
    response = requests.get(f'https://api.openalex.org/institutions/{institution_id}')
    if response.status_code != 200:
        return None
    data = response.json()
    return {
        'name': data['display_name'],
        'location': data.get('location', {}).get('country', 'N/A'),
        'total_publications': data['works_count'],
        'total_citations': data['cited_by_count']
    }

def get_publications_by_field(field_id, max_publications):
    base_url = 'https://api.openalex.org/works'
    params = {
        'filter': f'concepts.id:{field_id}',
        'per_page': max_publications
    }

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print("Error fetching data:", response.status_code, response.text)
        return []

    data = response.json()
    return data['results']

def get_publications_by_institution(institution_id, max_results):
    base_url = 'https://api.openalex.org/works'
    params = {
        'filter': f'institutions.id:{institution_id}',
        'per_page': 200
    }
    all_publications = []
    page = 1

    while len(all_publications) < max_results:
        params['page'] = page
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            break
        data = response.json()
        works = data.get('results', [])
        if not works:
            break
        all_publications.extend(works)
        page += 1
        if len(works) < params['per_page']:
            break

    return all_publications[:max_results]


def get_publications(institution_id, max_publications):
    base_url = "https://api.openalex.org/works"
    params = {
        'filter': f'institutions.id:{institution_id}',
        'per-page': 200,
        'page': 1
    }

    publications = []
    while len(publications) < max_publications:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            break

        data = response.json()
        publications.extend(data['results'])

        if len(data['results']) < 200:  # No more pages
            break

        params['page'] += 1

    return publications[:max_publications]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search_by_institution', methods=['GET', 'POST'])
def search_by_institution():
    countries = get_countries()
    if request.method == 'POST':
        print('POST request triggered')
        print('Form data:', request.form)
        institution_name = request.form.get('institution_name')
        if not institution_name:
            return render_template('search_by_institution.html', error="Institution not found.", countries=countries)

        max_publications = int(request.form['max_publications'])
        selected_columns = request.form.getlist('columns')
        institution_id = get_institution_id(institution_name)
        if not institution_id:
            return render_template('search_by_institution.html', error="Institution not found.", countries=countries)
        
        publications = get_publications(institution_id, max_publications)
        publications_data = []

        for publication in publications:
            authors = [author.get('author', {}).get('display_name', 'N/A') for author in publication.get('authorships', [])]
            publication_info = {
                'Title': publication.get('display_name', 'N/A'),
                'DOI': publication.get('doi', 'N/A'),
                'Publication Date': publication.get('publication_date', 'N/A'),
                'Cited by Count': publication.get('cited_by_count', 0),
                'Authors': ", ".join(authors),
                'Abstract': publication.get('abstract', 'N/A'),
                'Venue': publication.get('host_venue', {}).get('display_name', 'N/A'),
                'Type': publication.get('type', 'N/A'),
                'Open Access': publication.get('open_access', {}).get('is_oa', 'N/A'),
                'Volume': publication.get('host_venue', {}).get('volume', 'N/A'),
                'Issue': publication.get('host_venue', {}).get('issue', 'N/A'),
                'Pages': publication.get('biblio', {}).get('pages', 'N/A'),
                'Publisher': publication.get('host_venue', {}).get('publisher', 'N/A'),
                'Language': publication.get('language', 'N/A'),
                'References Count': publication.get('referenced_works_count', 0),
                'Is Retracted': publication.get('is_retracted', 'N/A'),
                'Is Paratext': publication.get('is_paratext', 'N/A'),
                'Source URL': publication.get('host_venue', {}).get('url', 'N/A'),
                'License': publication.get('license', 'N/A')
            }
            filtered_publication_info = {key: publication_info[key] for key in selected_columns}
            publications_data.append(filtered_publication_info)

        df = pd.DataFrame(publications_data)
        sanitized_institution_name = institution_name.replace(" ", "_").lower()
        csv_path = f'{sanitized_institution_name}_{max_publications}_publications.csv'
        df.to_csv(csv_path, index=False)

        return render_template('search_by_institution.html', tables=[df.to_html(classes='data', header="true")], csv_path=csv_path, countries=countries)

    print('GET request')
    return render_template('search_by_institution.html', countries=countries)


@app.route('/get_institutions', methods=['GET'])
def get_institutions():
    country_code = request.args.get('country_code')
    if country_code:
        institutions = get_institutions_by_country(country_code)
        return jsonify(institutions)
    return jsonify([])

@app.route('/download')
def download_file():
    csv_path = request.args.get('csv_path')
    if csv_path and os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True)
    return "File not found.", 404

@app.route('/search_by_country', methods=['GET', 'POST'])
def search_by_country():
    countries = get_countries()
    if request.method == 'POST':
        country_code = request.form.get('country')
        max_publications = int(request.form['max_publications'])
        selected_columns = request.form.getlist('columns')

        # Fetch publications for the selected country
        publications = get_publications_by_country(country_code, max_publications)
        publications_data = []

        for publication in publications:
            authors = [author.get('author', {}).get('display_name', 'N/A') for author in publication.get('authorships', [])]
            publication_info = {
                'Title': publication.get('display_name', 'N/A'),
                'DOI': publication.get('doi', 'N/A'),
                'Publication Date': publication.get('publication_date', 'N/A'),
                'Cited by Count': publication.get('cited_by_count', 0),
                'Authors': ", ".join(authors),
                'Abstract': publication.get('abstract', 'N/A'),
                'Venue': publication.get('host_venue', {}).get('display_name', 'N/A'),
                'Type': publication.get('type', 'N/A'),
                'Open Access': publication.get('open_access', {}).get('is_oa', 'N/A'),
                'Volume': publication.get('host_venue', {}).get('volume', 'N/A'),
                'Issue': publication.get('host_venue', {}).get('issue', 'N/A'),
                'Pages': publication.get('biblio', {}).get('pages', 'N/A'),
                'Publisher': publication.get('host_venue', {}).get('publisher', 'N/A'),
                'Language': publication.get('language', 'N/A'),
                'References Count': publication.get('referenced_works_count', 0),
                'Is Retracted': publication.get('is_retracted', 'N/A'),
                'Is Paratext': publication.get('is_paratext', 'N/A'),
                'Source URL': publication.get('host_venue', {}).get('url', 'N/A'),
                'License': publication.get('license', 'N/A')
            }
            filtered_publication_info = {key: publication_info[key] for key in selected_columns}
            publications_data.append(filtered_publication_info)

        df = pd.DataFrame(publications_data)
        sanitized_country_code = country_code.replace(" ", "_").lower()
        csv_path = f'{sanitized_country_code}_{max_publications}_publications.csv'
        df.to_csv(csv_path, index=False)

        return render_template('search_by_country.html', tables=[df.to_html(classes='data', header="true")], csv_path=csv_path, countries=countries)

    return render_template('search_by_country.html', countries=countries)

@app.route('/get_fields_of_study', methods=['GET'])
def get_fields_of_study():
    level = request.args.get('level')
    fields = fetch_fields_of_study(level)
    return jsonify(fields)



@app.route('/search_by_field', methods=['GET', 'POST'])
def search_by_field():
    level_0_concepts = fetch_level_0_concepts()
    if request.method == 'POST':
        field_id = request.form.get('field')
        max_publications = int(request.form['max_publications'])
        selected_columns = request.form.getlist('columns')

        # Fetch publications for the selected field of study
        publications = get_publications_by_field(field_id, max_publications)
        publications_data = []

        for publication in publications:
            authors = [author.get('author', {}).get('display_name', 'N/A') for author in publication.get('authorships', [])]
            publication_info = {
                'Title': publication.get('display_name', 'N/A'),
                'DOI': publication.get('doi', 'N/A'),
                'Publication Date': publication.get('publication_date', 'N/A'),
                'Cited by Count': publication.get('cited_by_count', 0),
                'Authors': ", ".join(authors),
                'Abstract': publication.get('abstract', 'N/A'),
                'Venue': publication.get('host_venue', {}).get('display_name', 'N/A'),
                'Type': publication.get('type', 'N/A'),
                'Open Access': publication.get('open_access', {}).get('is_oa', 'N/A'),
                'Volume': publication.get('host_venue', {}).get('volume', 'N/A'),
                'Issue': publication.get('host_venue', {}).get('issue', 'N/A'),
                'Pages': publication.get('biblio', {}).get('pages', 'N/A'),
                'Publisher': publication.get('host_venue', {}).get('publisher', 'N/A'),
                'Language': publication.get('language', 'N/A'),
                'References Count': publication.get('referenced_works_count', 0),
                'Is Retracted': publication.get('is_retracted', 'N/A'),
                'Is Paratext': publication.get('is_paratext', 'N/A'),
                'Source URL': publication.get('host_venue', {}).get('url', 'N/A'),
                'License': publication.get('license', 'N/A')
            }
            filtered_publication_info = {key: publication_info[key] for key in selected_columns}
            publications_data.append(filtered_publication_info)

        df = pd.DataFrame(publications_data)
        sanitized_field_id = field_id.replace(" ", "_").lower()
        csv_path = f'{sanitized_field_id}_{max_publications}_publications.csv'
        df.to_csv(csv_path, index=False)

        return render_template('search_by_field.html', tables=[df.to_html(classes='data', header="true")], csv_path=csv_path, level_0_concepts=level_0_concepts)

    return render_template('search_by_field.html', level_0_concepts=level_0_concepts)




@app.route('/get_concepts_by_parent', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_concepts_by_parent():
    parent_id = request.args.get('parent_id')
    level = request.args.get('level')
    page = request.args.get('page', 1, type=int)
    concepts = fetch_concepts_by_parent(parent_id, level, page)
    return jsonify(concepts)

@app.route('/institution_details', methods=['GET'])
def institution_details():
    institutions = get_institutions()  # Implement this function to fetch all institutions
    return render_template('institution_details.html', institutions=institutions)


@app.route('/institution_details/<institution_id>', methods=['GET'])
def institution_details_page(institution_id):
    institution = get_institution_details(institution_id)  # Implement this function to fetch institution details
    publications = get_publications_by_institution(institution_id, 100)  # Fetch latest 100 publications
    return render_template('institution_details_page.html', institution=institution, publications=publications)


if __name__ == '__main__':
    app.run(debug=True)

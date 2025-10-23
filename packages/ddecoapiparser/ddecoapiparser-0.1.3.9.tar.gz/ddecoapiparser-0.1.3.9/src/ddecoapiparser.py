"""
ddecoapidataparser script to request data from the DD-ECO-API
"""
import pandas as pd
import numpy as np
import requests

"""
File: ddecoapidataparser.py
Author: Wouter Abels (wouter.abels@rws.nl)
Created: 16/06/21
Last modified: 24/07/2023
Python ver: 3.11.4
"""

api_url = 'https://ddecoapi.aquadesk.nl/v2/'

def http_error_check(
    e: requests.status_codes) -> bool:
    """Function to check HTTP error from API

    Args:q
        e (requests.status_codes, optional): HTTP error from API. Defaults to None

    Returns:
        bool: True for break in while loop.
    """
    if e.response.status_codes == 403:
        print('Invalid api key')
        return True
    else:
        print(f'Error: {e.reason}')
        return True

def url_builder(query_url: str,
                query_filter: str = None,
                skip_properties: str = None,
                page_number: int = 1,
                page_size: int = 10000) -> str:
    """Builds query url for every page with defined endpoint, filters and skip properties

    Args:
        query_url (str): API endpoint for query
        query_filter (str, optional): Filtering within API. Defaults to None.
        skip_properties (str, optional): Properties to skip in response. Defaults to None.
        page_number (int, optional): Starting page number. Defaults to 1.
        page_size (int, optional): Default max page size. Defaults to 10000.

    Returns:
        str: base
    """
    base = f'{api_url+query_url}?page={page_number}&pagesize={page_size}'
    if query_filter != None:
        base = f'{base}&filter={query_filter}'
    if skip_properties !=None:
        base = f'{base}&skipproperties={skip_properties}'
    base = base.replace(" ", "%20")
    return base


def check_ending(response: list) -> bool:
    """Check if ending of the response pages is reached (When response paging next is an empty string, thus more data is available on the next page)

    Args:
        response (list,optional: Response list from query. Defaults to None.
    Returns:
        bool: True if response paging next is not an empty string.
    """
    if not response['paging']['next']:
        print('Finished!')
        return True
    else:
        return False

def return_query(query_url: str,
                    query_filter: str = None,
                    skip_properties: str = None,
                    api_key: str = None,
                    page: int = 1,
                    page_size: int = 10000) -> list:
    """Returns query from api, for testing and discovery purposes, Returns json result.

    Args:
        query_url (str): API endpoint for query
        query_filter (str, optional): Filtering within API. Defaults to None.
        skip_properties (str, optional): Properties to skip in response. Defaults to None.
        api_key (str, optional): API key for identification as company. Defaults to None.
        page (int, optional): Starting page number. Defaults to 1.
        page_size (int, optional): Default max page size. Defaults to 10000.

    Returns:
        list: query URL for testing purpose
    """
            
    request_url = url_builder(
        query_url, query_filter, skip_properties, page, page_size)
    try:
        request = requests.get(
            request_url, headers={"Accept": "application/json", "x-api-key": api_key})
        return request.url 
    except requests.HTTPError as e:
        http_error_check(e)
        return e

                    
def parse_data_dump(query_url: str ,
                    api_key: str = None,
                    query_filter: str = None,
                    skip_properties: str = None,
                    page: int = 1,
                    page_size: int = 10000,
                    parse_watertypes=False):
    """Parse through all pages and send to path file location as csv.


    Args:
        query_url (str): API endpoint for query
        api_key (str, optional): API key for identification as company. Defaults to None.
        query_filter (str, optional): Filtering within API. Defaults to None.
        skip_properties (str, optional): Properties to skip in response. Defaults to None.
        page (int, optional): Starting page number. Defaults to 1.
        page_size (int, optional): Default max page size. Defaults to 10000.
        parse_watertypes (list, optional): Used to parse watertypes column into split columns. Defaults to False.

    Returns:
        pd.DataFrame: DataFrame containing all the requested data including multiple pages
    """

    json_request_list = []

    while True:
        request_url = url_builder(
            query_url, query_filter, skip_properties, page, page_size)
        try:
            request = requests.get(
                request_url, headers={"Accept": "application/json", "x-api-key": api_key}).json()
            response = request['result']
            json_request_list.extend(response)
            print(f'Gathering data from the DD-ECO-API, currently on page: {page}...')
            if check_ending(request):
                return return_dataframe(json_request_list, parse_watertypes)
            page += 1

        except requests.HTTPError as e:
            if http_error_check(e):
                print(e)
                return e
        
        except KeyError as k:
            print('The following error occured: ')
            return print(request['errors'])


def return_dataframe(json_object: list,
                        parse_watertypes: bool) -> pd.DataFrame:
    """Returns dataframe and parses watertypes column if it is in the set.

    Args:
        json_object (list): Json object from aquadesk API
        parse_watertypes (bool): Selected watertypes

    Returns:
        pd.DataFrame: Pandas Dataframe of query
    """
    df=pd.json_normalize(json_object)
    if ("watertypes" in df.columns) & (parse_watertypes == True):
        watertypes_nan_dict = {'classificationsystem': np.nan, 'watertypecode': np.nan}
        return pd.concat([df.drop("watertypes", axis=1),
                            pd.json_normalize(df["watertypes"].apply(lambda x: x[0] if isinstance(x, list) else watertypes_nan_dict))], axis=1)
    elif df.empty:
        return 'No data has been retrieved, try again with different filter criteria.'
    else:
        return df
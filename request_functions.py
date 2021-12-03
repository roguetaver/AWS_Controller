import requests
import logging


# =====================================================================================================================
# FUNCTIONS
# =====================================================================================================================


def post(url, title, date, description):
    response = requests.post(
        url,
        data={
            "title": title,
            "pub_date": date,
            "description": description
        }
    )
    print(response)
    return response.json()

# =====================================================================================================================


def get(url):
    response = requests.get(url)
    print(response)
    return response.json()

# =====================================================================================================================

# LOGGING
# =====================================================================================================================


logging.basicConfig(filename='log_file.txt', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

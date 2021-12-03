import requests


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

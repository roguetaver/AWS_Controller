from request_functions import *
from datetime import datetime


# =====================================================================================================================
# INPUTS
# =====================================================================================================================


print("-------------------------------------------------------------")
request = input("type 1-> get or 2 -> post: ")
print("-------------------------------------------------------------")

# get
if request == "1":
    print("-------------------------------------------------------------")
    url = input("type url: ")
    print("-------------------------------------------------------------")
    print(get(url))

# post
if request == "2":
    now = datetime.now()
    actual_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    print("-------------------------------------------------------------")
    url = input("type the url: ")
    print("-------------------------------------------------------------")
    title = input("type the title: ")
    print("-------------------------------------------------------------")
    description = input("type the description ")
    print("-------------------------------------------------------------")
    print(post(url, title, actual_time, description))
    print("-------------------------------------------------------------")

# =====================================================================================================================

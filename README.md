# Cert_Fetcher
Fetch certificates from [crt.sh](https://crt.sh/) and [Facebook Certificate Transparency](https://developers.facebook.com/tools/ct/)

# dependency
- Python 3.x
- [requests](https://requests.readthedocs.io/en/master/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [lxml](https://lxml.de/)
- [dateutil](https://pypi.org/project/python-dateutil/)

# Usage
Before running any script, please install requirement.txt first by using
```
pip install -r requirements.txt
```
or
```
pip3 install -r requrements.txt
```

## crtsh_fetcher.py
```
python3 crtsh_fetcher.py -d <domain-name> -s <path-for-saving-the-certs>
```
For example, if I'd like to retrieve certificates of domain **snote.online** and stored it to my current directory **./**, just simply type
```
python3 crtsh_fetcher.py -d snote.online -s .
```
or if you don't want to save the certs locally, just ignore the -s parameter
```
python3 crtsh_fetcher.py -d snote.online
```

## Facebook_fetcher.py
```
python3 Facebook_fetcher.py -d <domain-name> -s <path-for-saving-the-certs>
```
For example, if I'd like to retrieve certificates of domain **snote.online** and stored it to my current directory **./**, just simply type
```
python3 Facebook_fetcher.py -d snote.online -s .
```
or if you don't want to save the certs locally, just ignore the -s parameter
```
python3 Facebook_fetcher.py -d snote.online
```

## TODO
- Multithread
- Header Pool to avoid being locked

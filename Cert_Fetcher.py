import requests
import json
import argparse
import os
import lxml
import datetime
import crtsh_fetcher
import Facebook_fetcher

from bs4 import BeautifulSoup
from dateutil.parser import parse

def main():
    parser = argparse.ArgumentParser(description="Arg parser for running this crawler")
    parser.add_argument('-d', dest='domain', action='store', help="domain name")
    parser.add_argument('-s', dest='save', action='store', help='destination directory for saving the certificates')
    
    args = parser.parse_args()
    cralwer = crtsh_fetcher()
    certs = []
    certs_detail = {}

if __name__ == "__main__":
    main()
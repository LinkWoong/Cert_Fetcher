import requests
import json
import argparse
import os
import lxml
import datetime

from crtsh_fetcher import crtsh_fetcher
from crtsh_fetcher import datetime_handler
from Facebook_fetcher import Facebook_fetcher

from bs4 import BeautifulSoup
from dateutil.parser import parse

def main():
    parser = argparse.ArgumentParser(description="Arg parser for running this crawler")
    parser.add_argument('-d', dest='domain', action='store', help="domain name")
    parser.add_argument('-s', dest='save', action='store', help='destination directory for saving the certificates')
    
    args = parser.parse_args()
    crtsh_client = crtsh_fetcher(args.domain, True, True)
    # facebook_client = Facebook_fetcher()
    
    crtsh_certs = []
    crtsh_sha256 = []
    crtsh_cert_details = {}
    
    try:
        if args.domain:
            crtsh_certs = crtsh_client.retrieve_cert(args.domain, True, True)
            print("########### crt.sh #############")
            print("Before dedup contains %d" % len(crtsh_certs))
            crtsh_unique_cert_id = crtsh_client.dedup(crtsh_certs)
            print("After dedup contains %d" % len(crtsh_unique_cert_id))
            
            for id in crtsh_unique_cert_id:
                crtsh_cert_details[id] = crtsh_client.get_cert_detail(id)
                crtsh_sha256.append(crtsh_cert_details[id]["sha256"])
            
            
                
        if args.save:
            if crtsh_certs is None or len(crtsh_cert_details) == 0:
                print("Current result is empty")
            elif not os.path.exists(args.save):
                os.mkdir(args.save)
                with open(os.path.join(args.save, "/crtsh_certs.json"), "w", encoding="utf-8") as f:
                    json.dump(crtsh_cert_details, f, ensure_ascii=False, indent=4)
            else:
                with open(args.save + "/crtsh_certs.json", "w", encoding="utf-8") as f:
                    json.dump(crtsh_cert_details, f, ensure_ascii=False, indent=4, default=datetime_handler)
    except ValueError:
        print("Argument value error!")

if __name__ == "__main__":
    main()
import requests
import json
import argparse
import os
import lxml
import datetime
import threading

from crtsh_fetcher import crtsh_fetcher
from crtsh_fetcher import datetime_handler
from Facebook_fetcher import Facebook_fetcher
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from bs4 import BeautifulSoup
from dateutil.parser import parse

def main():
    parser = argparse.ArgumentParser(description="Arg parser for running this crawler")
    parser.add_argument('-d', dest='domain', action='store', help="domain name")
    parser.add_argument('-s', dest='save', action='store', help='destination directory for saving the certificates')
    
    args = parser.parse_args()
    crtsh_client = crtsh_fetcher(args.domain, True, True)
    facebook_client = Facebook_fetcher(args.domain, True, True)
    
    lock = threading.Lock()
    
    crtsh_certs = []
    crtsh_sha256 = {}
    crtsh_cert_details = {}
    
    facebook_certs = []
    facebook_sha256 = {}
    facebook_cert_details = {}
    
    try:
        if args.domain:
            
            crtsh_certs = crtsh_client.retrieve_cert(args.domain, True, True)
            
            print("########### crt.sh #############")
            crtsh_unique_cert_id = crtsh_client.dedup(crtsh_certs)
            print("After dedup crt.sh contains %d" % len(crtsh_unique_cert_id))
            count = 1
            
            """ Multithreading, didn't work. GET still takes 2+ seconds, website still throttling
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for id in crtsh_unique_cert_id:
                    print("Processing %d / %d" % (count, len(crtsh_unique_cert_id)))
                    # print("Retrieving %d " % id)
                    futures.append(executor.submit(crtsh_client.get_cert_detail, id))
                    # crtsh_cert_details[id] = executor.submit(crtsh_client.get_cert_detail, id)
                for future in as_completed(futures):
                    try:
                        crtsh_cert_details[id] = future.result()
                    except requests.ConnectTimeout:
                        print("Connection time out") 
            """
            
            # persist each certificate to the directory specified by args.save
            # crt.sh
            
            for id in crtsh_unique_cert_id:
                print("Processing %d / %d" % (count, len(crtsh_unique_cert_id)))
                count += 1
                current = crtsh_client.get_cert_detail(id)
                crtsh_cert_details[id] = current
                if args.save:
                    if os.path.exists("./crtsh_certs.json"):
                        with open("./crtsh_certs.json") as f:
                            data = json.load(f)
                            
                        data.update({id: current})
                        
                        with open("./crtsh_certs.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4, default=datetime_handler)
                    else:
                        with open("./crtsh_certs.json", "w", encoding="utf-8") as f:
                            json.dump(crtsh_cert_details, f, ensure_ascii=False, indent=4, default=datetime_handler)
                # if count == 5:
                    # break
            
            print("crt.sh retrival successful\n")
            
            for key, value in crtsh_cert_details.items():
                if "sha256" in value:
                    # print("SHA256")
                    crtsh_sha256[str.lower(value["sha256"])] = key
                # <sha256, id>
                
            # crtsh_sha256.pop(str.lower("1A2410FD48E5A962C901746510F1FB070FE48880FC9C2708A22DBE2BEBBA20A3"))
            # crtsh_sha256.pop(str.lower("449D1A6E0AF9057A65BD8FABA37D6839200E47A178EBDF417E88490D1310F49B"))
            # cert_hash_sha256
            # Facebook CT Monitor
            
            print("########### Facebook Monitor #############")
            facebook_certs = facebook_client.retrieve_cert(args.domain, True, True)
            facebook_cert_details_list = facebook_client.dedup(facebook_certs)
            print("After dedup Facebook Monitor contains %d" % len(facebook_cert_details_list))
            
            for item in facebook_cert_details_list:
                current_id = item["id"]
                facebook_sha256[str.lower(item["cert_hash_sha256"])] = current_id
                facebook_cert_details[current_id] = item
                
            # facebook_sha256.pop(str.lower("1A2410FD48E5A962C901746510F1FB070FE48880FC9C2708A22DBE2BEBBA20A3"))
            # facebook_sha256.pop(str.lower("449D1A6E0AF9057A65BD8FABA37D6839200E47A178EBDF417E88490D1310F49B"))
            
            # for key, value in facebook_cert_details:
                # facebook_sha256[str.lower(value["cert_hash_sha256"])] = key
                
            # missing_certs = set(crtsh_sha256.values()).difference(facebook_sha256)
            missing_certs = set()
            for item in crtsh_sha256.keys():
                if item not in facebook_sha256.keys():
                    missing_certs.add(item)
            for item in facebook_sha256.keys():
                if item not in crtsh_sha256.keys():
                    missing_certs.add(item)
        
            # if len(missing_certs) == 0 or count == 5:
            if len(missing_certs) == 0:
                print("crt.sh returned the same with Facebook")
            else:
                print("crt.sh has %d while Facebook has %d, the difference is %d " % (len(crtsh_sha256), len(facebook_sha256), len(missing_certs)))
                for i in missing_certs:
                    if i in crtsh_sha256:
                        cert_id = crtsh_sha256[i]
                    elif i in facebook_sha256:
                        cert_id = facebook_sha256[i]
                    else:
                        print("ERROR! Cert detail not found")
                    
                    if os.path.exists("./missing_certs.json"):
                        with open("./missing_certs.json") as f:
                            data = json.load(f)
                            
                        content = {}
                        
                        if cert_id in crtsh_cert_details:
                            content[cert_id] = crtsh_cert_details[cert_id]
                        else:
                            content[cert_id] = facebook_cert_details[cert_id]
                            
                        data.update(content)
                        with open("./missing_certs.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4, default=datetime_handler)
                    else:        
                        with open("./missing_certs.json", "w", encoding="utf-8") as f:
                            content = {}
                            if cert_id in crtsh_cert_details:
                                content[cert_id] = crtsh_cert_details[cert_id]
                            else:
                                content[cert_id] = facebook_cert_details[cert_id]
                            json.dump(content, f, ensure_ascii=False, indent=4, default=datetime_handler)
        else:
            print("Start validating")
            if not os.path.exists("./missing_certs.json"):
                print("missing_certs.json not found")
                return
                
            missing_certs = {}
            
            with open("./missing_certs.json") as f:
                missing_certs = json.load(f)
            
        """ 
        if args.save:
            if crtsh_certs is None or len(crtsh_cert_details) == 0:
                print("Current result is empty")
            elif not os.path.exists(args.save):
                os.mkdir(args.save)
                with open(os.path.join(args.save, "/crtsh_certs.json"), "w", encoding="utf-8") as f:
                    json.dump(crtsh_cert_details, f, ensure_ascii=False, indent=4)
                with open(os.path.join(args.save, "/facebook_certs.json"), "w", encoding="utf-8") as f:
                    json.dump(facebook_cert_details, f, ensure_ascii=False, indent=4)
            else:
                with open(args.save + "/crtsh_certs.json", "w", encoding="utf-8") as f:
                    json.dump(crtsh_cert_details, f, ensure_ascii=False, indent=4, default=datetime_handler)
                with open(os.path.join(args.save, "/facebook_certs.json"), "w", encoding="utf-8") as f:
                    json.dump(facebook_cert_details, f, ensure_ascii=False, indent=4) 
        """
        
    except ValueError:
        print("Argument value error!")

if __name__ == "__main__":
    main()
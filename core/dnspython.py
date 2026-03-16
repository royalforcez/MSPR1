import dns.resolver
import dns.exception

def check_dns(server_ip):
    """Test le service DNS de la machine cible"""
    tester = dns.resolver.Resolver()
    tester.nameservers = [server_ip]
    tester.lifetime = 2.0

    try: 
        # Tente de résoudre google.com en utilisant le serveur cible
        tester.resolve('google.com', 'A') 
        return "UP"
    
    except (dns.resolver.Timeout, dns.resolver.NoNameservers, Exception):    
        return "DOWN"































# import dns.resolver
# import dns.exception
# import json

# def connection_test(server_ip, server_name) :
    
#     tester = dns.resolver.Resolver()

#     tester.nameservers = [server_ip]

#     tester.lifetime = 2.0

#     res = {
#         "ip :": server_ip,
#         "name": server_name,
#         "service": "DNS",
#         "statue": "OK",
#         "response_details": ""
#     }

#     try : 
#         response = tester.resolve('google.com', 'A') #A = IPv4 address record
#         res["response_details"] = f"Test OK: {response[0]}"
#         return res
    
#     except dns.resolver.Timeout:    
#         res["statue"] = "ERREUR"
#         res["response_details"] = "Timeout : Le service DNS ne repond pas."

#     except dns.resolver.NoNameservers:
#         res["statue"] = "ERREUR"
#         res["details"] = "Impossible de contacter le domain name server#."

#     return res

# tab = [{"ip":"192.168.10.10","name":"DC01"},
#         {"ip":"192.168.10.11","name":"DC02"}]

# rapport = []

# #for i in tab :
#     #test = connection_test(i["ip"], i["name"])
#     #rapport.append(test)

# #print(json.dumps(rapport, indent=2))
    



# test = connection_test("192.168.179.128", "DNS Server")

# print(json.dumps(test, indent=2))
import dns.resolver
import dns.exception
import json

def connection_test(server_ip, server_name) :
    
    tester = dns.resolver.Resolver()

    tester.nameservers = [server_ip]

    tester.lifetime = 2.0

    res = {
        "ip :": server_ip,
        "name": server_name,
        "service": "DNS",
        "statue": "OK",
        "response_details": ""
    }

    try : 
        response = tester.resolve('google.com', 'A') #A = IPv4 address record
        res["response_details"] = f"Test OK: {response[0]}"
        return res
    
    except dns.resolver.Timeout:    
        res["statue"] = "ERREUR"
        res["response_details"] = "Timeout : Le service DNS ne repond pas."

    except dns.resolver.NoNameservers:
        res["statue"] = "ERREUR"
        res["details"] = "Impossible de contacter le domain name server#."

    return res


test = connection_test("192.168.152.245", "DNS Server")

print(json.dumps(test, indent=2))
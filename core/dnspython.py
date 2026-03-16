import dns.resolver

def check_dns(server_ip):
    tester = dns.resolver.Resolver()
    tester.nameservers = [server_ip]
    tester.lifetime = 2.0
    try: 
        tester.resolve('google.com', 'A') 
        return "UP"
    except:    
        return "DOWN"
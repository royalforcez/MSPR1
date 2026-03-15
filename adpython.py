from ldap3 import Server, Connection, ALL, NTLM, Tls
import ssl
import json


def connection_test(connectionpassword: str, domaine: str, utilisateur: str, ip: str):
    tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS)

    server = Server(ip,
                    port=636,
                    use_ssl=True, 
                    get_info=ALL,
                    tls=tls_config)

    connection = Connection(server, 
                            user=f'{domaine}\\{utilisateur}',
                            password= connectionpassword,
                            authentication='SIMPLE',
                            auto_bind=True)


    return {
        "is connected": connection.bound,
    }

tab = [{"connectionpassword":"Formation2025","domaine":"NTL", "utilisateur":"Administrateur","ip":"192.168.10.10" },
        {"connectionpassword":"Formation2025","domaine":"NTL", "utilisateur":"Administrateur","ip":"192.168.10.11" }]

rapport = []

test = connection_test("Formation2025", "WINSRV", "Administrateur", "192.168.179.128")
#test1 = connection_test("Formation2025", "NTL", "Administrateur", "192.168.10.10")

#for i in tab :
    #test = connection_test(i["connectionpassword"], i["domaine"], i["utilisateur"], i["ip"])
    #rapport.append(test)


print(json.dumps(rapport, indent=2))
print(json.dumps(test, indent=2))
#print(json.dumps(test1, indent=2))

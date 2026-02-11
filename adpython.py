from ldap3 import Server, Connection, ALL, NTLM, Tls
import ssl

tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

server = Server('192.168.139.142',
                port=636,
                use_ssl=True, 
                get_info=ALL,
                tls=tls_config)

connection = Connection(server, 
                        user='TESTSRV\\Administrateur',
                        password='Formation2025',
                        authentication=NTLM,
                        auto_bind=True)

print(f"Connecté : {connection.bound}")


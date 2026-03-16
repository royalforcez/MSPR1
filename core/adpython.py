from ldap3 import Server, Connection, ALL, Tls
import ssl

def check_ad(ip, domaine, utilisateur, connectionpassword):
    try:
        tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS)
        server = Server(ip, port=636, use_ssl=True, get_info=ALL, tls=tls_config)
        connection = Connection(server, user=f'{domaine}\\{utilisateur}', password=connectionpassword, authentication='SIMPLE', auto_bind=True, receive_timeout=3)

        if connection.bound:
            connection.unbind()
            return "UP"
        else:
            return "DOWN"
    except Exception:
        return "DOWN"
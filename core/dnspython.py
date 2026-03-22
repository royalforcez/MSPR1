import dns.resolver

def check_dns(ip_serveur_dns):
    try:
        testeur = dns.resolver.Resolver(configure=False)
        testeur.nameservers = [ip_serveur_dns]
        testeur.lifetime = 3
        domaine_a_tester = "test-cache.sachacazin.fr"
        
        try:
            reponse = testeur.resolve(domaine_a_tester, 'A', tcp= True)
            ip_trouvee = reponse[0].to_text()
            print(f"      [DNS OK] {domaine_a_tester} a répondu avec l'IP : {ip_trouvee}")
            return "UP"
            
        except Exception as e:
            print(f"      [DNS ERREUR] Impossible de résoudre le nom : {e}")
            return "DOWN"

    except Exception as e:
        print(f"      [DNS ERREUR CRITIQUE] Le serveur injoignable : {e}")
        return "DOWN"
    
  
# services up connectes
up

# nombre de requetes effectue sur la route /accounts/me
http_requests_total{service="identity",handler="/accounts/me"}
# requete api accounts/me
curl -k -i https://localhost:8443/api/identity/accounts/me

# camgr

Python script to create new certificates for local CA using OpenSSL.
Script allows for the creation of SANs for hosts.

Run with:
`python certnew.py`

Environment File is needed.  Example:
```aiignore
CA_KEY=/opt/certs/ca/ca.key
CA_CERT=/opt/certs/ca/ca.crt
OUTPUT_DIR=certs
ORGANIZATION=orgname
COUNTRY=AU
```

- Create the CA first.

```aiignore
openssl genrsa -aes256 -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt -subj "/CN=My Root CA/O=My Organization/C=US"
openssl x509 -in ca.crt -text -noout
```


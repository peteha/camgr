# **camgr**
A Python script to create and manage SSL/TLS certificates using a local CA with `OpenSSL`. This script supports creating **Subject Alternative Names (SANs)** for hosts and provides tools for certificate renewal while maintaining consistency across SAN configurations.
## **Features**
- **Generate New Certificates:** Creates private keys, CSRs, and signed certificates.
- **Subject Alternative Names (SANs):** Allows specifying SANs for certificates and stores SAN configurations for reuse.
- **Renew Certificates:** Automatically renews certificates using existing CSRs and SAN files.
- **Environment File Configuration:** Easily customize paths, organization details, and certificate validity.

## **Setup**
### **Environment File**
The script requires an `.env` file to store essential paths and configurations. Below is an example `.env` file:

```aiignore
CA_KEY=/opt/certs/ca/ca.key
CA_CERT=/opt/certs/ca/ca.crt
OUTPUT_DIR=certs
ORGANIZATION=orgname
COUNTRY=AU
CERT_VALIDITY_DAYS=365
```
### **Create the CA**
Before generating certificates, you need to create the Certificate Authority (CA) key and certificate. Use the following commands:

```aiignore
openssl genrsa -aes256 -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt -subj "/CN=My Root CA/O=My Organization/C=US"
openssl x509 -in ca.crt -text -noout
```
Ensure the generated `ca.key` and `ca.crt` files are placed in the locations specified in the `.env` file.

## **Run the Script**
Run the script to create or renew certificates:
`python certnew.py`

## **Arguments**
The script accepts the following arguments:

| Argument | Description |
| --- | --- |
| `-cn`, `--common-name` | (Required unless renewing) Specify the `Common Name` for the certificate (e.g., `example.com`). |
| `-san`, `--subject-alternative-names` | (Optional) Comma-separated list of SANs (e.g., `www.example.com,api.example.com`). |
| `-pw`, `--password` | Password for the CA private key (leave empty if no password is required). |
| `-r`, `--renew` | Flag to renew all certificates based on the CSRs and SAN files in the output directory. |

## **Examples**
### **Generate a Certificate**
To generate a certificate for `example.com` with SANs for `www.example.com` and `api.example.com`:
``` bash
python certnew.py --common-name example.com --subject-alternative-names www.example.com,api.example.com --password mypassword
```
### **Default SAN (No SANs Provided)**
If no SANs are explicitly passed, the SAN will default to the `Common Name`:
``` bash
python certnew.py --common-name example.com
```
### **Renew Certificates**
To renew all certificates based on the CSRs and SAN files in the `OUTPUT_DIR`:
``` bash
python certnew.py --renew
```
Ensure the corresponding `.csr` and `.san` files are present in the output directory.

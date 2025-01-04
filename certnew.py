import os
import subprocess
from getpass import getpass
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

# Read environment variables
CA_KEY = os.getenv("CA_KEY", "./ca.key")
CA_CERT = os.getenv("CA_CERT", "./ca.crt")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./certs")
ORGANIZATION = os.getenv("ORGANIZATION", "DefaultOrganization")
COUNTRY = os.getenv("COUNTRY", "US")
CERT_VALIDITY_DAYS = int(os.getenv("CERT_VALIDITY_DAYS", "365"))  # Default to 365 days if not specified


def generate_certificate_from_csr(csr_file, cert_file, san_file, ca_key_password=None):
    """
    Generate a certificate from an existing CSR file while reusing SANs stored in a file.
    """
    try:
        print(f"Renewing certificate for CSR: {csr_file}")

        if not os.path.exists(san_file):
            raise FileNotFoundError(f"SAN configuration file not found: {san_file}")

        # Sign the certificate using the stored SAN configuration
        sign_command = [
            "openssl",
            "x509",
            "-req",
            "-in",
            csr_file,
            "-CA",
            CA_CERT,
            "-CAkey",
            CA_KEY,
            "-CAcreateserial",
            "-out",
            cert_file,
            "-days",
            str(CERT_VALIDITY_DAYS),
            "-sha256",
            "-extensions",
            "v3_req",
            "-extfile",
            san_file,
        ]

        if ca_key_password:
            sign_command.extend(["-passin", f"pass:{ca_key_password}"])

        subprocess.run(sign_command, check=True)

        print(f"Certificate successfully renewed: {cert_file}")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred during the certificate renewal process: {e}")
        raise


def generate_san_file(common_name, sans):
    """
    Save the SAN configuration to the output directory in a file.
    """
    san_file_path = os.path.join(OUTPUT_DIR, f"{common_name}.san")
    config_content = f"""
[ req ]
default_bits        = 2048
prompt              = no
distinguished_name  = req_distinguished_name
req_extensions      = v3_req
x509_extensions     = v3_req

[ req_distinguished_name ]
C  = {COUNTRY}
O  = {ORGANIZATION}
CN = {common_name}

[ v3_req ]
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = {common_name}
"""

    # Add SANs to the configuration
    if sans:
        for idx, san in enumerate(sans, start=2):
            config_content += f"DNS.{idx} = {san}\n"

    # Save SAN configuration to file
    with open(san_file_path, "w") as f:
        f.write(config_content)

    print(f"SAN file created: {san_file_path}")
    return san_file_path


def renew_all_csrs(output_dir, ca_key_password):
    """
    Renew all CSRs in the output directory using stored SAN files.
    """
    print("Looking for CSRs to renew...")

    for file_name in os.listdir(output_dir):
        if file_name.endswith(".csr"):
            csr_file = os.path.join(output_dir, file_name)
            cert_file = os.path.join(output_dir, file_name.replace(".csr", ".crt"))
            common_name = os.path.splitext(file_name)[0]
            san_file = os.path.join(output_dir, f"{common_name}.san")

            # Renew certificate using the CSR and the corresponding SAN file
            generate_certificate_from_csr(csr_file, cert_file, san_file, ca_key_password)

    print("All CSRs have been renewed!")


def generate_certificate(common_name, sans=None, ca_key_password=None):
    """
    Generate a new private key, CSR, certificate, and save the SAN config to a file.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # File paths
    key_file = os.path.join(OUTPUT_DIR, f"{common_name}.key")
    csr_file = os.path.join(OUTPUT_DIR, f"{common_name}.csr")
    cert_file = os.path.join(OUTPUT_DIR, f"{common_name}.crt")

    try:
        # Generate private key
        print(f"Generating private key: {key_file}")
        subprocess.run(["openssl", "genrsa", "-out", key_file, "2048"], check=True)

        # Generate CSR with SANs if provided
        if sans:
            print(f"Generating CSR with SANs: {csr_file}")
            san_file = generate_san_file(common_name, sans)

            # Generate CSR using the SAN configuration
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-key",
                    key_file,
                    "-out",
                    csr_file,
                    "-config",
                    san_file,
                ],
                check=True,
            )
        else:
            print(f"Generating CSR without SANs: {csr_file}")
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-new",
                    "-key",
                    key_file,
                    "-out",
                    csr_file,
                    "-subj",
                    f"/C={COUNTRY}/O={ORGANIZATION}/CN={common_name}",
                ],
                check=True,
            )

        # Generate SAN file
        san_file = generate_san_file(common_name, sans or [])

        # Sign the CSR to create the certificate
        print(f"Signing certificate: {cert_file}")
        sign_command = [
            "openssl",
            "x509",
            "-req",
            "-in",
            csr_file,
            "-CA",
            CA_CERT,
            "-CAkey",
            CA_KEY,
            "-CAcreateserial",
            "-out",
            cert_file,
            "-days",
            str(CERT_VALIDITY_DAYS),
            "-sha256",
            "-extensions",
            "v3_req",
            "-extfile",
            san_file,
        ]

        if ca_key_password:
            sign_command.extend(["-passin", f"pass:{ca_key_password}"])

        subprocess.run(sign_command, check=True)

        print("Certificate successfully created!")
        print(f"  Private Key File: {key_file}")
        print(f"  CSR File        : {csr_file}")
        print(f"  Certificate File: {cert_file}")
        print(f"  SAN File        : {san_file}")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred during the OpenSSL process: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SSL certificates and manage renewals.")
    parser.add_argument("-cn", "--common-name", help="Common Name (e.g., example.com)", required=False)
    parser.add_argument(
        "-san",
        "--subject-alternative-names",
        help="Comma-separated SANs (e.g., www.example.com,api.example.com)",
        required=False,
    )
    parser.add_argument("-pw", "--password", help="Password for the CA private key", required=False)
    parser.add_argument(
        "-r", "--renew", action="store_true", help="Renew all CSRs in the output directory", required=False
    )

    args = parser.parse_args()

    # Handle password input
    ca_key_password = args.password or getpass("Enter password for CA private key (if any): ")

    try:
        if args.renew:
            # Renew all CSRs in the output directory
            renew_all_csrs(OUTPUT_DIR, ca_key_password)
        else:
            # Create a new certificate
            common_name = args.common_name or input("Enter Common Name (e.g., example.com): ").strip()
            sans_input = args.subject_alternative_names or input(
                "Enter SANs (comma-separated, optional): "
            ).strip()
            sans_list = [san.strip() for san in sans_input.split(",")] if sans_input else None
            generate_certificate(common_name, sans_list, ca_key_password)
    except Exception as e:
        print(f"An error occurred: {e}")

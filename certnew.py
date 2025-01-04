import os
import subprocess
import tempfile
from getpass import getpass
from dotenv import load_dotenv  # To load environment variables from .env

# Load environment variables from .env file
load_dotenv()

# Read environment variables
CA_KEY = os.getenv("CA_KEY", "./ca.key")
CA_CERT = os.getenv("CA_CERT", "./ca.crt")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./certs")
ORGANIZATION = os.getenv("ORGANIZATION", "DefaultOrganization")
COUNTRY = os.getenv("COUNTRY", "US")


def generate_san_config(common_name, sans):
    """
    Generate a temporary OpenSSL configuration file to include SANs.
    """
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

    # Add additional SAN entries
    for idx, san in enumerate(sans, start=2):
        config_content += f"DNS.{idx} = {san}\n"

    # Write to a temporary configuration file
    san_config = tempfile.mktemp()
    with open(san_config, "w") as f:
        f.write(config_content)

    return san_config


def generate_certificate(
        common_name,
        sans=None,
        ca_key_password=None,
):
    """
    Generate private key, CSR, and signed certificate including SANs.
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
            print("Generating CSR with SANs...")
            san_config = generate_san_config(common_name, sans)

            # Generate the CSR
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
                    san_config,
                ],
                check=True,
            )

            # Cleanup the temporary SAN configuration file
            os.remove(san_config)
        else:
            print("Generating CSR without SANs...")
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

        # Sign the CSR to create the certificate
        print("Signing certificate...")
        san_config = generate_san_config(common_name, sans or [])

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
            "365",
            "-sha256",
            "-extensions",
            "v3_req",
            "-extfile",
            san_config,
        ]

        # Include CA private key password if provided
        if ca_key_password:
            sign_command.extend(["-passin", f"pass:{ca_key_password}"])

        subprocess.run(sign_command, check=True)

        # Cleanup the temporary SAN configuration file
        os.remove(san_config)

        print("Certificate successfully created!")
        print(f"  Private Key File: {key_file}")
        print(f"  CSR File        : {csr_file}")
        print(f"  Certificate File: {cert_file}")

        return key_file, csr_file, cert_file

    except subprocess.CalledProcessError as e:
        print(f"An error occurred during the OpenSSL process: {e}")
        raise


if __name__ == "__main__":
    try:
        # Get user inputs
        common_name = input("Enter Common Name (e.g., example.com): ").strip()
        sans_input = input("Enter Subject Alternative Names (comma-separated, optional): ").strip()
        ca_key_password = getpass("Enter password for CA private key (if any): ")  # Hide input for password
        sans = [san.strip() for san in sans_input.split(",")] if sans_input else None

        generate_certificate(common_name, sans, ca_key_password)

    except Exception as e:
        print(f"An error occurred: {e}")

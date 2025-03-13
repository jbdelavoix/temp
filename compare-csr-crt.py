from cryptography import x509
from cryptography.hazmat.backends import default_backend


# Fonction pour extraire les SANs (Subject Alternative Names)
def extract_sans(certificate):
    try:
        ext = certificate.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
        return ext.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        return []


# Charger un certificat à partir d'un fichier CRT
def load_certificate(file_path):
    with open(file_path, "rb") as f:
        cert_data = f.read()
    cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    return cert


# Charger un CSR à partir d'un fichier CSR
def load_csr(file_path):
    with open(file_path, "rb") as f:
        csr_data = f.read()
    csr = x509.load_pem_x509_csr(csr_data, default_backend())
    return csr


# Obtenir les SANs uniques dans le CSR mais absents du CRT
def get_unique_sans(csr_file, crt_file):
    csr = load_csr(csr_file)
    crt = load_certificate(crt_file)

    csr_sans = set(extract_sans(csr))
    crt_sans = set(extract_sans(crt))

    unique_sans = csr_sans - crt_sans
    return list(unique_sans)


# Exemple d'utilisation
csr_file_path = "chemin/vers/votre_fichier.csr"
crt_file_path = "chemin/vers/votre_fichier.crt"

unique_sans = get_unique_sans(csr_file_path, crt_file_path)
print("SANs uniques dans le CSR mais absents du CRT :", unique_sans)

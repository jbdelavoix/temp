import os
import requests
from flask import Flask, jsonify, abort, request, Response, send_from_directory

app = Flask(__name__)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# Configuration de ton provider custom
PROVIDERS = {
    "org": {
        "myprovider": {
            "1.0.0": {
                "linux": {
                    "amd64": {
                        "download_url": "https://toto.com/downloads/terraform-provider-myprovider_1.0.0_linux_amd64.zip",
                        "shasum": "1111111111111111111111111111111111111111111111111111111111111111"
                    }
                }
            }
        }
    }
}

# 1. Découverte du registry
@app.route("/.well-known/terraform.json", methods=["GET"])
def terraform_discovery():
    return jsonify({
        "providers.v1": "/v1/providers/"
    })

# 2. Liste des versions disponibles d'un provider
@app.route("/v1/providers/<namespace>/<type>/versions", methods=["GET"])
def provider_versions(namespace, type):
    if namespace in PROVIDERS and type in PROVIDERS[namespace]:
        versions_data = PROVIDERS[namespace][type]
        return jsonify({
            "versions": [
                {
                    "version": version,
                    "platforms": [
                        {"os": os, "arch": arch}
                        for os in versions_data[version]
                        for arch in versions_data[version][os]
                    ]
                }
                for version in versions_data
            ]
        })
    else:
        return proxy_to_registry_io(request)

# 3. Metadata pour téléchargement du provider
@app.route("/v1/providers/<namespace>/<type>/<version>/download/<os>/<arch>", methods=["GET"])
def download_metadata(namespace, type, version, os, arch):
    try:
        data = PROVIDERS[namespace][type][version][os][arch]
        return jsonify({
            "protocols": ["5.0"],
            "os": os,
            "arch": arch,
            "filename": f"terraform-provider-{type}_{version}_{os}_{arch}.zip",
            "download_url": data["download_url"],
            "shasum": data["shasum"]
        })
    except KeyError:
        return proxy_to_registry_io(request)

# 4. Servir les fichiers ZIP localement
@app.route("/downloads/<path:filename>", methods=["GET"])
def serve_download(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

# 5. Proxy fallback vers registry.terraform.io
def proxy_to_registry_io(req):
    url = f"https://registry.terraform.io{req.full_path}"
    print(f"→ Proxy: {url}")
    upstream = requests.get(url, headers={"Accept": "application/json"})
    return Response(
        upstream.content,
        status=upstream.status_code,
        content_type=upstream.headers.get("Content-Type")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=("toto.com.pem", "toto.com-key.pem"))

"""Temporary private CA, never installed in a system store or packaged."""
from pathlib import Path
import shutil
import subprocess


def create_certificates(directory: Path) -> Path:
    openssl = shutil.which("openssl")
    if not openssl:
        raise RuntimeError("OpenSSL with req -addext support is required")
    directory.chmod(0o700)
    def run(*args):
        subprocess.run([openssl, *args], cwd=directory, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
    run("req", "-x509", "-newkey", "rsa:2048", "-noenc", "-days", "1",
        "-keyout", "ca.key", "-out", "ca.pem", "-subj", "/CN=js2py temporary CA",
        "-addext", "basicConstraints=critical,CA:TRUE",
        "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    run("req", "-new", "-newkey", "rsa:2048", "-noenc", "-keyout", "leaf.key",
        "-out", "leaf.csr", "-subj", "/CN=lab.test")
    (directory / "leaf.ext").write_text(
        "subjectAltName=DNS:lab.test\nbasicConstraints=critical,CA:FALSE\n"
        "keyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n")
    run("x509", "-req", "-in", "leaf.csr", "-CA", "ca.pem", "-CAkey", "ca.key",
        "-CAcreateserial", "-out", "leaf.pem", "-days", "1", "-sha256", "-extfile", "leaf.ext")
    for item in directory.iterdir():
        if item.is_file():
            item.chmod(0o600)
    return directory / "ca.pem"

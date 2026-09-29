"""Text invariants only; not caddy validate or a public TLS acceptance test."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check():
    local = (ROOT / "Caddyfile.local").read_text()
    prod = (ROOT / "Caddyfile.production.template").read_text()
    assert "bind 127.0.0.1" in local and "admin off" in local
    assert "api.example.invalid" in prod
    for source in (local, prod):
        assert "reverse_proxy 127.0.0.1:8034" in source
        assert "header_up -Forwarded" in source
        assert "tls_insecure_skip_verify" not in source
        assert "trusted_proxies" not in source
    return ["same_host_upstream=loopback", "production_domain=reserved_placeholder",
            "caddy_runtime=NOT_VERIFIED", "public_dns_and_certificate=NOT_VERIFIED"]


if __name__ == "__main__":
    print("\n".join(check()))

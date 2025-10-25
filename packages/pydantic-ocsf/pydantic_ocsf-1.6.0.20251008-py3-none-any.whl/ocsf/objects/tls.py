from typing import ClassVar

from ocsf.objects.certificate import Certificate
from ocsf.objects.fingerprint import Fingerprint
from ocsf.objects.object import Object
from ocsf.objects.san import San
from ocsf.objects.tls_extension import TLSExtension


class TLS(Object):
    allowed_profiles: ClassVar[list[str]] = []
    schema_name: ClassVar[str] = "tls"

    # Required
    version: str

    # Recommended
    certificate: Certificate | None = None
    certificate_chain: list[str] | None = None
    cipher: str | None = None
    client_ciphers: list[str] | None = None
    ja3_hash: Fingerprint | None = None
    ja3s_hash: Fingerprint | None = None
    sni: str | None = None

    # Optional
    alert: int | None = None
    extension_list: list[TLSExtension] | None = None
    handshake_dur: int | None = None
    key_length: int | None = None
    sans: list[San] | None = None
    server_ciphers: list[str] | None = None
    tls_extension_list: list[TLSExtension] | None = None

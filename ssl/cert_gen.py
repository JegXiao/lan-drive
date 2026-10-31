import os
import socket
import ipaddress
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_self_signed_cert():
    # 1. 获取本机 IP
    def get_host_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    local_ip = get_host_ip()
    print(f"正在为 IP: {local_ip} 生成自签证书...")

    # 2. 生成私钥
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 3. 构建证书信息
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"CN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"GD"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"SZ"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"JEGPAN Storage"),
        x509.NameAttribute(NameOID.COMMON_NAME, local_ip),
    ])

    # 使用新版的 timezone-aware datetime
    now = datetime.now(timezone.utc)

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now
    ).not_valid_after(
        now + timedelta(days=3650)
    ).add_extension(
        # 修复点：使用 ipaddress.ip_address() 包装 IP 字符串
        x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.ip_address(local_ip)),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            x509.DNSName(u"localhost"),
        ]),
        critical=False,
    ).sign(key, hashes.SHA256())

    # 4. 保存私钥
    with open("key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # 5. 保存证书
    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"✅ 证书生成成功！\n文件位置: {os.getcwd()}\n包含 IP: {local_ip}")

if __name__ == "__main__":
    generate_self_signed_cert()
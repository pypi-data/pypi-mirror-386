import argparse
from .server import SecureChatServer
from .client import SecureChatClient

def main():
    parser = argparse.ArgumentParser(description='Secure Chat')
    subparsers = parser.add_subparsers(dest='command')

    server_parser = subparsers.add_parser('server', help='Start server')
    server_parser.add_argument('--port', type=int, default=12346)
    server_parser.add_argument('--cert', default='server.crt', help='Certificate file')
    server_parser.add_argument('--key', default='server.key', help='Key file')
    server_parser.add_argument('--db-path', help='Database file path')

    client_parser = subparsers.add_parser('client', help='Start client')
    client_parser.add_argument('server', help='server:port')
    client_parser.add_argument('username', help='your username')

    cert_parser = subparsers.add_parser('generate-certs', help='Generate self-signed certificates')

    args = parser.parse_args()

    if args.command == 'server':
        server = SecureChatServer(port=args.port, cert_file=args.cert, key_file=args.key, db_path=args.db_path)
        server.start()
    elif args.command == 'client':
        host, port = args.server.split(':')
        client = SecureChatClient(host, int(port), args.username)
        client.connect()
    elif args.command == 'generate-certs':
        from .crypto import generate_self_signed_cert
        generate_self_signed_cert('server.crt', 'server.key')
        print("Certificates generated: server.crt, server.key")

if __name__ == '__main__':
    main()
from app import app
import ssl

if __name__ == '__main__':
    #app.run(debug=True)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.load_cert_chain('cert.pem', 'key.pem')
    app.run(host='127.0.0.1', port=5000, ssl_context=context, debug=True)

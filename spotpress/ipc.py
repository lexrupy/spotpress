from spotpress.qtcompat import QLocalSocket, QLocalServer
from spotpress.utils import SOCKET_NAME
import atexit

# Garante que o socket seja removido em encerramento normal
atexit.register(lambda: QLocalServer.removeServer(SOCKET_NAME))


def send_command_to_existing_instance(command, name=SOCKET_NAME):
    """
    Tenta se conectar a uma instância existente e envia um comando via QLocalSocket.
    Retorna True se o comando foi enviado, False se não há instância ativa.
    """
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(500):
        return False
    socket.write(command.encode())
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def setup_ipc_server(callback, name=SOCKET_NAME, parent=None):
    """
    Cria um QLocalServer que escuta comandos externos.
    `callback` será chamado com a string recebida.

    Retorna o QLocalServer criado ou None se o socket já estiver em uso.
    """
    try:
        QLocalServer.removeServer(name)
    except Exception:
        pass  # Pode ignorar falhas aqui

    server = QLocalServer(parent)
    if not server.listen(name):
        return None  # Já está rodando

    def handle_new_connection():
        socket = server.nextPendingConnection()
        if not socket:
            return

        def read_and_dispatch():
            try:
                # data = bytes(socket.readAll()).decode(errors="ignore").strip()
                data = socket.readAll().data().decode(errors="ignore").strip()
                if data:
                    callback(data)
            except Exception:
                pass

        socket.readyRead.connect(read_and_dispatch)
        socket.disconnected.connect(socket.deleteLater)

    server.newConnection.connect(handle_new_connection)
    return server

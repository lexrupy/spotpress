#!/usr/bin/env python3
import sys
from spotpress.ipc import send_command_to_existing_instance


def main():
    if len(sys.argv) <= 1:
        print("Uso: spotpressctl [comando]")
        print("Comandos disponíveis:")
        print("  --show-config       Exibe a janela principal")
        print("  --quit              Encerra o SpotPress")
        print("  --set-mode=MODE     Define o modo (spotlight, laser, pen)")
        sys.exit(1)

    command = " ".join(sys.argv[1:])
    if send_command_to_existing_instance(command):
        sys.exit(0)
    else:
        print("Nenhuma instância do SpotPress está em execução.")
        sys.exit(1)


if __name__ == "__main__":
    main()

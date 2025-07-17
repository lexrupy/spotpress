#!/bin/bash
set -e

APPDIR=AppDir

# Limpa diretório
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Cria venv e instala dependências
python3 -m venv --copies "$APPDIR/usr/venv"
"$APPDIR/usr/venv/bin/pip" install --upgrade pip
"$APPDIR/usr/venv/bin/pip" install  -r requirements.txt
# Copia scripts
cp main.py spotpressctl.py spotpress.sh -t "$APPDIR/usr/bin/"
cp -r spotpress "$APPDIR/usr/bin/"

# Atalho para launcher
# echo -e '#!/bin/bash\nDIR="$(dirname "$(readlink -f "$0")")"\n"$DIR/../venv/bin/python3" "$DIR/main.py" "$@"' > "$APPDIR/usr/bin/spotpress-launcher"
# chmod +x "$APPDIR/usr/bin/spotpress-launcher"

# Cria AppRun launcher

# Ícone e desktop
cp spotpress.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/spotpress.png"
cp spotpress.desktop "$APPDIR/"


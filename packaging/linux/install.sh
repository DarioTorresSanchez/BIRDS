#!/bin/sh
# Installs B.I.R.D.S for the current user, from the unpacked Linux bundle:
#
#     ./install.sh               install, or replace an earlier copy
#     ./install.sh --uninstall   remove it again
#
# Everything goes under the home folder -- no administrator password.
# The program goes to ~/.local/share/BIRDS, a BIRDS command to
# ~/.local/bin, and the menu entry, the .birds session type and both
# icons to where the desktop looks for them, so the app appears among
# the others and a .birds file opens with a double-click.

set -e

here=$(cd "$(dirname "$0")" && pwd)
data=${XDG_DATA_HOME:-$HOME/.local/share}
prefix="$data/BIRDS"
bin="$HOME/.local/bin"

app_icon="$data/icons/hicolor/256x256/apps/birds.png"
doc_icon="$data/icons/hicolor/256x256/mimetypes/application-x-birds-session.png"
mime="$data/mime/packages/birds-session.xml"
entry="$data/applications/birds.desktop"

# The desktop's caches; each tool is optional, and missing ones are skipped.
refresh() {
    if command -v update-mime-database >/dev/null 2>&1; then
        update-mime-database "$data/mime" || true
    fi
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$data/applications" || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q -t "$data/icons/hicolor" 2>/dev/null || true
    fi
}

if [ "$1" = "--uninstall" ]; then
    rm -rf "$prefix"
    rm -f "$app_icon" "$doc_icon" "$mime" "$entry"
    # Only the command this script made, not one of the same name.
    if [ -L "$bin/BIRDS" ]; then
        rm -f "$bin/BIRDS"
    fi
    refresh
    echo "B.I.R.D.S has been removed."
    exit 0
fi

if [ ! -x "$here/BIRDS/BIRDS" ]; then
    echo "Run this from the unpacked bundle: BIRDS/BIRDS is not next to it." >&2
    exit 1
fi

rm -rf "$prefix"
mkdir -p "$prefix" "$bin" "$(dirname "$app_icon")" "$(dirname "$doc_icon")" \
         "$(dirname "$mime")" "$(dirname "$entry")"
cp -R "$here/BIRDS/." "$prefix/"
ln -sf "$prefix/BIRDS" "$bin/BIRDS"

cp "$here/birds_app_256.png" "$app_icon"
cp "$here/birds_document_256.png" "$doc_icon"
cp "$here/birds-session.xml" "$mime"
# The entry names the program by its full path, so the menu and a
# double-click work even where ~/.local/bin is not on the PATH.
sed "s|^Exec=BIRDS |Exec=\"$prefix/BIRDS\" |" "$here/birds.desktop" > "$entry"
refresh

echo "B.I.R.D.S is installed: open it from the applications menu, or type BIRDS."
case ":$PATH:" in
    *":$bin:"*) ;;
    *) echo "(The BIRDS command needs $bin on your PATH; the menu works without it.)" ;;
esac

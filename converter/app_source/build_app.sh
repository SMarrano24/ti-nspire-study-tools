#!/bin/bash
# Builds "Nspire Convert.app" in the folder above this one.
set -e
cd "$(dirname "$0")"
APP="../Nspire Convert.app"
VERSION=$(sed -n 's/^let appVersion = "\(.*\)"$/\1/p' NspireConvert.swift)  # the version shown at the top of the window
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
swiftc -O -target arm64-apple-macos14.0 -parse-as-library NspireConvert.swift -o "$APP/Contents/MacOS/NspireConvert"
cp ../nspire_convert.py luna/luna "$APP/Contents/Resources/"
[ -f AppIcon.icns ] && cp AppIcon.icns "$APP/Contents/Resources/"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Nspire Convert</string>
  <key>CFBundleDisplayName</key><string>Nspire Convert</string>
  <key>CFBundleIdentifier</key><string>local.nspireconvert</string>
  <key>CFBundleExecutable</key><string>NspireConvert</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>CFBundleDocumentTypes</key><array><dict>
    <key>CFBundleTypeName</key><string>Document</string>
    <key>CFBundleTypeRole</key><string>Viewer</string>
    <key>LSHandlerRank</key><string>Alternate</string>
    <key>LSItemContentTypes</key><array><string>public.data</string><string>public.content</string></array>
  </dict></array>
</dict></plist>
PLIST
codesign --force --deep -s - "$APP"
echo "Built $APP"

# Also refresh any other copies of the app, so an old one never gets used by mistake.
for COPY in "$HOME/Desktop/Nspire Convert.app" "/Applications/Nspire Convert.app"; do
  if [ -d "$COPY" ]; then rm -rf "$COPY" && ditto "$APP" "$COPY" && echo "Updated $COPY"; fi
done

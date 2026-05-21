#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${ROOT_DIR}/runtime"
ENV_ROOT="${RUNTIME_DIR}/aspose_envs"
COMPAT_ROOT="${RUNTIME_DIR}/compat/openssl1.1"
COMPAT_LIB_DIR="${COMPAT_ROOT}/usr/lib/x86_64-linux-gnu"
LIBSSL_DEB="${RUNTIME_DIR}/downloads/libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb"
LIBSSL_URL="http://security.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb"
GDIPLUS_ROOT="${RUNTIME_DIR}/compat/libgdiplus"
GDIPLUS_LIB_DIR="${GDIPLUS_ROOT}/usr/lib"
GDIPLUS_DEB="${RUNTIME_DIR}/downloads/libgdiplus_6.0.4+dfsg-2_amd64.deb"
GDIPLUS_URL="http://archive.ubuntu.com/ubuntu/pool/universe/libg/libgdiplus/libgdiplus_6.0.4+dfsg-2_amd64.deb"
EXIF_ROOT="${RUNTIME_DIR}/compat/libexif"
EXIF_LIB_DIR="${EXIF_ROOT}/usr/lib/x86_64-linux-gnu"
EXIF_DEB="${RUNTIME_DIR}/downloads/libexif12_0.6.24-1build1_amd64.deb"
EXIF_URL="http://archive.ubuntu.com/ubuntu/pool/main/libe/libexif/libexif12_0.6.24-1build1_amd64.deb"

mkdir -p "${RUNTIME_DIR}/downloads" "${COMPAT_ROOT}" "${ENV_ROOT}"

if [[ ! -f "${COMPAT_LIB_DIR}/libssl.so.1.1" || ! -f "${COMPAT_LIB_DIR}/libcrypto.so.1.1" ]]; then
  echo "Fetching OpenSSL 1.1 compatibility package..."
  wget -q -O "${LIBSSL_DEB}" "${LIBSSL_URL}"
  dpkg-deb -x "${LIBSSL_DEB}" "${COMPAT_ROOT}"
fi

if [[ ! -f "${GDIPLUS_LIB_DIR}/libgdiplus.so" ]]; then
  echo "Fetching libgdiplus compatibility package..."
  wget -q -O "${GDIPLUS_DEB}" "${GDIPLUS_URL}"
  dpkg-deb -x "${GDIPLUS_DEB}" "${GDIPLUS_ROOT}"
fi
ln -sf libgdiplus.so "${GDIPLUS_LIB_DIR}/liblibgdiplus.so"
ln -sf libgdiplus.so "${GDIPLUS_LIB_DIR}/liblibgdiplus"

if [[ ! -f "${EXIF_LIB_DIR}/libexif.so.12" ]]; then
  echo "Fetching libexif compatibility package..."
  wget -q -O "${EXIF_DEB}" "${EXIF_URL}"
  dpkg-deb -x "${EXIF_DEB}" "${EXIF_ROOT}"
fi

create_env() {
  local name="$1"
  local package="$2"
  local env_dir="${ENV_ROOT}/${name}"

  echo "Preparing ${name} worker environment..."
  rm -rf "${env_dir}"
  python3 -m venv "${env_dir}"
  "${env_dir}/bin/python" -m pip install --upgrade pip
  "${env_dir}/bin/python" -m pip install -e "${ROOT_DIR}"
  "${env_dir}/bin/python" -m pip install "${package}"
}

create_env "word" "aspose-words>=26.5,<27.0"
create_env "cells" "aspose-cells-python>=26.5,<27.0"
create_env "slides" "aspose-slides>=26.5,<27.0"
create_env "email" "Aspose.Email-for-Python-via-NET>=26.5,<27.0"

cat > "${RUNTIME_DIR}/.env.runtime" <<EOF
export ASPOSE_SERVICE_WORKER_LIBRARY_PATH="${COMPAT_LIB_DIR}:${GDIPLUS_LIB_DIR}:${EXIF_LIB_DIR}"
export ASPOSE_SERVICE_WORD_PYTHON="${ENV_ROOT}/word/bin/python"
export ASPOSE_SERVICE_CELLS_PYTHON="${ENV_ROOT}/cells/bin/python"
export ASPOSE_SERVICE_SLIDES_PYTHON="${ENV_ROOT}/slides/bin/python"
export ASPOSE_SERVICE_EMAIL_PYTHON="${ENV_ROOT}/email/bin/python"
EOF

echo "Worker environments are ready."
echo "Run: source ${RUNTIME_DIR}/.env.runtime"

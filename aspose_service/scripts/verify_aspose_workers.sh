#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

source "${ROOT_DIR}/runtime/.env.runtime"
export LD_LIBRARY_PATH="${ASPOSE_SERVICE_WORKER_LIBRARY_PATH}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

"${ASPOSE_SERVICE_WORD_PYTHON}" -c 'import aspose.words as aw; print("word", hasattr(aw, "Document"))'
"${ASPOSE_SERVICE_CELLS_PYTHON}" -c 'import aspose.cells as cells; print("cells", hasattr(cells, "Workbook"))'
"${ASPOSE_SERVICE_SLIDES_PYTHON}" -c 'import aspose.slides as slides; print("slides", hasattr(slides, "Presentation"))'
"${ASPOSE_SERVICE_EMAIL_PYTHON}" -c 'import aspose.email as email; print("email", hasattr(email, "MailMessage"))'

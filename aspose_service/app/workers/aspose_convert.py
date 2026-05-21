import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) not in {4, 5}:
        print(
            "Usage: python -m app.workers.aspose_convert <word|excel|presentation|email-mhtml> <source> <output> [license]",
            file=sys.stderr,
        )
        return 64

    family = argv[1]
    source_path = Path(argv[2])
    output_path = Path(argv[3])
    license_path = Path(argv[4]) if len(argv) == 5 else None

    try:
        if family == "word":
            convert_word(source_path, output_path, license_path)
        elif family == "excel":
            convert_excel(source_path, output_path, license_path)
        elif family == "presentation":
            convert_presentation(source_path, output_path, license_path)
        elif family == "email-mhtml":
            convert_email_to_mhtml(source_path, output_path, license_path)
        else:
            print(f"Unsupported worker family: {family}", file=sys.stderr)
            return 64
    except ImportError as exc:
        print(f"Missing Aspose dependency: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


def convert_word(source_path: Path, output_path: Path, license_path: Path | None) -> None:
    import aspose.words as aw

    if license_path and license_path.exists():
        aw.License().set_license(str(license_path))
    document = aw.Document(str(source_path))
    document.save(str(output_path), aw.SaveFormat.PDF)


def convert_excel(source_path: Path, output_path: Path, license_path: Path | None) -> None:
    import aspose.cells as cells

    if license_path and license_path.exists():
        cells.License().set_license(str(license_path))
    workbook = cells.Workbook(str(source_path))
    workbook.save(str(output_path), cells.SaveFormat.PDF)


def convert_presentation(source_path: Path, output_path: Path, license_path: Path | None) -> None:
    import aspose.slides as slides

    if license_path and license_path.exists():
        slides.License().set_license(str(license_path))
    with slides.Presentation(str(source_path)) as presentation:
        presentation.save(str(output_path), slides.export.SaveFormat.PDF)


def convert_email_to_mhtml(source_path: Path, output_path: Path, license_path: Path | None) -> None:
    import aspose.email as email

    if license_path and license_path.exists():
        email.License().set_license(str(license_path))
    message = email.MailMessage.load(str(source_path))
    message.save(str(output_path), email.SaveOptions.default_mhtml)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

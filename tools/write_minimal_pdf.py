"""Genera un PDF de una página de ejemplo (solo biblioteca estándar)."""

from __future__ import annotations

from pathlib import Path


def _escape_pdf_text(s: str) -> str:
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "knowledge_base" / "05_codigo_conducta.pdf"

    lines = [
        "Codigo de Conducta — Acme Labs S.A.S. (ficticio)",
        "",
        "Confidencialidad: no compartir credenciales ni datos personales de clientes",
        "fuera de los sistemas aprobados.",
        "",
        "Regalos: no aceptar regalos mayores a 150.000 COP sin reportar a Compliance.",
        "",
        "Conflictos de interes: declararlos antes de firmar contratos con proveedores",
        "relacionados.",
    ]

    ops: list[str] = ["BT", "/F1 11 Tf", "72 720 Td"]
    for i, line in enumerate(lines):
        if i > 0:
            ops.append("0 -16 Td")
        ops.append(f"({_escape_pdf_text(line)}) Tj")
    ops.append("ET")
    stream_inner = "\n".join(ops).encode("latin-1", errors="replace")

    stream_dict = f"<< /Length {len(stream_inner)} >>\n".encode() + b"stream\n" + stream_inner + b"\nendstream"

    bodies = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        stream_dict,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    pieces: list[bytes] = [header]
    offsets: list[int] = [0]

    pos = len(header)
    for i, body in enumerate(bodies, start=1):
        offsets.append(pos)
        chunk = f"{i} 0 obj\n".encode("ascii") + body + b"\nendobj\n"
        pieces.append(chunk)
        pos += len(chunk)

    xref_pos = pos
    xref = [b"xref\n", f"0 {len(bodies)+1}\n".encode("ascii"), b"0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("ascii"))
    pieces.extend(xref)
    pieces.append(
        f"trailer\n<< /Size {len(bodies)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )

    out.write_bytes(b"".join(pieces))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

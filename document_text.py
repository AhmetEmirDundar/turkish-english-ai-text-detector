"""Yerel belgelerden analiz edilebilir metni çıkarır."""
from io import BytesIO
from zipfile import ZipFile

MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".pptx"}


def excel_text(data, extension):
    if extension == ".xls":
        import xlrd

        with xlrd.open_workbook(file_contents=data, on_demand=True, ragged_rows=True) as book:
            for index in range(book.nsheets):
                sheet = book.sheet_by_index(index)
                if sheet.visibility == 0:
                    for row in sheet.get_rows():
                        yield from (cell.value for cell in row if cell.ctype == xlrd.XL_CELL_TEXT)
                book.unload_sheet(index)
        return

    from openpyxl import load_workbook

    book = load_workbook(BytesIO(data), read_only=True, data_only=True, keep_links=False)
    try:
        for sheet in book.worksheets:
            if sheet.sheet_state == "visible":
                sheet.reset_dimensions()
                for row in sheet.iter_rows():
                    yield from (cell.value for cell in row if cell.data_type in {"s", "str", "inlineStr"})
    finally:
        book.close()


def slide_text(shapes):
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from slide_text(shape.shapes)
        elif shape.has_text_frame:
            yield shape.text.replace("\v", "\n")
        elif shape.has_table:
            for cell in shape.table.iter_cells():
                if not cell.is_spanned:
                    yield cell.text.replace("\v", "\n")


def extract_document(data, extension, max_chars=None):
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("Belge dosyaları en fazla 20 MB olabilir.")
    if extension not in DOCUMENT_EXTENSIONS:
        raise ValueError("PDF, Word, Excel veya PowerPoint dosyası seç.")

    try:
        if extension in {".docx", ".xlsx", ".pptx"}:
            with ZipFile(BytesIO(data)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 100 * 1024 * 1024:
                    raise DocumentError("Belgenin açılmış boyutu 100 MB sınırını aşıyor.")
        if extension == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise DocumentError("PDF parola korumalı. Parolasız bir kopyasını yükle.")
            parts = (page.extract_text() for page in reader.pages)
        elif extension == ".docx":
            from docx import Document
            from docx.text.paragraph import Paragraph

            document = Document(BytesIO(data))
            # Tablo hücrelerindeki paragraflar da belgedeki sırayla okunur.
            parts = (Paragraph(p, document).text for p in document.element.body.xpath(".//w:p"))
        elif extension == ".pptx":
            from pptx import Presentation

            slides = Presentation(BytesIO(data)).slides
            parts = (text for slide in slides for text in slide_text(slide.shapes))
        else:
            parts = excel_text(data, extension)

        lines = []
        length = 0
        for part in parts:
            if part and part.strip():
                length += len(part) + bool(lines)
                if max_chars is not None and length > max_chars:
                    raise DocumentError("En fazla 100.000 karakter yüklenebilir.")
                lines.append(part)
    except DocumentError:
        raise
    except ImportError as exc:
        raise RuntimeError("Belge okuyucusu eksik. Projenin requirements.txt paketlerini kur.") from exc
    except Exception as exc:
        raise ValueError("Belge okunamadı. Dosyanın açılabildiğini ve biçimini kontrol et.") from exc

    if not lines:
        if extension == ".pdf":
            raise ValueError("PDF içinde okunabilir metin bulunamadı. Taranmış belgeler için önce OCR ile metin tanıma uygula.")
        if extension in {".xls", ".xlsx"}:
            raise ValueError("Excel dosyasının görünür sayfalarında metin içeren hücre bulunamadı.")
        if extension == ".pptx":
            raise ValueError("PowerPoint slaytlarında okunabilir metin bulunamadı.")
        raise ValueError("Word belgesinde okunabilir metin bulunamadı.")
    return "\n".join(lines)


class DocumentError(ValueError):
    """Belgeyi yükleyen kişiye gösterilecek hata."""

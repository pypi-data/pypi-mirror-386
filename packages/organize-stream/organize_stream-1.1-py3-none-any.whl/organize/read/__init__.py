#!/usr/bin/env python3
from __future__ import annotations
import os.path
from io import BytesIO

from convert_stream.mod_types.table_types import (
    concat_maps, ColumnBody, ColumnsTable, create_map_from_values,
    create_map_from_file_values, TextTable,
)
from convert_stream import DocumentPdf, PageDocumentPdf
from convert_stream.pdf import ConvertPdfToImages
from convert_stream.image import ImageObject
from ocr_stream import RecognizeImage
from ocr_stream.bin_tess import BinTesseract
from ocr_stream.modules import LibOcr, DEFAULT_LIB_OCR
from soup_files import Directory, File, InputFiles, LibraryDocs, ProgressBarAdapter


class Ocr(RecognizeImage):
    _instance = None  # armazena a instância única

    def __new__(cls, bin_tess: BinTesseract = BinTesseract(), *, lib_ocr: LibOcr = DEFAULT_LIB_OCR):
        if cls._instance is None:
            # Cria a instância uma única vez
            cls._instance = super(Ocr, cls).__new__(cls)
        return cls._instance

    def __init__(self, bin_tess: BinTesseract = BinTesseract(), *, lib_ocr: LibOcr = DEFAULT_LIB_OCR):
        # Evita reexecutar __init__ em chamadas subsequentes
        if not hasattr(self, "_initialized"):
            super().__init__(bin_tess, lib_ocr=lib_ocr)
            self._initialized = True


def create_table_from_dict(data: dict[str, ColumnBody]) -> TextTable:
    _values: list[ColumnBody] = []
    for _k in data.keys():
        _values.append(data[_k])
    return TextTable(_values)


def recognize_images(
            images: list[ImageObject], *,
            ocr: Ocr = Ocr(),
            pbar: ProgressBarAdapter = ProgressBarAdapter()
        ) -> DocumentPdf:
    """
        Aplicar OCR em lista de imagens, e retornar um documento DocumentPdf() com as imagens embutidas.
    """
    pages_pdf: list[PageDocumentPdf] = []
    max_num: int = len(images)
    print()
    pbar.start()
    for _num, im in enumerate(images):
        pbar.update(
            ((_num + 1) / max_num) * 100,
            f'[OCR]: {_num + 1}/{max_num} {im.name}',
        )
        tmp_doc = ocr.image_recognize(im).to_document()
        pages_pdf.extend(tmp_doc.to_pages())
        del tmp_doc
    pbar.stop()
    print()
    return DocumentPdf.create_from_pages(pages_pdf)


def read_image(
            image: File | ImageObject | bytes | BytesIO, *, ocr: Ocr = Ocr(),
        ) -> dict[str, ColumnBody]:

    if isinstance(image, File):
        image: ImageObject = ImageObject(image)
    elif isinstance(image, ImageObject):
        pass
    elif isinstance(image, bytes):
        image: ImageObject = ImageObject.create_from_bytes(image)
    elif isinstance(image, BytesIO):
        image: ImageObject = ImageObject(image)
    else:
        raise ValueError('Use: File|DocumentPdf|bytes|ByesIO')

    txt = ocr.image_to_string(image)
    try:
        _values = txt.split('\n')
    except Exception as e:
        print(f'Error: {e}')
        _values = ['nan']

    if image.metadata['file_path'] is None:
        return create_map_from_values(_values, file_type='.png')
    else:
        return create_map_from_file_values(File(image.metadata['file_path']), _values)


def read_files_image(
            images_files: list[ImageObject], *,
            ocr: Ocr = Ocr(),
            pbar: ProgressBarAdapter = ProgressBarAdapter(),
        ) -> dict[str, ColumnBody]:
    """
        Ler as imagens de um diretório e retorna dict[str, ColumnBody]
    """
    list_table: list[dict[str, ColumnBody]] = []
    max_num: int = len(images_files)
    print()
    pbar.start()
    for _num, img in enumerate(images_files):
        pbar.update(
            ((_num + 1) / max_num) * 100,
            f'[OCR]: {_num + 1}/{max_num} {img.name}',
        )
        list_table.append(read_image(img, ocr=ocr))
    return concat_maps(list_table)


def read_directory_image(
            directory: Directory, *,
            ocr: Ocr = Ocr(),
            pbar: ProgressBarAdapter = ProgressBarAdapter(),
        ) -> list[TextTable]:
    """
        Ler as imagens de um diretório e retorna list[TextMap]
    """
    images_files: list[File] = InputFiles(directory).get_files(file_type=LibraryDocs.IMAGE)
    _data: list[TextTable] = []
    max_num: int = len(images_files)
    print()
    pbar.start()
    for _num, file_image in enumerate(images_files):
        pbar.update(
            ((_num + 1) / max_num) * 100,
            f'[OCR]: {_num + 1}/{max_num} {file_image.basename()}',
        )
        _data.append(
            create_table_from_dict(read_image(file_image, ocr=ocr))
        )
    return _data


def read_document_pdf(
            document: DocumentPdf,
            file_path: str,
            apply_ocr: bool = False,
            ocr: Ocr = Ocr(),
            pbar: ProgressBarAdapter = ProgressBarAdapter(),
        ) -> TextTable:
    """Extrair os textos de páginas PDF e retornar um objeto dict[str, ColumnBody]"""
    if not isinstance(document, DocumentPdf):
        raise TypeError(f'file_pdf dev ser DocumentPdf() não {type(file_pdf)}')
    if apply_ocr:
        conv = ConvertPdfToImages.create(document)
        images: list[ImageObject] = conv.to_images()
        document: DocumentPdf = recognize_images(images, ocr=ocr, pbar=pbar)
    tb = document.to_dict()
    max_num = len(tb[ColumnsTable.TEXT.value])
    tb[ColumnsTable.FILE_PATH.value] = ColumnBody(
        ColumnsTable.FILE_PATH.value, [file_path] * max_num
    )
    tb[ColumnsTable.DIR.value] = ColumnBody(
        ColumnsTable.DIR.value, [os.path.basename(file_path)] * max_num
    )
    tb[ColumnsTable.FILE_NAME.value] = ColumnBody(
        ColumnsTable.FILE_NAME.value, [os.path.basename(file_path)] * max_num
    )
    return create_table_from_dict(tb)


def read_file_pdf(
            file_pdf: File,
            apply_ocr: bool = False,
            ocr: Ocr = Ocr(),
            pbar: ProgressBarAdapter = ProgressBarAdapter(),
        ) -> TextTable:
    """Extrair os textos de páginas PDF e retornar um objeto TextMap()"""
    if not isinstance(file_pdf, File):
        raise TypeError(f'file_pdf dev ser File() não {type(file_pdf)}')
    tb = read_document_pdf(
        DocumentPdf(file_pdf), file_pdf.absolute(), ocr=ocr, pbar=pbar, apply_ocr=apply_ocr
    )
    return create_table_from_dict(tb)


def read_directory_pdf(
            directory: Directory, *,
            apply_ocr: bool = False,
            ocr: Ocr = Ocr(),
            pbar: ProgressBarAdapter = ProgressBarAdapter(),
        ) -> list[TextTable]:
    #
    files_doc_pdf: list[File] = InputFiles(directory).get_files(file_type=LibraryDocs.PDF)
    _text_maps: list[TextTable] = []
    for f_pdf in files_doc_pdf:
        _current_maps: dict[str, ColumnBody] = read_file_pdf(f_pdf, apply_ocr=apply_ocr, ocr=ocr, pbar=pbar)
        _text_maps.append(create_table_from_dict(_current_maps))
    return _text_maps


__all__ = [
    'Ocr', 'read_image', 'read_files_image', 'read_directory_image',
    'read_document_pdf', 'read_file_pdf', 'read_directory_pdf', 'create_table_from_dict'
]

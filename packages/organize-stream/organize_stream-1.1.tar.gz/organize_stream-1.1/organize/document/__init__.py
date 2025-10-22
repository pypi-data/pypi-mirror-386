#!/usr/bin/env python3
from __future__ import annotations
from typing import Union
from organize.find import DocumentFinder
from organize.read import (
    read_directory_pdf, read_directory_image, read_file_pdf, read_document_pdf,
    read_image, create_table_from_dict
)
from soup_files import File, Directory, ProgressBarAdapter, InputFiles, LibraryDocs
from convert_stream.mod_types.table_types import (
    ArrayString, TextTable, ColumnsTable, create_void_table, ColumnBody
)
from convert_stream import DocumentPdf
from convert_stream.image import ImageObject
import pandas as pd
import shutil

FindItem = Union[str, list[str]]

#  
_bad_chars: list[str] = [
    '.', '!', ':', '?', '(', ')', '{', '}',
    '+', '#', '@', '<', '>', '/', '¢', ':',
    ',', '®', '“'
]


def fmt_str_file(filename: str) -> str:
    for c in _bad_chars:
        filename = filename.replace(c, '')
    while '--' in filename:
        filename = filename.replace('--', '-')
    if len(filename) <= 80:
        return filename
    return filename[0:80]


def move_list_files(mv_items: dict[str, list[File]], *, replace: bool = False) -> None:
    total_file = len(mv_items['src'])
    for idx, file in enumerate(mv_items['src']):
        if not file.exists():
            print(f'[PULANDO]: {idx + 1} Arquivo não encontrado {file.absolute()}')
        if mv_items['dest'][idx].exists():
            if not replace:
                print(f'[PULANDO]: {idx+1} O arquivo já existe {mv_items["dest"][idx].absolute()}')
                continue
        print(f'Movendo: {idx+1}/{total_file} {file.absolute()}')
        try:
            shutil.move(file.absolute(), mv_items['dest'][idx].absolute())
        except Exception as e:
            print(f'{e}')


# Sujeito notificador
class NotifyProvider(object):

    def __init__(self):
        self.observers: list[Observer] = []

    def add_observer(self, observer) -> None:
        self.observers.append(observer)

    def send_notify(self, tb: TextTable) -> None:
        for obs in self.observers:
            obs.receive_notify(tb)


# Sujeito Observador.
class Observer(object):

    def __init__(self):
        pass

    def receive_notify(self, notify: TextTable) -> None:
        pass


class FilterText(object):
    def __init__(
                self,
                find_txt: str,
                out_dir: Directory, *,
                separator: str = ' ',
                case: bool = False,
                iqual: bool = False
            ):
        self.find_txt: str = find_txt
        self.out_dir: Directory = out_dir
        self.case: bool = case
        self.iqual: bool = iqual
        self.separator: str = separator


class DocumentTextExtract(NotifyProvider):
    """
        Extrair texto de arquivos, e converter em Excel/DataFrame
    """

    def __init__(self):
        super().__init__()
        self.tb_list: list[TextTable] = []
        self.pbar: ProgressBarAdapter = ProgressBarAdapter()
        self.__count: int = 0

    @property
    def is_empty(self) -> bool:
        return len(self.tb_list) == 0

    @property
    def finder(self) -> DocumentFinder:
        return DocumentFinder(self.tb_list)

    def add_table(self, tb: TextTable) -> None:
        self.tb_list.append(tb)
        self.send_notify(tb)
        self.__count += 1
        print(f'{__class__.__name__} Tabela adicionada: {self.__count}')

    def add_directory_pdf(self, dir_pdf: Directory, *, apply_ocr: bool = False):
        files_pdf = InputFiles(dir_pdf).get_files(file_type=LibraryDocs.PDF)
        for f in files_pdf:
            tb = read_file_pdf(f, apply_ocr=apply_ocr, pbar=self.pbar)
            self.add_table(tb)

    def add_directory_image(self, dir_image: Directory):
        files_images = InputFiles(dir_image).get_files(file_type=LibraryDocs.IMAGE)
        for f in files_images:
            tb: TextTable = create_table_from_dict(read_image(f))
            self.add_table(tb)

    def add_file_pdf(self, file_pdf: File, apply_ocr: bool = False):
        tb = read_file_pdf(file_pdf, pbar=self.pbar, apply_ocr=apply_ocr)
        self.add_table(tb)

    def add_file_image(self, file_image: File):
        tb: TextTable = create_table_from_dict(read_image(file_image))
        self.add_table(create_table_from_dict(tb))

    def add_image(self, image: ImageObject):
        if not isinstance(image, ImageObject):
            raise TypeError('Image must be an ImageObject')
        _tb: TextTable = create_table_from_dict(read_image(image))
        self.add_table(_tb)

    def add_document(self, document: DocumentPdf, *, apply_ocr: bool = False):
        self.add_table(
            read_document_pdf(document, document.metadata['file_path'], pbar=self.pbar, apply_ocr=apply_ocr)
        )

    def to_data(self) -> pd.DataFrame:
        if len(self.tb_list) == 0:
            return create_void_table()
        
        _data: list[pd.DataFrame] = []
        for m in self.tb_list:
            _data.append(pd.DataFrame.from_dict(m))
        return pd.concat(_data).astype('str')
       
    def to_excel(self, file: File) -> None:
        self.to_data().to_excel(file.absolute(), index=False)


class OrganizeOnFilter(Observer):

    def __init__(self, filter_text: FilterText):
        super().__init__()
        self.filter: FilterText = filter_text
        self.__count: int = 0

    def receive_notify(self, notify: TextTable) -> None:
        self.__count += 1
        print(f'{__class__.__name__} notificação recebida {self.__count}')
        self.move_where_math_text(notify)

    def move_where_math_text(self, tb: TextTable) -> None:
        """

        """
        file_txt: ColumnBody = tb[ColumnsTable.TEXT.value]
        arr = ArrayString(file_txt)
        _idx = arr.find_index(self.filter.find_txt, iqual=self.filter.iqual, case=self.filter.case)
        if _idx is None:
            return
        src_path = File(tb[ColumnsTable.FILE_PATH.value][_idx])
        txt = arr[_idx:]
        new_name = fmt_str_file(self.filter.separator.join(txt))
        new_path = self.filter.out_dir.join_file(f'{new_name}{src_path.extension()}')
        mv_items: dict[str, list[File]] = {
            'src': [src_path],
            'dest': [new_path],
        }
        move_list_files(mv_items)


class OrganizeDocuments(object):

    def __init__(self, table_files: pd.DataFrame):
        super().__init__()
        self.table_files: pd.DataFrame = table_files
        self.pbar: ProgressBarAdapter = ProgressBarAdapter()

    def move_where_contains_text(
                self,
                find_txt: str,
                out_dir: Directory, *,
                case: bool = False,
                iqual: bool = False
            ) -> None:
        """
            Mover arquivos conforme as ocorrências de texto encontradas nos documentos.
        O arquivo é movido de diretório quando determinada ocorrência é encontrada, preservando
        o nome original.
        """
        df = self.table_files[[ColumnsTable.TEXT.value, ColumnsTable.FILE_PATH.value]].astype('str')
        mv_items: dict[str, list[File]] = {'src': [], 'dest': []}

        if case:
            if iqual:
                for idx, row in df.iterrows():
                    txt_in_file = f'{row[ColumnsTable.TEXT.value]}'
                    if find_txt == txt_in_file:
                        src_file = File(f'{row[ColumnsTable.FILE_PATH.value]}')
                        dest_file = out_dir.join_file(src_file.basename())
                        mv_items['src'].append(src_file)
                        mv_items['dest'].append(dest_file)
            else:
                for idx, row in df.iterrows():
                    txt_in_file = f'{row[ColumnsTable.TEXT.value]}'
                    if find_txt in txt_in_file:
                        src_file = File(f'{row[ColumnsTable.FILE_PATH.value]}')
                        dest_file = out_dir.join_file(src_file.basename())
                        mv_items['src'].append(src_file)
                        mv_items['dest'].append(dest_file)
        else:
            if iqual:
                for idx, row in df.iterrows():
                    txt_in_file = f'{row[ColumnsTable.TEXT.value]}'
                    if find_txt.upper() == txt_in_file.upper():
                        src_file = File(f'{row[ColumnsTable.FILE_PATH.value]}')
                        dest_file = out_dir.join_file(src_file.basename())
                        mv_items['src'].append(src_file)
                        mv_items['dest'].append(dest_file)
            else:
                for idx, row in df.iterrows():
                    txt_in_file = f'{row[ColumnsTable.TEXT.value]}'
                    if find_txt.upper() in txt_in_file.upper():
                        src_file = File(f'{row[ColumnsTable.FILE_PATH.value]}')
                        dest_file = out_dir.join_file(src_file.basename())
                        mv_items['src'].append(src_file)
                        mv_items['dest'].append(dest_file)
        move_list_files(mv_items)

    def move_where_math_text(
                self,
                find_txt: str,
                out_dir: Directory, *,
                separator: str = ' ',
                include_all_text: bool = False,
            ) -> None:
        """
            Mover arquivos conforme as ocorrências de texto encontradas nos documentos.
        O arquivo é movido de diretório quando determinada ocorrência é encontrada, preservando
        o nome original.
        """
        values_text = self.table_files[ColumnsTable.TEXT.value].astype('str').values.tolist()
        values_files = self.table_files[ColumnsTable.FILE_PATH.value].astype('str').values.tolist()
        mv_items: dict[str, list[File]] = {'src': [], 'dest': []}

        for idx, txt_in_file in enumerate(values_text):

            if find_txt.upper() in txt_in_file.upper():
                src_file = File(values_files[idx])
                # filtrar a string apagando os caracteres que antecedem o padrão informado.
                try:
                    arr = ArrayString(txt_in_file.split(separator))
                    if not include_all_text:
                        new_file_name = arr.get_next(find_txt)
                    else:
                        new_file_name = arr.get_next_all(find_txt)
                        if len(new_file_name) == 0:
                            print(f'{__class__.__name__} Falha ao obter filename')
                            continue
                        elif len(new_file_name) == 1:
                            new_file_name = new_file_name[0]
                        else:
                            new_file_name = separator.join(new_file_name)
                except Exception as e:
                    print(e)
                else:
                    if new_file_name is None:
                        print(f'{__class__.__name__} Falha, filename is None')
                        continue
                    new_file_name = fmt_str_file(new_file_name)
                    mv_items['src'].append(src_file)
                    mv_items['dest'].append(out_dir.join_file(f'{new_file_name}{src_file.extension()}'))
        move_list_files(mv_items)

    def move_where_math_column(
                self,
                df: pd.DataFrame,
                out_dir: Directory, *,
                col_find: str,
                col_new_name: str,
                cols_in_name: list[str] = [],
            ) -> None:
        """
            Mover arquivos conforme as ocorrências de texto encontradas na tabela/DataFrame df.
        o nome do novo arquivo será igual à ocorrência de texto da coluna 'col_find', podendo
        estender o nome com elementos de outras colunas, tais colunas podem ser informadas (opcionalmente)
        no parâmetro cols_in_name.
            Ex:
        Suponha que a tabela para renomear aquivos tenha a seguinte estrutura:

        A      B        C
        maça   Cidade 1 xxyyy
        banana Cidade 2 yyxxx
        mamão  Cidade 3 xyxyx

        Se passarmos os parâmetros col_find='A' e col_new_name='A' e o texto banana for
        encontrado no(s) documento, o novo nome do arquivo será banana. Caso incluir o parâmetro
        cols_in_name=['B'] o novo nome do arquivo será banana-Cidade 2 ou
        banana-Cidade 2-yyxxx (se incluir cols_in_name=['B', 'C']).

        """
        list_values_find = df[col_find].astype('str').values.tolist()
        list_values_new_name = df[col_new_name].astype('str').values.tolist()

        text_in_docs = self.table_files[ColumnsTable.TEXT.value].astype('str').values.tolist()
        text_file_names = self.table_files[ColumnsTable.FILE_PATH.value].astype('str').values.tolist()
        mv_items: dict[str, list[File]] = {'src': [], 'dest': []}

        cols_include_names: list[list[str]] = []
        if len(cols_in_name) > 0:
            for c in cols_in_name:
                values_include: list[str] = df[c].astype('str').values.tolist()
                cols_include_names.append(values_include)

        for num, txt in enumerate(list_values_find):
            for num_idx, txt_doc in enumerate(text_in_docs):
                if txt in txt_doc:
                    src_file = File(text_file_names[num_idx])
                    output_file = list_values_new_name[num]
                    if len(cols_in_name) > 0:
                        new = ''
                        for element in cols_include_names:
                            new = f'{new}-{element[num]}'
                        output_file = f'{output_file}-{new}'
                    output_file = fmt_str_file(output_file)
                    mv_items['src'].append(src_file)
                    mv_items['dest'].append(out_dir.join_file(f'{output_file}{src_file.extension()}'))
        move_list_files(mv_items)

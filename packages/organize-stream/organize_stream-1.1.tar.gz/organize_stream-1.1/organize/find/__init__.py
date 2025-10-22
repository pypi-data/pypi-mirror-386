#!/usr/bin/env python3

from __future__ import annotations
import pandas as pd
from soup_files import File, JsonConvert
from convert_stream.mod_types.table_types import (
    ColumnsTable, HeadCell, HeadValues, ColumnBody, TextTable, ArrayString, create_void_map
)


class SearchableText(object):

    default_elements: dict[str, ColumnBody] = create_void_map()
    default_columns: HeadValues = HeadValues([HeadCell(x) for x in list(default_elements.keys())])

    def __init__(self):
        self.elements: dict[str, ColumnBody] = create_void_map()

    def __repr__(self):
        return f'SearchableText\nHead: {self.head}\nBody: {self.body}'

    def is_empty(self) -> bool:
        return len(self.elements[HeadCell(ColumnsTable.TEXT.value)]) == 0

    @property
    def head(self) -> HeadValues:
        return HeadValues([HeadCell(x) for x in list(self.elements.keys())])

    @property
    def body(self) -> list[ColumnBody]:
        return [ColumnBody(HeadCell(_k), self.elements[_k]) for _k in self.elements.keys()]

    @property
    def first(self) -> dict[str, str]:
        if self.is_empty():
            return {}
        cols: HeadValues = self.head
        _first = {}
        for col in cols:
            _first[col] = self.elements[col][0]
        return _first

    @property
    def last(self) -> dict[str, str]:
        if self.is_empty():
            return {}
        cols = self.head
        _last = {}
        for col in cols:
            _last[col] = self.elements[col][-1]
        return _last

    @property
    def length(self) -> int:
        return len(self.elements[HeadCell(ColumnsTable.TEXT.value)])

    @property
    def files(self) -> ColumnBody:
        return self.elements[HeadCell(ColumnsTable.FILE_PATH.value)]

    def get_item(self, idx: int) -> dict[str, str]:
        cols: HeadValues = self.head
        try:
            _item = {}
            for col in cols:
                _item[col] = self.elements[col][idx]
            return _item
        except Exception as err:
            print(err)
            return {}

    def get_column(self, name: str) -> ColumnBody:
        return self.elements[HeadCell(name)]

    def add_line(self, line: dict[str, str]) -> None:
        cols_line: HeadValues = HeadValues([HeadCell(x) for x in list(line.keys())])
        cols_origin: HeadValues = self.head
        for col in cols_origin:
            if cols_line.contains(col, case=True, iqual=True):
                self.elements[col].append(line[col])

    def clear(self) -> None:
        for _k in self.elements.keys():
            self.elements[_k].clear()

    def to_string(self) -> str:
        """
            Retorna o texto da coluna TEXT em formato de string
        ou 'nas' em caso de erro nas = Not a String
        """
        try:
            return ' '.join(self.elements[HeadCell(ColumnsTable.TEXT.value)])
        except Exception as e:
            print(e)
            return 'nan'

    def to_data_frame(self) -> pd.DataFrame:
        return pd.DataFrame.from_dict(self.elements)

    def to_file_json(self, file: File):
        """Exporta os dados da busca para arquivo .JSON"""
        dt = JsonConvert.from_dict(self.elements).to_json_data()
        dt.to_file(file)

    def to_file_excel(self, file: File):
        """Exporta os dados da busca para arquivo .XLSX"""
        self.to_data_frame().to_excel(file.absolute(), index=False)

    @classmethod
    def create(cls, df: pd.DataFrame):
        cols: list[str] = df.columns.tolist()
        tb = {}
        for col in cols:
            tb[HeadCell(col)] = ColumnBody(col, df[col])
        s = cls()
        s.elements = tb
        return s


class DocumentFinder(object):

    def __init__(self, text_maps: list[TextTable]):
        self.text_maps: list[TextTable] = text_maps
        # Coluna que contem o texto usado como filtro em cada linha da busca
        self._col_name_filter: str = 'FILTRO'
        # Coluna que contem o texto de filtro adicional
        self._col_include_filter: str = 'FILTRO ADICIONAL'

    def add_table(self, item: TextTable) -> None:
        self.text_maps.append(item)

    def find(self, text: str, *, iqual: bool = False, case: bool = False) -> SearchableText:
        _data = []
        s = SearchableText()
        for text_map in self.text_maps:
            arr = ArrayString(text_map[ColumnsTable.TEXT.value])
            _current_idx: int | None = arr.find_index(text, iqual=iqual, case=case)
            if _current_idx is not None:
                new_line = {
                    ColumnsTable.KEY.value: text_map[ColumnsTable.KEY.value][_current_idx],
                    ColumnsTable.NUM_PAGE.value: text_map[ColumnsTable.NUM_PAGE.value][_current_idx],
                    ColumnsTable.NUM_LINE.value: text_map[ColumnsTable.NUM_LINE.value][_current_idx],
                    ColumnsTable.TEXT.value: text_map[ColumnsTable.TEXT.value][_current_idx],
                    ColumnsTable.FILETYPE.value: text_map[ColumnsTable.FILETYPE.value][_current_idx],
                    ColumnsTable.FILE_PATH.value: text_map[ColumnsTable.FILE_PATH.value][_current_idx],
                    ColumnsTable.DIR.value: text_map[ColumnsTable.DIR.value][_current_idx],
                }
                s.add_line(new_line)
                break
        return s

    def find_all(self, text: str, iqual: bool = False, case: bool = False) -> SearchableText:
        _data = []
        s = SearchableText()
        for current_tb in self.text_maps:
            arr = ArrayString(current_tb[ColumnsTable.TEXT.value])
            _current_idx = arr.find_index(text, iqual=iqual, case=case)
            if _current_idx is not None:
                new_line = {
                    ColumnsTable.KEY.value: current_tb[ColumnsTable.KEY.value][_current_idx],
                    ColumnsTable.NUM_PAGE.value: current_tb[ColumnsTable.NUM_PAGE.value][_current_idx],
                    ColumnsTable.NUM_LINE.value: current_tb[ColumnsTable.NUM_LINE.value][_current_idx],
                    ColumnsTable.TEXT.value: current_tb[ColumnsTable.TEXT.value][_current_idx],
                    ColumnsTable.FILETYPE.value: current_tb[ColumnsTable.FILETYPE.value][_current_idx],
                    ColumnsTable.FILE_PATH.value: current_tb[ColumnsTable.FILE_PATH.value][_current_idx],
                    ColumnsTable.DIR.value: current_tb[ColumnsTable.DIR.value][_current_idx],
                }
                s.add_line(new_line)
        return s

    def find_from_data(self, df: pd.DataFrame, *, col_filter: str, col_new_filter: str = None) -> SearchableText:
        """
            Filtrar vários textos em documentos/arquivos, incluindo dois tipos de filtros simultaneos.

        :df: DataFrame com os textos a serem usados como filtro apartir da coluna indicada
        :col_filter: string da coluna que contém os textos a serem filtrados
        :col_new_filter: string da coluna que contém um filtro adicional (opcional)

        @type df: pd.DataFrame
        @type col_filter: str
        @type col_new_filter: str
        @rtype: SearchableText
        """
        if col_new_filter is not None:
            df = df[[col_filter, col_new_filter]].dropna(subset=[col_filter]).astype('str')
        else:
            df = df[[col_filter]].dropna(subset=[col_filter]).astype('str')

        list_data: list[pd.DataFrame] = []
        for i, row in df.iterrows():
            _searchable = self.find_all(f'{row[col_filter]}').to_data_frame()
            if not _searchable.empty:
                if col_new_filter is not None:
                    new_searchable = self.find_all(f'{row[col_new_filter]}').to_data_frame()
                    if not new_searchable.empty:
                        _searchable = pd.concat([_searchable, new_searchable])
                        _searchable[self._col_name_filter] = [row[col_filter]] * len(_searchable)
                        _searchable[self._col_include_filter] = [row[col_new_filter]] * len(_searchable)
                    else:
                        _searchable[self._col_name_filter] = [row[col_filter]] * len(_searchable)
                        _searchable[self._col_include_filter] = ['nan'] * len(_searchable)
                else:
                    _searchable[self._col_name_filter] = [row[col_filter]] * len(_searchable)
                    _searchable[self._col_include_filter] = ['nan'] * len(_searchable)
                list_data.append(_searchable)

        if len(list_data) > 0:
            return SearchableText.create(pd.concat(list_data))
        return SearchableText()

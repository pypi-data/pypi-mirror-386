from ..enums import ResponseFormat, DynamicDate, CorporateActionType, BooleanString
from typing import Union, Optional, Any, Dict


from ..enums import ResponseFormat, DynamicDate, CorporateActionType, BooleanString
from typing import Union, Optional, Any, Dict

class DataPack:

    def __init__(self, core):
        self._core = core

    # ---------------------------------------------------------------------
    # Helpers internos
    # ---------------------------------------------------------------------
    def _normalize_value(self, value: Any):
        """Converte enums (ResponseFormat, DynamicDate, BooleanString, CorporateActionType)
        para seus valores primitivos. Mantém outros tipos inalterados."""
        if isinstance(value, (ResponseFormat, DynamicDate, BooleanString, CorporateActionType)):
            return value.value
        return value

    def _prepare_params(self, **kwargs) -> Dict[str, Any]:
        """Remove chaves cujo valor é None e normaliza enums/datas dinâmicas."""
        clean: Dict[str, Any] = {}
        for k, v in kwargs.items():
            if v is None:
                continue
            clean[k] = self._normalize_value(v)
        return clean

    def _request_endpoint(self, endpoint: str, **kwargs):
        """Encapsula chamada ao método genérico do core para endpoints DataPack.

        Args:
            endpoint (str): Nome do endpoint (ex: 'getFX').
            **kwargs: Parâmetros específicos do endpoint.
        """
        params = self._prepare_params(**kwargs)

        return self._core._BDSCore__make_request(
            self._core.datapack_url,
            endpoint,
            **params
        )
    # Débito Técnico: Implementação manual do método getTradeInformation direto no UP2DATA. Deve-se implementar uma API BDS para este método futuramente.
    def getTradeInformation(self, symbol: str = ":all", instrumentType: str = None, referencedate: str = None):
        """
        Busca o último arquivo Trade_FixedIncome para o tipo (CRA, CRI, DEB) e data informada, consome via SAS e retorna BDSResult.
        Aceita referencedate como YYYYMMDD, YYYY-MM-DD ou dinâmico (D-1, D+1, C-1, ...).
        Permite filtrar o array de objetos retornado pelo blob por qualquer campo, ex: TckrSymb:25H2095950 ou ISIN:XYZ.
        Se symbol=":all" (default), retorna todos os registros sem filtro.
        """
        import requests
        import re
        import time
        import xml.etree.ElementTree as ET
        from ..result import BDSResult

        if not instrumentType or instrumentType.upper() not in {"CRI", "CRA", "DEB"}:
            raise ValueError(
                f"O parâmetro 'instrumentType' deve ser um dos valores permitidos: CRI, CRA ou DEB. Valor recebido: '{instrumentType}'. "
                "Consulte a documentação do método getTradeInformation para detalhes."
            )

        # Resolve referencedate
        refdate = referencedate
        if isinstance(refdate, str) and ('+' in refdate or '-' in refdate):
            from .common import Common
            common = Common(self._core)
            base_date = getattr(common._core, 'reference_date', None)
            if not base_date:
                import datetime
                base_date = datetime.date.today().strftime('%Y-%m-%d')
            result = common.decodeDynamicDate(ReferenceDate=base_date, DynamicDates=refdate).data.to_dict()
            refdate = result[0]['date'].replace('-', '')
        else:
            if isinstance(refdate, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", refdate):
                refdate = refdate.replace('-', '')

        # Obtém SAS via API externa validando api_key
        sas_api_url = "https://prod-88.eastus.logic.azure.com:443/workflows/ae939630c3b547eca6cd3c552962eaf7/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=tuNC_HFgksiyJp0bG1NPygC_X6y9suvIrd_QcLtUWfI"
        api_key = getattr(self._core, 'api_key', None)
        if not api_key:
            raise ValueError('api_key não encontrada no core')
        headers = {"BDSKey": api_key}
        sas_resp = requests.post(sas_api_url, headers=headers)
        sas_resp.raise_for_status()
        sas_dict = sas_resp.json()
        instrumentType_lower = instrumentType.lower()
        if instrumentType_lower not in sas_dict:
            raise ValueError(f"SAS para o símbolo '{instrumentType}' não encontrada na resposta da API")
        sas_url = sas_dict[instrumentType_lower]

        prefix = f"{refdate}/Trade_FixedIncome/{instrumentType}/Trade_FixedIncome_TradeOTCFile_{instrumentType}_{refdate}_"
        list_url = sas_url.split('?')[0] + f"?restype=container&comp=list&prefix={refdate}/Trade_FixedIncome/{instrumentType}/"
        if '?' in sas_url:
            list_url += '&' + sas_url.split('?',1)[1]
        resp = requests.get(list_url)
        resp.raise_for_status()
        tree = ET.fromstring(resp.text)
        blobs = [b.find('Name').text for b in tree.findall('.//Blob') if b.find('Name') is not None]
        files = [b for b in blobs if b.startswith(prefix) and b.endswith('.json')]
        if not files:
            raise FileNotFoundError(f"Nenhum arquivo encontrado para {instrumentType} em {refdate}")
        def extract_counter(fname):
            try:
                return int(fname.split('_')[-1].replace('.json',''))
            except Exception:
                return -1
        last_file = max(files, key=extract_counter)

        blob_url = sas_url.split('?')[0] + '/' + last_file
        if '?' in sas_url:
            blob_url += '?' + sas_url.split('?',1)[1]
        start = time.time()
        file_resp = requests.get(blob_url)
        file_resp.raise_for_status()
        data = file_resp.json()
        duration = time.time() - start

        # Aplica filtro genérico se fornecido
        if symbol == ":all":
            symbol = None
        if symbol and isinstance(data, list):
            if ':' in symbol:
                field, value = symbol.split(':', 1)
                data = [item for item in data if str(item.get(field)) == value]
            else:
                # Se não especificar campo, filtra por TckrSymb
                value = symbol
                data = [item for item in data if str(item.get('TckrSymb')) == value]

        return BDSResult(
            api_url=blob_url,
            body=data,
            headers=dict(file_resp.headers),
            status_code=file_resp.status_code,
            call_duration=duration
        )

    # ====================================
    # MÉTODOS DE MERCADO FINANCEIRO
    # ====================================

    def getFX(self, Symbols, InitialDate, FinalDate: Optional[Union[str, DynamicDate]] = None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format: Optional[ResponseFormat] = None, IgnNull: Optional[BooleanString] = None, isActive=None):
        """
        Obtém dados de câmbio e moedas estrangeiras.
        
        Args:
            Symbols (str): Símbolos das moedas para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str | DynamicDate): Data final da consulta (opcional)
                                         Aceita datas dinâmicas: DynamicDate.YESTERDAY, DynamicDate.LAST_BUSINESS_DAY, etc.
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (ResponseFormat): Formato de retorno (default: ResponseFormat.JSON)
                                   Opções: ResponseFormat.JSON, ResponseFormat.XML, ResponseFormat.CSV, ResponseFormat.EXCEL
            IgnNull (BooleanString): Se deve retornar valores nulos (default: BooleanString.FALSE)
                                   Opções: BooleanString.TRUE, BooleanString.FALSE
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de câmbio para os símbolos especificados
        """
        return self._request_endpoint(
            "getFX",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getEquitiesB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de ações negociadas na B3 (Bolsa de Valores do Brasil).
        
        Args:
            Symbols (str): Símbolos das ações para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de ações da B3 para os símbolos especificados
        """
        return self._request_endpoint(
            "getEquitiesB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getBrazilianTreasury(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados cadastrais e de valores de títulos públicos brasileiros (LFT, LTN, NTN-B, NTN-C, NTN-F).
        
        Args:
            Symbols (str): Símbolos dos títulos públicos para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de títulos do Tesouro Nacional
        """
        return self._request_endpoint(
            "getBrazilianTreasury",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getCommodities(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de commodities negociadas no mercado internacional.
        
        Args:
            Symbols (str): Símbolos das commodities para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de commodities para os símbolos especificados
        """
        return self._request_endpoint(
            "getCommodities",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getIndex(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de índices financeiros internacionais.
        
        Args:
            Symbols (str): Símbolos dos índices para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de índices financeiros
        """
        return self._request_endpoint(
            "getIndex",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getIndexB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de índices negociados na B3 (ex: Ibovespa, IBrX-100, etc.).
        
        Args:
            Symbols (str): Símbolos dos índices B3 para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de índices da B3
        """
        return self._request_endpoint(
            "getIndexB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getIndexPortfolioB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de portfólio dos índices negociados na B3.
        
        Args:
            Symbols (str): Símbolos dos índices para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de portfólio dos índices B3
        """
        return self._request_endpoint(
            "getIndexPortfolioB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    # ====================================
    # MÉTODOS DE DERIVATIVOS E FUTUROS
    # ====================================

    def getFuturesB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de contratos futuros negociados na B3.
        
        Args:
            Symbols (str): Símbolos dos futuros para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de contratos futuros da B3
        """
        return self._request_endpoint(
            "getFuturesB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getFuturesCME(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de contratos futuros negociados na CME (Chicago Mercantile Exchange).
        
        Args:
            Symbols (str): Símbolos dos futuros CME para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de contratos futuros da CME
        """
        return self._request_endpoint(
            "getFuturesCME",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getCMEAgricFutures(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de futuros agrícolas negociados na CME.
        
        Args:
            Symbols (str): Símbolos dos futuros agrícolas para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de futuros agrícolas da CME
        """
        return self._request_endpoint(
            "getCMEAgricFutures",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getCMEFuturesCommodities(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de futuros de commodities negociados na CME.
        
        Args:
            Symbols (str): Símbolos dos futuros de commodities para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de futuros de commodities da CME
        """
        return self._request_endpoint(
            "getCMEFuturesCommodities",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getFuturesOptionsB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de opções sobre futuros negociadas na B3.
        
        Args:
            Symbols (str): Símbolos das opções sobre futuros para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de opções sobre futuros da B3
        """
        return self._request_endpoint(
            "getFuturesOptionsB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    def getOptionsOnEquitiesB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
        """
        Obtém dados de opções sobre ações negociadas na B3.
        
        Args:
            Symbols (str): Símbolos das opções sobre ações para consulta (obrigatório)
            InitialDate (str): Data inicial da consulta (obrigatório)
            FinalDate (str): Data final da consulta (opcional)
            Fields (str): Campos específicos a retornar
            Interval (str): Intervalo dos dados
            IgnDefault (str): Ignorar valores padrão
            Lang (str): Idioma da resposta
            Page (int): Número da página
            Rows (int): Quantidade de linhas por página
            Format (str): Formato de retorno (default: "Json")
            IgnNull (str): Se deve retornar valores nulos (default: "False")
            isActive (str): Filtrar apenas símbolos ativos
            
        Returns:
            dict: Dados de opções sobre ações da B3
        """
        return self._request_endpoint(
            "getOptionsOnEquitiesB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            Interval=Interval,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull,
            isActive=isActive
        )

    # ====================================
    # MÉTODOS DE EVENTOS CORPORATIVOS 
    # ====================================

    def getAdjQuoteHistory(self, Symbols, InitialDate, FinalDate: Optional[Union[str, DynamicDate]] = None, NominalValue: Optional[bool] = None, MissingValues: Optional[bool] = None, Page: Optional[int] = None, Rows: Optional[int] = None, Format: Optional[ResponseFormat] = None):
        """
        Retorna o histórico completo de cotações ajustadas aos proventos de um ativo específico.
        
        Este endpoint fornece preços de abertura, fechamento, máximo, mínimo, volume negociado e 
        fatores de ajuste aplicados devido a eventos corporativos como dividendos, splits, bonificações, etc.
        
        Args:
            Symbols (str): Código de identificação do ativo na bolsa de valores (ticker symbol) (obrigatório)
                          Exemplos: PETR4 (Petrobras PN), VALE3 (Vale ON), ITUB4 (Itaú Unibanco PN)
            InitialDate (str): Data de início do período para consulta no formato YYYY-MM-DD (ISO 8601) (obrigatório)
                              Aceita datas dinâmicas: DynamicDate.YESTERDAY, DynamicDate.LAST_BUSINESS_DAY, DynamicDate.FIRST_BUSINESS_DAY_PREV_MONTH
            FinalDate (str | DynamicDate): Data de fim do período para consulta no formato YYYY-MM-DD (ISO 8601) (opcional)
                           Se não informado: retorna dados apenas da data inicial
            NominalValue (bool): Define se os valores nominais (não ajustados) devem ser incluídos na resposta (opcional)
                               True: retorna valores ajustados + nominais para comparação
                               False: apenas valores ajustados (padrão)
            MissingValues (bool): Define se deve preencher dados ausentes com valores específicos (opcional)
                                Útil para análises que requerem continuidade temporal (padrão: False)
            Page (int): Número da página para paginação dos resultados (opcional)
                       Inicia em 1, se não informado: retorna a primeira página
            Rows (int): Quantidade máxima de registros por página (opcional)
                       Máximo geral: 1.000 registros, Formato Excel: automaticamente ajustado para 10.000 registros
            Format (ResponseFormat): Formato de serialização da resposta da API (opcional)
                         Opções: ResponseFormat.JSON (padrão), ResponseFormat.XML, ResponseFormat.CSV, ResponseFormat.EXCEL
            
        Returns:
            BDSResult: Histórico de cotações ajustadas com preços corrigidos por proventos e eventos corporativos
                      Inclui preços ajustados, volumes, quantidades e fatores de correção aplicados
        """
        return self._request_endpoint(
            "getAdjQuoteHistory",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            NominalValue=NominalValue,
            MissingValues=MissingValues,
            Page=Page,
            Rows=Rows,
            Format=Format
        )

    def getCorporateActions(self, Symbols, InitialDate, FinalDate: Optional[Union[str, DynamicDate]] = None, EvtActnTpCd: Optional[CorporateActionType] = None, Page: Optional[int] = None, Rows: Optional[int] = None, Format: Optional[ResponseFormat] = None):
        """
        Retorna informações detalhadas sobre eventos corporativos de ativos listados na bolsa.
        
        Tipos de eventos corporativos incluem distribuição de proventos (dividendos, JCP, bonificações),
        alterações no capital (splits, grupamentos, incorporações), direitos de subscrição e outros eventos
        que afetam o preço e quantidade de ações.
        
        Args:
            Symbols (str): Código de identificação do ativo na bolsa de valores (ticker symbol) (obrigatório)
                          Exemplos: PETR4 (Petrobras PN), VALE3 (Vale ON), ITUB4 (Itaú Unibanco PN)
            InitialDate (str): Data de início do período para consulta no formato YYYY-MM-DD (ISO 8601) (obrigatório)
                              Aceita datas dinâmicas: DynamicDate.YESTERDAY, DynamicDate.LAST_BUSINESS_DAY, DynamicDate.FIRST_BUSINESS_DAY_PREV_MONTH
            FinalDate (str | DynamicDate): Data de fim do período para consulta no formato YYYY-MM-DD (ISO 8601) (opcional)
                           Se não informado: busca eventos apenas na data inicial
            EvtActnTpCd (CorporateActionType): Filtra por tipo específico de evento corporativo (opcional)
                              Códigos principais:
                              - CorporateActionType.DIVIDEND: Dividendo
                              - CorporateActionType.INTEREST_ON_EQUITY: Juros sobre Capital Próprio
                              - CorporateActionType.STOCK_SPLIT: Desdobramento (Split)
                              - CorporateActionType.STOCK_GROUPING: Grupamento
                              - CorporateActionType.INCORPORATION: Incorporação
                              - CorporateActionType.MERGER: Fusão
                              E muitos outros... (veja CorporateActionType para lista completa)
            Page (int): Número da página para paginação dos resultados (opcional)
                       Inicia em 1, se não informado: retorna a primeira página
            Rows (int): Quantidade máxima de registros por página (opcional)
                       Máximo geral: 1.000 registros, Formato Excel: automaticamente ajustado para 10.000 registros
            Format (ResponseFormat): Formato de serialização da resposta da API (opcional)
                         Opções: ResponseFormat.JSON (padrão), ResponseFormat.XML, ResponseFormat.CSV, ResponseFormat.EXCEL
            
        Returns:
            BDSResult: Lista de eventos corporativos com detalhes completos incluindo datas, valores, 
                      tipos de evento e informações societárias
        """
        return self._request_endpoint(
            "getCorporateActions",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            EvtActnTpCd=EvtActnTpCd,
            Page=Page,
            Rows=Rows,
            Format=Format
        )


    def getCurvesB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """Obtém dados de curvas (Curves B3)."""
        return self._request_endpoint(
            "getCurvesB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getEconomicIndicatorsB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """Obtém indicadores econômicos B3."""
        return self._request_endpoint(
            "getEconomicIndicatorsB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getScheduleCriB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """Obtém agenda de CRI da B3."""
        return self._request_endpoint(
            "getScheduleCriB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getScheduleCraB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """Obtém agenda de CRA da B3."""
        return self._request_endpoint(
            "getScheduleCraB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getDebenturesB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """
            Contém dados de debêntures da B3, é possível encontrar registros cadastrais, tais como mercadoria, ticker, ISIN, moeda de negociação, nome da companhia, data de vencimento do instrumento, taxa de juros, valor unitário do título, classificação de risco do ativo, banco mandatário, instituição depositária e outros; também é possível encontrar registros de valor, tais como preço de abertura do dia, preço máximo do dia, preço mínimo do dia, preço médio do dia, preço de fechamento, oscilação do dia, prazo de dias para liquidação e outros
            
            Args:
                Symbols (str): Símbolos dos fundos para consulta (obrigatório) 
                InitialDate (str): Data inicial da consulta (obrigatório)
                FinalDate (str): Data final da consulta (opcional)
                Fields (str): Campos específicos a retornar
                Interval (str): Intervalo dos dados
                IgnDefault (str): Ignorar valores padrão
                Lang (str): Idioma da resposta
                Page (int): Número da página
                Rows (int): Quantidade de linhas por página
                Format (str): Formato de retorno (default: "Json")
                IgnNull (str): Se deve retornar valores nulos (default: "False")
                isActive (str): Filtrar apenas símbolos ativos
                
            Returns:
                dict: Dados de CRI e CRA da B3
        """
        return self._request_endpoint(
            "getDebenturesB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getCorpActB3(self, Symbols, RefDate, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """Obtém eventos corporativos B3 (forma alternativa corporativa)."""
        return self._request_endpoint(
            "getCorpActB3",
            Symbols=Symbols,
            RefDate=RefDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getVolSB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """Obtém dados de volatilidade (VolS) da B3."""
        return self._request_endpoint(
            "getVolSB3",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getRegulatoryListed(self, Symbols, InitialDate, FinalDate=None, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """Obtém dados regulatórios de ativos listados."""
        return self._request_endpoint(
            "getRegulatoryListed",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getRegulatoryOTC(self, Symbols, InitialDate, FinalDate=None, Fields=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None):
        """Obtém dados regulatórios de operações OTC."""
        return self._request_endpoint(
            "getRegulatoryOTC",
            Symbols=Symbols,
            InitialDate=InitialDate,
            FinalDate=FinalDate,
            Fields=Fields,
            IgnDefault=IgnDefault,
            Lang=Lang,
            Page=Page,
            Rows=Rows,
            Format=Format,
            IgnNull=IgnNull
        )

    def getFundsCVM175(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
            """
            Obtém dados de fundos CVM (atualizados pela resolução Nº 175 da CVM).

            Args:
                Symbols (str): Símbolos dos fundos para consulta (obrigatório)
                InitialDate (str): Data inicial da consulta (obrigatório)
                FinalDate (str): Data final da consulta (opcional)
                Fields (str): Campos específicos a retornar
                Interval (str): Intervalo dos dados
                IgnDefault (str): Ignorar valores padrão
                Lang (str): Idioma da resposta
                Page (int): Número da página
                Rows (int): Quantidade de linhas por página
                Format (str): Formato de retorno (default: "Json")
                IgnNull (str): Se deve retornar valores nulos (default: "False")
                isActive (str): Filtrar apenas símbolos ativos
                
            Returns:
                dict: Dados de ações da B3 para os símbolos especificados
            """
            return self._request_endpoint(
                "getFundsCVM175",
                Symbols=Symbols,
                InitialDate=InitialDate,
                FinalDate=FinalDate,
                Fields=Fields,
                Interval=Interval,
                IgnDefault=IgnDefault,
                Lang=Lang,
                Page=Page,
                Rows=Rows,
                Format=Format,
                IgnNull=IgnNull,
                isActive=isActive
            )
    
    def getFundsAnbima175(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
            """
            Obtém dados de fundos Anbima (atualizados pela resolução Nº 175 da CVM).

            Args:
                Symbols (str): Símbolos dos fundos para consulta (obrigatório)
                InitialDate (str): Data inicial da consulta (obrigatório)
                FinalDate (str): Data final da consulta (opcional)
                Fields (str): Campos específicos a retornar
                Interval (str): Intervalo dos dados
                IgnDefault (str): Ignorar valores padrão
                Lang (str): Idioma da resposta
                Page (int): Número da página
                Rows (int): Quantidade de linhas por página
                Format (str): Formato de retorno (default: "Json")
                IgnNull (str): Se deve retornar valores nulos (default: "False")
                isActive (str): Filtrar apenas símbolos ativos
                
            Returns:
                dict: Dados de ações da B3 para os símbolos especificados
            """
            return self._request_endpoint(
                "getFundsAnbima175",
                Symbols=Symbols,
                InitialDate=InitialDate,
                FinalDate=FinalDate,
                Fields=Fields,
                Interval=Interval,
                IgnDefault=IgnDefault,
                Lang=Lang,
                Page=Page,
                Rows=Rows,
                Format=Format,
                IgnNull=IgnNull,
                isActive=isActive
            )


    def getCriCraB3(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
            """
            Método para trazer dados de CRI e CRA da B3, tais como empresa emissora, instituição depositária, agente fiduciário, pu de emissão, quantidade emitida, taxa de juros e outros.

            Args:
                Symbols (str): Símbolos dos fundos para consulta (obrigatório) 
                InitialDate (str): Data inicial da consulta (obrigatório)
                FinalDate (str): Data final da consulta (opcional)
                Fields (str): Campos específicos a retornar
                Interval (str): Intervalo dos dados
                IgnDefault (str): Ignorar valores padrão
                Lang (str): Idioma da resposta
                Page (int): Número da página
                Rows (int): Quantidade de linhas por página
                Format (str): Formato de retorno (default: "Json")
                IgnNull (str): Se deve retornar valores nulos (default: "False")
                isActive (str): Filtrar apenas símbolos ativos
                
            Returns:
                dict: Dados de CRI e CRA da B3
            """
            return self._request_endpoint(
                "getCriCraB3",
                Symbols=Symbols,
                InitialDate=InitialDate,
                FinalDate=FinalDate,
                Fields=Fields,
                Interval=Interval,
                IgnDefault=IgnDefault,
                Lang=Lang,
                Page=Page,
                Rows=Rows,
                Format=Format,
                IgnNull=IgnNull,
                isActive=isActive
            )
 
    def getCriCraAnbima(self, Symbols, InitialDate, FinalDate=None, Fields=None, Interval=None, IgnDefault=None, Lang=None, Page=None, Rows=None, Format=None, IgnNull=None, isActive=None):
            """
            Método para trazer dados de mercado secundário de CRI e CRA do Anbima-Feed

            Args:
                Symbols (str): Símbolos dos fundos para consulta (obrigatório) 
                InitialDate (str): Data inicial da consulta (obrigatório)
                FinalDate (str): Data final da consulta (opcional)
                Fields (str): Campos específicos a retornar
                Interval (str): Intervalo dos dados
                IgnDefault (str): Ignorar valores padrão
                Lang (str): Idioma da resposta
                Page (int): Número da página
                Rows (int): Quantidade de linhas por página
                Format (str): Formato de retorno (default: "Json")
                IgnNull (str): Se deve retornar valores nulos (default: "False")
                isActive (str): Filtrar apenas símbolos ativos
                
            Returns:
                dict: Dados de mercado secundário de CRI e CRA do Anbima-Feed
            """
            return self._request_endpoint(
                "getCriCraAnbima",
                Symbols=Symbols,
                InitialDate=InitialDate,
                FinalDate=FinalDate,
                Fields=Fields,
                Interval=Interval,
                IgnDefault=IgnDefault,
                Lang=Lang,
                Page=Page,
                Rows=Rows,
                Format=Format,
                IgnNull=IgnNull,
                isActive=isActive
            )
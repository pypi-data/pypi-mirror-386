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
    def getTradeInformation(self, Symbols: str = ":all", InstrumentType: str = None, ReferenceDate: str = None):
        """
        Busca e retorna informações de negociações de renda fixa (Negócio a Negócio) para o tipo de instrumento e data especificados.

        Este método retorna dados de negócio a negócio para o tipo de instrumento informado (CRA, CRI, DEB) e para a data de referência desejada.
        Permite aplicar filtros flexíveis sobre o array de objetos retornado, possibilitando a seleção por qualquer campo presente no JSON (ex: TckrSymb:25H2095950, ISIN:XYZ).
        Caso o parâmetro Symbols seja ":all" (padrão), todos os registros do arquivo serão retornados sem filtro.

        Parâmetros:
            Symbols (str, opcional): Filtro para os registros retornados. 
                - Para filtrar por campo específico, utilize o formato "Campo:Valor" (ex: TckrSymb:25H2095950, ISIN:XYZ).
                - Se apenas o valor for informado (ex: "25H2095950"), o filtro será aplicado sobre o campo padrão 'TckrSymb'.
                - Se ":all" (padrão), retorna todos os registros do arquivo sem filtro.
            InstrumentType (str, obrigatório): Tipo do instrumento financeiro. Aceita apenas "CRA", "CRI" ou "DEB".
            ReferenceDate (str, opcional): Data de referência do arquivo.
                - Aceita formatos YYYYMMDD, YYYY-MM-DD ou dinâmico (ex: D-1, D+1, C-1).
                - Datas dinâmicas são resolvidas automaticamente via utilitário interno.

        Returns:
            BDSResult: Objeto contendo os dados filtrados do arquivo Trade_FixedIncome.
                - api_url (str): URL do arquivo JSON acessado no blob.
                - body (list): Lista de registros filtrados conforme os parâmetros.
                - headers (dict): Cabeçalhos HTTP da resposta do blob.
                - status_code (int): Código de status HTTP da requisição.
                - call_duration (float): Tempo de execução da chamada em segundos.
                - data: (object): Dados brutos retornados pela API.

        Raises:
            ValueError: Se InstrumentType não for um dos valores permitidos ou se api_key não estiver configurada.
            FileNotFoundError: Se nenhum arquivo correspondente for encontrado para o tipo e data informados.     

        Exemplos de uso:
            # Retorna todos os registros de DEB para a data dinâmica D-1
            result = bdscore.datapack.getTradeInformation(Symbols=":all", InstrumentType="DEB", ReferenceDate="D-1")

            # Filtra registros por ticker específico
            result = bdscore.datapack.getTradeInformation(Symbols="TckrSymb:25H2095950", InstrumentType="CRA", ReferenceDate="20231020")

            # Filtra registros por ISIN
            result = datapack.getTradeInformation(Symbols="ISIN:BR1234567890", InstrumentType="CRI", ReferenceDate="2023-10-20")
        """
        import requests
        import re
        import time
        import xml.etree.ElementTree as ET
        from ..result import BDSResult

        if not InstrumentType or InstrumentType.upper() not in {"CRI", "CRA", "DEB"}:
            raise ValueError(
                f"O parâmetro 'InstrumentType' deve ser um dos valores permitidos: CRI, CRA ou DEB. Valor recebido: '{InstrumentType}'. "
                "Consulte a documentação do método getTradeInformation para detalhes."
            )

        # Resolve ReferenceDate
        refdate = ReferenceDate
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
        InstrumentType_lower = InstrumentType.lower()
        if InstrumentType_lower not in sas_dict:
            raise ValueError(f"Instrumento invalido:'{InstrumentType}' não encontrado na resposta da API.")
        sas_url = sas_dict[InstrumentType_lower]

        prefix = f"{refdate}/Trade_FixedIncome/{InstrumentType}/Trade_FixedIncome_TradeOTCFile_{InstrumentType}_{refdate}_"
        list_url = sas_url.split('?')[0] + f"?restype=container&comp=list&prefix={refdate}/Trade_FixedIncome/{InstrumentType}/"
        if '?' in sas_url:
            list_url += '&' + sas_url.split('?',1)[1]
        resp = requests.get(list_url)
        resp.raise_for_status()
        tree = ET.fromstring(resp.text)
        blobs = [b.find('Name').text for b in tree.findall('.//Blob') if b.find('Name') is not None]
        files = [b for b in blobs if b.startswith(prefix) and b.endswith('.json')]
        if not files:
            raise FileNotFoundError(f"Nenhum arquivo encontrado para {InstrumentType} em {refdate}")
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
        if Symbols == ":all":
            Symbols = None
        if Symbols and isinstance(data, list):
            if ':' in Symbols:
                field, value = Symbols.split(':', 1)
                data = [item for item in data if str(item.get(field)) == value]
            else:
                # Se não especificar campo, filtra por TckrSymb
                value = Symbols
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
        Obtém dados de títulos públicos brasileiros (Tesouro Nacional) para o período e filtros especificados.

        Retorna informações cadastrais e de valores dos títulos, com suporte a filtros por campo, data, e outros parâmetros.

        Parâmetros:
            Symbols (str): Filtro para os registros retornados.
            InitialDate (str): Data inicial do período.
            FinalDate (str, opcional): Data final do período.
            Fields, Interval, IgnDefault, Lang, Page, Rows, Format, IgnNull, isActive: Mesma descrição dos métodos anteriores.

        Returns:
            BDSResult: Objeto com os dados filtrados.
                - api_url (str)
                - body (list)
                - headers (dict)
                - status_code (int)
                - call_duration (float)
                - data (object): Dados brutos retornados pela API.

        Raises:
            ValueError, FileNotFoundError, requests.HTTPError

        Exemplos de uso:
            result = datapack.getBrazilianTreasury(Symbols=":all", InitialDate="D-5", FinalDate="D-1")
            df = result.data.to_df().head()
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
        Obtém dados de debêntures negociadas na B3 para o período e filtros especificados.

        Retorna registros cadastrais e de valores de debêntures, com filtros flexíveis por campo, data, e outros parâmetros.

        Parâmetros:
            Symbols (str): Filtro para os registros retornados.
            InitialDate (str): Data inicial do período.
            FinalDate (str, opcional): Data final do período.
            Fields, Interval, IgnDefault, Lang, Page, Rows, Format, IgnNull, isActive: Mesma descrição dos métodos anteriores.

        Returns:
            BDSResult: Objeto com os dados filtrados.
                - api_url (str)
                - body (list)
                - headers (dict)
                - status_code (int)
                - call_duration (float)
                - data (object): Dados brutos retornados pela API.

        Raises:
            ValueError, FileNotFoundError, requests.HTTPError

        Exemplos de uso:
            result = datapack.getDebenturesB3(Symbols=":all", InitialDate="D-5", FinalDate="D-1")
            df = result.data.to_df().head()
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
        Obtém dados de CRI e CRA negociados na B3 para o período e filtros especificados.

        Este método retorna informações cadastrais e de valores dos Certificados de Recebíveis Imobiliários (CRI) e do Agronegócio (CRA) negociados na B3, permitindo filtros flexíveis por campo, data e outros parâmetros.

        Parâmetros:
            Symbols (str): Filtro para os registros retornados. 
                - ":all" retorna todos os registros.
                - "Campo:Valor" filtra por campo específico (ex: ISIN:XYZ).
                - Valor simples filtra por TckrSymb.
            InitialDate (str): Data inicial do período (YYYYMMDD, YYYY-MM-DD ou dinâmico, ex: D-5).
            FinalDate (str, opcional): Data final do período (mesmos formatos).
            Fields (str, opcional): Campos específicos a retornar.
            Interval (str, opcional): Intervalo dos dados.
            IgnDefault (str, opcional): Ignorar valores padrão.
            Lang (str, opcional): Idioma da resposta.
            Page (int, opcional): Número da página.
            Rows (int, opcional): Quantidade de linhas por página.
            Format (str, opcional): Formato de retorno (JSON, XML, CSV, EXCEL).
            IgnNull (str, opcional): Se deve retornar valores nulos.
            isActive (str, opcional): Filtrar apenas ativos.

        Returns:
            BDSResult: Objeto com os dados filtrados.
                - api_url (str): URL do arquivo acessado.
                - body (list): Registros filtrados.
                - headers (dict): Cabeçalhos HTTP.
                - status_code (int): Código HTTP.
                - call_duration (float): Tempo de execução.
                - data (object): Dados brutos retornados pela API.: Dados brutos retornados.

        Raises:
            ValueError: Parâmetros inválidos.
            FileNotFoundError: Nenhum registro encontrado.
            requests.HTTPError: Erro nas requisições.

        Exemplos de uso:
            result = datapack.getCriCraB3(Symbols=":all", InitialDate="D-5", FinalDate="D-1")
            df = result.data.to_df().head()
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
        Obtém dados de CRI e CRA registrados na ANBIMA para o período e filtros especificados.

        Retorna informações detalhadas sobre CRI e CRA conforme registros da ANBIMA, com suporte a filtros por campo, data, e outros parâmetros.

        Parâmetros:
            Symbols (str): Filtro para os registros retornados. 
                - ":all" retorna todos os registros.
                - "Campo:Valor" filtra por campo específico.
                - Valor simples filtra por TckrSymb.
            InitialDate (str): Data inicial do período.
            FinalDate (str, opcional): Data final do período.
            Fields, Interval, IgnDefault, Lang, Page, Rows, Format, IgnNull, isActive: Mesma descrição do método anterior.

        Returns:
            BDSResult: Objeto com os dados filtrados.
                - api_url (str)
                - body (list)
                - headers (dict)
                - status_code (int)
                - call_duration (float)
                - data (object): Dados brutos retornados pela API.

        Raises:
            ValueError, FileNotFoundError, requests.HTTPError

        Exemplos de uso:
            result = datapack.getCriCraAnbima(Symbols=":all", InitialDate="D-5", FinalDate="D-1")
            df = result.data.to_df().head()
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
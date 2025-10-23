import logging

from typing import Any, Dict, List, Optional, Type, Union

from edat_utils.v2.graphql_service import T, GraphQLService

logger = logging.getLogger(__name__)


class ApiLotacaoService(GraphQLService):
    """Classe para gerenciar funcionarios"""

    head_query = """
    query {
        getDadosLotacoes(
            filter: {"""

    tail_query = """},
            orders: {field: "nome_local", type: ASC},
        ) {
            items {
                unidade
                numeroUnidade
                codigoUnidade
                numeroLocal
                unidadeOriginal
                nomeUnidade
                nomeUnidadeAcentuada
                categoriaUnidade
                local
                nomeLocal
                codigoLocal
                siglaArea
                tipoUnidade
            }
        }
      }"""

    def __init__(
        self,
        endpoint_url: str,
        response_model: Type[T],
        max_retries: int = 3,
        timeout: float = 10,
        logger: Optional[logging.Logger] = None,
        token: Optional[str] = None,
    ):
        super().__init__(
            endpoint_url, response_model, max_retries, timeout, logger, token
        )

    async def execute_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Union[T, List[T]]:
        """
        Método para buscar na api

        Args:
        - query: str dos filtros
        - variables: dict com as variáveis
        """
        query = query.replace("'", '"')
        _query = f"{self.head_query}{query}{self.tail_query}"
        return await super().execute_query(_query, variables)

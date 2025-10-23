from decimal import ROUND_HALF_UP, Decimal
import threading
from typing import Optional
import aiohttp

import aiohttp
import requests
from aiohttp import ClientSession
from rich.console import Console

from worker_automate_hub.api.helpers.api_helpers import handle_api_response
from worker_automate_hub.config.settings import load_env_config
from worker_automate_hub.models.dao.rpa_configuracao import RpaConfiguracao
from worker_automate_hub.models.dao.rpa_processo import RpaProcesso
from worker_automate_hub.models.dto.rpa_processo_entrada_dto import (
    RpaProcessoEntradaDTO,
)
from worker_automate_hub.utils.logger import logger
from worker_automate_hub.utils.util import get_new_task_info, get_system_info

console = Console()


async def get_new_task(stop_event: threading.Event) -> RpaProcessoEntradaDTO:
    env_config, _ = load_env_config()
    try:
        headers_basic = {"Authorization": f"Basic {env_config["API_AUTHORIZATION"]}"}
        data = await get_new_task_info()
        timeout = aiohttp.ClientTimeout(total=600) 

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True),timeout=timeout
        ) as session:
            async with session.post(
                f"{env_config["API_BASE_URL"]}/robo/new-job",
                data=data,
                headers=headers_basic,
            ) as response:
                res = await handle_api_response(response, stop_event)
                if res is not None:
                    return RpaProcessoEntradaDTO(**res.get("data"))
                else:
                    return None

    except Exception as e:
        err_msg = f"Erro ao obter nova tarefa: {e}"
        logger.error(err_msg)
        console.print(
            f"{err_msg}\n",
            style="bold red",
        )
        return None


async def notify_is_alive(stop_event: threading.Event):
    env_config, _ = load_env_config()
    try:

        headers_basic = {"Authorization": f"Basic {env_config["API_AUTHORIZATION"]}"}
        data = await get_system_info()

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            async with session.put(
                f"{env_config["API_BASE_URL"]}/robo/last-alive",
                data=data,
                headers=headers_basic,
            ) as response:
                return await handle_api_response(response, stop_event, last_alive=True)

    except Exception as e:
        err_msg = f"Erro ao informar is alive: {e}"
        logger.error(err_msg)
        console.print(
            f"{err_msg}\n",
            style="bold red",
        )
        return None


async def get_historico_by_processo_identificador(identificador, process_name):
    env_config, _ = load_env_config()

    if not identificador:
        return {
            "sucesso": False,
            "retorno": "Identificador do processo deve ser informado!",
        }
    elif not process_name:
        return {"sucesso": False, "retorno": "Nomedo do processo deve ser informado!"}

    headers_basic = {"Authorization": f"Basic {env_config["API_AUTHORIZATION"]}"}

    # Corpo da requisição
    body = {
        "identificador": identificador,
        "nomProcesso": process_name,
        "pageSize": 1,
        "periodoBusca": 2,
    }

    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            async with session.post(
                f"{env_config['API_BASE_URL']}/historico/by-identificador",
                headers=headers_basic,
                json=body,
            ) as response:
                if response.status != 200:
                    return {
                        "sucesso": False,
                        "retorno": f"Erro na requisição. Status code: {response.status}, {await response.text()}",
                    }

                # Processando a resposta JSON
                data = await response.json()

                if len(data) > 0:
                    return {"sucesso": True, "retorno": data}
                else:
                    return {
                        "sucesso": False,
                        "retorno": "Nenhum histórico encontrado para o processo",
                    }
    except Exception as e:
        return {"sucesso": False, "retorno": f"Erro ao buscar o histórico: {str(e)}"}


async def get_processo(uuidProcesso: str) -> RpaProcesso:
    """
    Retorna o processo com base no uuid informado.

    Args:
        uuidProcesso (str): O uuid do processo a ser retornado.

    Raises:
        ValueError: Se o uuid do processo n o for informado.
        Exception: Se houver um erro ao obter o processo.

    Returns:
        RpaProcesso: O processo caso tenha sido encontrado.
    """
    env_config, _ = load_env_config()
    x = 0
    while x < 10:
        try:
            if not uuidProcesso:
                raise ValueError("O uuid do processo deve ser informado")

            headers_basic = {"Authorization": f"Basic {env_config["API_AUTHORIZATION"]}"}
            timeout = aiohttp.ClientTimeout(total=600) 

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(verify_ssl=True), timeout=timeout
            ) as session:
                async with session.get(
                    f"{env_config["API_BASE_URL"]}/processo/{uuidProcesso}",
                    headers=headers_basic,
                ) as response:
                    if response.status != 200:
                        x += 1
                        console.print(f"Erro ao obter o processo: {response.content}")
                        continue
                    else:
                        res = await response.json()
                        if type(res["campos"]) == str and res["campos"] == "{}":
                            res["campos"] = {}
                        return RpaProcesso(**res)

        except ValueError as e:
            x += 1
            logger.error(f"Erro ao obter o processo: {str(e)}")
            console.print(
                f"{e}\n",
                style="bold red",
        )
            continue
            
    return None


async def get_workers():
    env_config, _ = load_env_config()
    try:

        headers_basic = {"Authorization": f"Basic {env_config["API_AUTHORIZATION"]}"}

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            async with session.get(
                f"{env_config["API_BASE_URL"]}/robo/workers",
                headers=headers_basic,
            ) as response:
                return await response.json()

    except Exception as e:
        err_msg = f"Erro ao obter a lista de workers: {e}"
        logger.error(err_msg)
        console.print(
            f"{err_msg}\n",
            style="bold red",
        )
        return None


async def get_config_by_name(name: str) -> RpaConfiguracao:
    """
    Obtem uma configuração pelo nome.

    Args:
        name (str): Nome da configuração a ser obtida.

    Returns:
        RpaConfiguracao: A configuração obtida.

    Raises:
        ValueError: Se não houver configuração do ambiente carregada.
        ValueError: Se não houver chave de autentica o na configuração do ambiente.
        ValueError: Se não houver URL da API na configuração do ambiente.
        Exception: Se houver um erro ao obter a configuração.
    """
    env_config, _ = load_env_config()
    if env_config is None:
        raise ValueError("Configuração do ambiente não carregada")
    if "API_AUTHORIZATION" not in env_config:
        raise ValueError(
            "Chave de autenticação não encontrada na configuração do ambiente"
        )
    if "API_BASE_URL" not in env_config:
        raise ValueError("URL da API não encontrada na configuração do ambiente")

    x = 0
    while x < 10:
        try:
            headers_basic = {"Authorization": f"Basic {env_config["API_AUTHORIZATION"]}"}
            timeout = aiohttp.ClientTimeout(total=600) 

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(verify_ssl=True), timeout=timeout
            ) as session:
                async with session.get(
                    f"{env_config["API_BASE_URL"]}/configuracao/api/{name}",
                    headers=headers_basic,
                ) as response:
                    if response.status != 200:
                        console.print(f"Erro ao obter a configuração: {response.content}")
                        x += 1
                    else:
                        data = await response.json()
                        return RpaConfiguracao(**data)
        except Exception as e:
            x += 1
            err_msg = f"Erro ao obter a configuração: {e}"
            logger.error(err_msg)
            console.print(
                f"{err_msg}\n",
                style="bold red",
            )
    return None


def sync_get_config_by_name(name: str) -> RpaConfiguracao:
    """
    Obtém a configuração do ambiente pelo nome.

    Args:
        name (str): Nome da configuração a ser obtida.

    Returns:
        RpaConfiguracao: A configuração obtida.

    Raises:
        ValueError: Se não houver configuração do ambiente carregada.
        ValueError: Se não houver chave de autenticação na configuração do ambiente.
        ValueError: Se não houver URL da API na configuração do ambiente.
        Exception: Se houver um erro ao obter a configuração.
    """
    env_config, _ = load_env_config()
    if env_config is None:
        raise ValueError("Configuração do ambiente não carregada")
    if "API_AUTHORIZATION" not in env_config:
        raise ValueError(
            "Chave de autenticação não encontrada na configuração do ambiente"
        )
    if "API_BASE_URL" not in env_config:
        raise ValueError("URL da API não encontrada na configuração do ambiente")

    try:
        headers_basic = {"Authorization": f"Basic {env_config['API_AUTHORIZATION']}"}

        response = requests.get(
            f"{env_config['API_BASE_URL']}/configuracao/api/{name}",
            headers=headers_basic,
            verify=False,  # Desativa a verificação SSL
        )

        response.raise_for_status()

        data = response.json()
        return RpaConfiguracao(**data)

    except requests.RequestException as e:
        err_msg = f"Erro ao obter a configuração: {e}"
        logger.error(err_msg)
        console.print(err_msg, style="red")
        return None


async def send_gchat_message(message: str) -> None:
    """
    Envia uma mensagem para o Google Chat.

    Args:
        message (str): Mensagem a ser enviada.

    Returns:
        dict: O retorno da API do Google Chat.

    Raises:
        ValueError: Se não houver configuração do ambiente carregada.
        ValueError: Se não houver chave de autenticação na configuração do ambiente.
        ValueError: Se não houver URL da API na configuração do ambiente.
        Exception: Se houver um erro ao enviar a mensagem.
    """
    env_config, _ = load_env_config()
    if env_config is None:
        raise ValueError("Configurão do ambiente não carregada")
    if "API_AUTHORIZATION" not in env_config:
        raise ValueError(
            "Chave de autenticação não encontrada na configuração do ambiente"
        )
    if "API_BASE_URL" not in env_config:
        raise ValueError("URL da API não encontrada na configuração do ambiente")

    try:
        headers_basic = {"Authorization": f"Basic {env_config['API_AUTHORIZATION']}"}

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            async with session.post(
                f"{env_config['API_BASE_URL']}/google-chat",
                data={"message": message},
                headers=headers_basic,
            ) as response:
                if response.status != 200:
                    raise Exception(
                        f"Erro ao enviar mensagem ao Google Chat: {response.content}"
                    )

    except ValueError as e:
        logger.error(f"Erro ao enviar mensagem ao Google Chat: {e}")
        console.print(
            f"{e}\n",
            style="bold red",
        )
        return None
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem ao Google Chat: {e}")
        console.print(
            f"{e}\n",
            style="bold red",
        )
        return None


def read_secret(path: str, vault_token: str):

    url = f"https://aspirina.simtech.solutions/{path}"
    headers = {"X-Vault-Token": vault_token, "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result["data"]["data"]
    elif response.status_code == 403:
        err_msg = "403 - Token inválido!"
        logger.error(err_msg)
        console.print(f"\n{err_msg}\n", style="bold red")
    else:
        response.raise_for_status()


def load_environments(env: str, vault_token: str):

    environments = {}
    credentials = {}

    environments[env] = read_secret(
        path=f"v1/{env}-sim/data/worker-automate-hub/env", vault_token=vault_token
    )
    credentials[env] = read_secret(
        path=f"v1/{env}-sim/data/worker-automate-hub/credentials.json",
        vault_token=vault_token,
    )

    return environments[env], credentials[env]


async def get_index_modelo_emsys(filial: str, descricao_documento: str):
    """
    Procura o index de um modelo de documento fiscal no EMSYS.

    Args:
    filial (str): Código da filial.
    descricao_documento (str): Descrição do documento fiscal.

    Returns:
    dict: Contendo o index do modelo de documento fiscal.

    Raises:
    Exception: Se houver um erro ao comunicar com o endpoint do Simplifica.
    """
    env_config, _ = load_env_config()

    body = {"codigoEmpresa": filial, "descricaoDocumento": descricao_documento}
    headers_basic = {"Authorization": f"Basic {env_config['API_AUTHORIZATION']}"}

    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            async with session.post(
                f"{env_config['API_BASE_URL']}/emsys/buscar-index-documento-fiscal",
                data=body,
                headers=headers_basic,
            ) as response:
                if response.status != 200:
                    raise Exception(
                        f"Erro ao comunicar com endpoint do Simplifica: {response.text}"
                    )
                data = await response.json()
                log_msg = f"\nSucesso ao procurar {data}.\n"
                console.print(
                    log_msg,
                    style="bold green",
                )
                logger.info(log_msg)
                return data

    except Exception as e:
        err_msg = f"Erro ao comunicar com endpoint do Simplifica: {e}"
        console.print(f"\n{err_msg}\n", style="bold green")
        logger.info(err_msg)


async def get_valor_remessa_cobranca(date: str):
    """
    Procura o valor da remssa de cobrança no EMSYS.

    Args:
    data (str): Data que deseja fazer a busca


    Returns:
    dict: Dicionario com o valor da remssa

    Raises:
    Exception: Se houver um erro ao comunicar com o endpoint da Api.
    """
    env_config, _ = load_env_config()

    body = {
        "data": date,
    }
    headers_basic = {"Authorization": f"Basic {env_config['API_AUTHORIZATION']}"}

    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            async with session.post(
                f"{env_config['API_BASE_URL']}/emsys/consulta-valor-remessa-cobranca",
                data=body,
                headers=headers_basic,
            ) as response:
                if response.status != 200:
                    raise Exception(
                        f"Erro ao comunicar com endpoint do Simplifica: {response.text}"
                    )
                data = await response.json()

                log_msg = f"\nSucesso ao procurar {data}.\n"
                console.print(
                    log_msg,
                    style="bold green",
                )
                logger.info(log_msg)
                valor = Decimal(str(data[0]["coalesce"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                return valor

    except Exception as e:
        err_msg = f"Erro ao comunicar com endpoint do Simplifica: {e}"
        console.print(f"\n{err_msg}\n", style="bold green")
        logger.info(err_msg)


async def get_status_nf_emsys(chave: int):
    """
    Procura o status de nota fiscal no EMSYS.
    """
    env_config, _ = load_env_config()

    url = f"{env_config['API_BASE_URL']}/emsys/consulta-status-nota?chaveNfe={chave}"
    headers_basic = {"Authorization": f"Basic {env_config['API_AUTHORIZATION']}"}
    timeout = aiohttp.ClientTimeout(total=600)

    try:
        timeout = aiohttp.ClientTimeout(total=600)  # aguarda até 10 minutos
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True),
            timeout=timeout
        ) as session:
            async with session.get(url, headers=headers_basic) as response:
                if response.status != 200:
                    raise Exception(
                        f"Erro ao comunicar com endpoint do Simplifica: {await response.text()}"
                    )
                data = await response.json()
                if not data or not isinstance(data, dict):
                    raise Exception(
                        f"Erro ao comunicar com endpoint do Simplifica: {data}"
                    )
                log_msg = f"\nSucesso ao procurar {data}.\n"
                console.print(log_msg, style="bold green")
                logger.info(log_msg)
                return data

    except Exception as e:
        err_msg = f"Erro ao comunicar com endpoint do Simplifica: {e}"
        console.print(f"\n{err_msg}\n", style="bold red")
        logger.error(err_msg)

async def get_dados_nf_emsys(
    chave: Optional[int] = None,
    numero_nota: Optional[int] = None,
    serie_nota: Optional[int] = None,
    filial_nota: Optional[int] = None
):
    """
    Consulta a NF no EMSYS (ahead-nota) e retorna os campos essenciais:
    empresaCodigo, numeroDoCfop e cfopProduto dentro de itens.

    Args:
        chave (int, opcional): Chave de acesso da NF.
        numero_nota (int, opcional): Número da NF.
        serie_nota (int, opcional): Série da NF (obrigatória se numero_nota for informado).
        filial_nota (int, opcional): Filial da NF (obrigatória se numero_nota for informado).

    Returns:
        list[dict]: Lista de notas no formato esperado.
    """
    env_config, _ = load_env_config()

    url = f"{env_config['API_BASE_URL']}/ahead-nota/find-by-number-nfe"

    params = {}

    # Caso 1: veio a chave
    if chave is not None:
        params["chaveNfe"] = chave

    # Caso 2: veio numero_nota → exige serie e filial
    elif numero_nota is not None:
        if serie_nota is None or filial_nota is None:
            raise ValueError("Para buscar por número da nota é obrigatório informar também 'serie_nota' e 'filial_nota'.")
        params["numeroNfe"] = numero_nota
        params["serieNfe"] = serie_nota
        params["empresaCodigo"] = filial_nota

    else:
        raise ValueError("É necessário informar 'chave' ou ('numero_nota' + 'serie_nota' + 'filial_nota').")

    headers_basic = {"Authorization": f"Basic {env_config['API_AUTHORIZATION']}"}

    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            async with session.get(url, headers=headers_basic, params=params) as response:
                if response.status != 200:
                    body = await response.text()  # ✅ lê o conteúdo do body
                    raise Exception(
                        f"({response.status}): {body}"
                    )

                data = await response.json()

                if not data:
                    raise Exception("Não foi possível buscar os dados da nota (ahead_nota).")

                if isinstance(data, dict):
                    data = [data]

                resultado = []
                for nota in data:
                    resultado.append({
                        "chaveNfe": nota.get("chaveNfe"),
                        "numeroDoCfop": nota.get("numeroDoCfop"),
                        "naturezaNota": nota.get("naturezaNota"),
                        "empresa": nota.get("empresa"),
                        "fornecedorCnpj": nota.get("fornecedorCnpj"),
                        "fornecedorNome": nota.get("fornecedorNome"),
                        "numeroNfe": nota.get("numeroNfe"),
                        "valorNfe": nota.get("valorNfe"),
                        "dataEmissao": nota.get("dataEmissao"),
                        "empresaCodigo": nota.get("empresaCodigo"),
                        "dataVencimento": nota.get("dataVencimento"),
                        "statusSituacao": nota.get("statusSituacao"),
                        "statusRebUnidade": nota.get("statusRebUnidade"),
                        "statusListarNotas": nota.get("statusListarNotas"),
                        "existeDespesa": nota.get("existeDespesa"),
                        "observacao": nota.get("observacao"),
                        "createdAt": nota.get("createdAt"),
                        "updatedAt": nota.get("updatedAt"),
                        "infCpl": nota.get("infCpl"),
                        "recebimentoFisico": nota.get("recebimentoFisico"),
                        "serieNfe": nota.get("serieNfe"),
                        "statusLancamento": nota.get("statusLancamento"),
                        "dataEntrada": nota.get("dataEntrada"),
                        "codPessoaFornecedor": nota.get("codPessoaFornecedor"),
                        "locked": nota.get("locked"),
                        "itens": [
                            {
                                "uuidNotaItem": item.get("uuidNotaItem"),
                                "chaveNfe": item.get("chaveNfe"),
                                "codigoProduto": item.get("codigoProduto"),
                                "descricaoProduto": item.get("descricaoProduto"),
                                "ncmsh": item.get("ncmsh"),
                                "ocst": item.get("ocst"),
                                "cfopProduto": item.get("cfopProduto"),
                                "unidadeMedida": item.get("unidadeMedida"),
                                "qtd": item.get("qtd"),
                                "valorUnitario": item.get("valorUnitario"),
                                "valorTotal": item.get("valorTotal"),
                                "bCalculoIcms": item.get("bCalculoIcms"),
                                "valorIcms": item.get("valorIcms"),
                                "valorIpi": item.get("valorIpi"),
                                "aliquotaIcms": item.get("aliquotaIcms"),
                                "aliquotaIpi": item.get("aliquotaIpi"),
                                "createdAt": item.get("createdAt"),
                                "updatedAt": item.get("updatedAt"),
                                "pedidoCompraXped": item.get("pedidoCompraXped"),
                                "pedidoCompraItemPed": item.get("pedidoCompraItemPed"),
                                "codItem": item.get("codItem"),
                                "desItem": item.get("desItem"),
                                "indBloqueadoCompra": item.get("indBloqueadoCompra"),
                                "indItemAtivo": item.get("indItemAtivo")
                            }
                            for item in nota.get("itens", [])
                        ]
                    })

                return resultado

    except Exception as e:
        raise Exception(f"{e}")



async def get_status_cte_emsys(chave: int):
    """
    Procura o status de CTE no  EMSYS.

    Args:
    chave (int): Chave de acesso do CTE.

    Returns:
    dict: Contendo o chave de acesso e status de processamento do CTE.

    Raises:
    Exception: Se houver um erro ao comunicar com o endpoint do Simplifica.
    """
    env_config, _ = load_env_config()

    url = f"{env_config['API_BASE_URL']}/emsys/consulta-status-cte?chaveCte={chave}"

    headers_basic = {"Authorization": f"Basic {env_config['API_AUTHORIZATION']}"}

    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            async with session.get(url, headers=headers_basic) as response:
                if response.status != 200:
                    raise Exception(
                        f"Erro ao comunicar com endpoint do Simplifica: {response.text}"
                    )
                data = await response.json()
                if not data or not isinstance(data, dict):
                    raise Exception(
                        f"Erro ao comunicar com endpoint do Simplifica: {data}"
                    )
                log_msg = f"\nSucesso ao procurar {data}.\n"
                console.print(
                    log_msg,
                    style="bold green",
                )
                logger.info(log_msg)
                return data

    except Exception as e:
        err_msg = f"Erro ao comunicar com endpoint do Simplifica: {e}"
        console.print(f"\n{err_msg}\n", style="bold green")
        logger.info(err_msg)


# Função para enviar arquivo de imagem a api
async def send_file(
    uuidRelacao: str,
    desArquivo: str,
    tipo: str,
    file: bytes,
    file_extension: str = "jpg",
) -> None:
    """
    Função assíncrona para enviar um arquivo para uma API.

    Args:
        uuidRelacao (str): UUID da relação associada ao arquivo.
        desArquivo (str): Nome real do arquivo (com extensão).
        tipo (str): Tipo de arquivo (ex: 'xls').
        file (bytes): Conteúdo binário do arquivo.
        file_extension (str): Extensão do arquivo (sem o ponto), usada para definir o content-type.
    """
    try:
        # Carrega as configurações de ambiente
        env_config, _ = load_env_config()

        # Define o content-type e o filename baseados na extensão
        if file_extension == "txt":
            content_type = "text/plain"
        elif file_extension == "pdf":
            content_type = "application/pdf"
        elif file_extension == "jpg":
            content_type = "image/jpeg"
        elif file_extension == "001":
            content_type = "text/plain"
        elif file_extension == "xls":
            filename = desArquivo
            content_type = "application/vnd.ms-excel"
        elif file_extension == "xlsx":
            filename = desArquivo
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif file_extension == "csv": 
            content_type = "text/csv"
        else:
            raise ValueError(f"Extensão de arquivo não suportada: {file_extension}")

        # Criação do corpo da requisição multipart
        body = aiohttp.FormData()
        body.add_field("uuidRelacao", uuidRelacao)
        body.add_field("desArquivo", desArquivo)
        body.add_field("tipo", tipo)
        body.add_field("file", file, filename=desArquivo, content_type=content_type)

        headers_basic = {
            "Authorization": f"Basic {env_config['API_AUTHORIZATION']}"
        }

        # Enviando requisição para a API
        async with ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(
                f"{env_config['API_BASE_URL']}/arquivo/send-file",
                data=body,
                headers=headers_basic,
            ) as response:
                if response.status != 200:
                    content = await response.text()
                    raise Exception(f"Erro {response.status} - Resposta da API: {content}")

                log_msg = f"\n✅ Sucesso ao enviar arquivo: {uuidRelacao}\n"
                console.print(log_msg, style="bold green")
                logger.info(log_msg)

    except aiohttp.ClientResponseError as e:
        err_msg = f"Erro na resposta da API: {e.status} - {e.message}"
        console.print(f"\n{err_msg}\n", style="bold red")
        logger.error(err_msg)

    except Exception as e:
        err_msg = f"Erro ao enviar arquivo: {str(e)}"
        console.print(f"\n{err_msg}\n", style="bold red")
        logger.error(err_msg)


async def change_robot_status_true(uuid_robo: str):
    env_config, _ = load_env_config()
    try:
        headers_basic = {"Authorization": f"Basic {env_config["API_AUTHORIZATION"]}"}

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            async with session.get(
                f"{env_config["API_BASE_URL"]}/robo/enable-robot/{uuid_robo}",
                headers=headers_basic,
            ) as response:
                if response.status == 200:
                    console.print("Robo alterado com sucesso!", style="bold green")
                else:
                    raise Exception(f"{response.status} - {response.text}")
    except Exception as e:
        err_msg = f"Erro ao obter nova tarefa: {e}"
        logger.error(err_msg)
        console.print(
            f"{err_msg}\n",
            style="bold red",
        )


async def download_file_from_historico(uuid: str):
    env_config, _ = load_env_config()

    url = f"{env_config['API_BASE_URL']}/arquivo/downloadById/"

    headers_basic = {"Authorization": f"Basic {env_config['API_AUTHORIZATION']}"}
    body = {"uuidRelacao": uuid}
    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=True)
        ) as session:
            console.print("Baixando arquivo do historico...", style="bold green")
            async with session.post(url, headers=headers_basic, json=body) as response:
                if response.status != 200:
                    raise Exception(
                        f"Erro ao baixar arquivo do historico: {response.text}"
                    )
                data = await response.json()
                log_msg = f"\nSucesso ao baixar arquivo.\n"
                console.print(
                    log_msg,
                    style="bold green",
                )
                logger.info(log_msg)
                return data

    except Exception as e:
        err_msg = (
            f"Erro ao comunicar com endpoint para download do arquivo do historico: {e}"
        )
        console.print(f"\n{err_msg}\n", style="bold green")
        logger.info(err_msg)

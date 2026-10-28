# Roda dentro do container "api" do Dify (chamado por corrigir-conhecimento.sh).
# Troca os modelos de embedding do Gemini que o Google desativou pelo atual e
# manda indexar de novo os documentos do Conhecimento que ficaram com erro.
#   sem argumentos: corrige uma vez e reindexa todos os documentos com erro
#   --vigiar:       faz o mesmo e depois repete a cada 15 s, reindexando só os que falharam
#                   pelo modelo desativado (o padrão é escolhido quando o aluno instala o Gemini)
import logging
import sys
import time

logging.disable(logging.CRITICAL)
from app_factory import create_app
from sqlalchemy import select
from extensions.ext_database import db
from extensions.ext_redis import redis_client
from models.dataset import Dataset, Document
from models.provider import TenantDefaultModel
from services.dataset_service import DatasetCollectionBindingService
from tasks.retry_document_indexing_task import retry_document_indexing_task

GEMINI = "langgenius/gemini/google"
DESATIVADOS = ("embedding-001", "text-embedding-004")  # o Google responde 404 para eles
ATUAL = "gemini-embedding-001"
VIGIAR = "--vigiar" in sys.argv


def corrigir(so_modelo):
    session = db.session
    for padrao in session.scalars(select(TenantDefaultModel).where(
            TenantDefaultModel.provider_name == GEMINI, TenantDefaultModel.model_name.in_(DESATIVADOS))):
        padrao.model_name = ATUAL
        print(f"Modelo de embedding padrão trocado para {ATUAL}", flush=True)

    for dataset in session.scalars(select(Dataset).where(
            Dataset.embedding_model_provider == GEMINI, Dataset.embedding_model.in_(DESATIVADOS))):
        dataset.embedding_model = ATUAL
        dataset.collection_binding_id = DatasetCollectionBindingService.get_dataset_collection_binding(
            GEMINI, ATUAL, session).id
        print(f"Base '{dataset.name}' agora usa {ATUAL}", flush=True)
    session.commit()

    consulta = select(Document).where(Document.indexing_status == "error")
    if so_modelo:
        consulta = consulta.where(Document.error.contains("is not found"))
    por_base = {}
    for d in session.scalars(consulta):
        # mesma trava do botão "Tentar novamente": não repete enquanto o worker não pegar
        if redis_client.set(f"document_{d.id}_is_retried", 1, ex=600, nx=True):
            por_base.setdefault(d.dataset_id, []).append(d.id)
    for dataset_id, ids in por_base.items():
        dataset = session.get(Dataset, dataset_id)
        if dataset.embedding_model in DESATIVADOS:
            continue
        retry_document_indexing_task.delay(dataset_id, ids, dataset.created_by)
        print(f"Reindexando {len(ids)} documento(s) da base '{dataset.name}'", flush=True)
    if not VIGIAR and not por_base:
        print("Nenhum documento com erro no Conhecimento.")
    session.remove()


with create_app()[1].app_context():
    # um vigia só: se outro já está rodando (ex.: ligar.sh rodou de novo), este sai
    if VIGIAR and not redis_client.set("kit_vigia_conhecimento", 1, ex=60, nx=True):
        sys.exit(0)
    corrigir(so_modelo=False)
    while VIGIAR:
        time.sleep(15)
        redis_client.expire("kit_vigia_conhecimento", 60)
        try:
            corrigir(so_modelo=True)
        except Exception as e:
            db.session.remove()
            print(f"Aviso: {e}", flush=True)

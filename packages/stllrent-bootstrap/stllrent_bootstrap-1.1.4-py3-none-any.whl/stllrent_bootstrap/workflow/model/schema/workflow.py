from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict, List
from datetime import datetime
from uuid import UUID
from enum import Enum
from ..enums import WorkflowStatus
from stllrent_bootstrap.workflow.model.schema.task import TaskResponse, TaskCreate

class CeleryFlowType(str, Enum):
    SINGLE = "single"
    GROUP = "group"
    CHAIN = "chain"
    CHORD = "chord"
    MAP = "map"
    STARMAP = "starmap"
    CHUNKS = "chunks"

class WorkflowCreate(BaseModel):
    """
    Schema para criar um novo Workflow.
    O cliente envia apenas os dados necessários para a criação, sem se preocupar com os dados gerados automaticamente pelo BD
    """
    resource: str = Field(..., description="Identificador do recurso associado ao workflow.")
    input: Dict[str, Any] = Field(..., description="Dados de entrada para o workflow, no formato JSON.")
    flow_type: CeleryFlowType = Field(..., description="Tipo do fluxo de trabalho.")
    flow_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais opcionais para o workflow.")
    task_list: List[TaskCreate] = Field(...)

class WorkflowResponse(BaseModel):
    """
    Schema para retornar um Workflow.
    Inclui todos os campos do banco de dados que podem ser expostos.
    """
    oid: UUID = Field(..., description="Identificador único do workflow. também chamado de request_id")
    status: WorkflowStatus = Field(..., description="Status atual da execução do workflow.")
    resource: str = Field(..., description="Identificador serviço responsável pro criar o workflow.")
    input: Dict[str, Any] = Field(..., description="Dados de entrada do workflow.")
    flow_type: CeleryFlowType = Field(..., description="Tipo do fluxo de trabalho.")
    flow_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais do workflow, que poder ser alterados durante a execução das tasks")
    created_at: datetime = Field(..., description="Data e hora de criação do workflow.")
    updated_at: Optional[datetime] = Field(None, description="Última data e hora de atualização do workflow.")

    # A lista de tarefas associadas, usando o TaskResponse.
    # Use Field(default_factory=list) se a lista puder ser vazia e você quiser um padrão.
    task_list: List[TaskResponse] = Field(default_factory=list, description="Lista de tasks associadas ao workflow.")

    # --- Configuração Pydantic v2 para permitir a criação a partir de instâncias de ORM ---
    model_config = ConfigDict(from_attributes=True)

class WorkflowUpdate(BaseModel):
    """
    Schema para atualizar campos específicos de um Workflow.
    Todos os campos são opcionais, permitindo atualizações parciais.
    """
    status: Optional[WorkflowStatus] = Field(None, description="Novo status para o workflow.")
    flow_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais para o workflow.")
    # Geralmente não se atualiza 'resource', 'input' ou 'flow_type' diretamente após a criação.
    # 'updated_at' é gerenciado pelo BD.

class WorkflowSummarized(BaseModel):
    """
    Schema listar workflows de forma resumida para resultado de pesquisa.
    """
    oid: UUID = Field(..., description="Identificador único do workflow. também chamado de request_id")
    resource: str = Field(..., description="Identificador serviço responsável pro criar o workflow.")
    status: WorkflowStatus = Field(..., description="Status atual da execução do workflow.")
    created_at: datetime = Field(..., description="Data e hora de criação do workflow.")
    flow_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais do workflow, que poder ser alterados durante a execução das tasks")
        
    # Permite que o Pydantic leia os dados de atributos de objeto (modo ORM)
    model_config = ConfigDict(from_attributes=True)

class GroupedCount(BaseModel):
    """
    Schema genérico para representar um resultado de contagem agrupado.
    Ex: { "item": "SUCCESS", "count": 10 }
    """
    item: Any = Field(..., description="O item que foi agrupado (e.g., status, resource, task_name).")
    count: int = Field(..., description="A contagem de ocorrências do item.")

class MonitoringResponse(BaseModel):
    """
    Schema para a resposta do endpoint de monitoramento.
    Agrega as contagens de status e recursos de workflows e tasks.
    """
    workflow_status_count: List[GroupedCount] = Field(..., description="Contagem de workflows por status.")
    task_status_count: List[GroupedCount] = Field(..., description="Contagem de tasks por status.")
    workflow_resource_count: List[GroupedCount] = Field(..., description="Contagem de workflows por recurso (resource).")
    task_name_count: List[GroupedCount] = Field(..., description="Contagem de tasks por nome (task_name).")

    model_config = ConfigDict(from_attributes=True)

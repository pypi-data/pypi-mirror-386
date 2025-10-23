# Como Usar keeps-learn-nexus-proto (Python)

## 1. Instalar o Pacote

```bash
pip install keeps-learn-nexus-proto
```

## 2. Nenhuma Configuração Necessária!

O pacote está publicado em PyPI público, então não precisa de token ou configuração especial.

Basta instalar e usar!

## 3. Usar nos Arquivos

### Opção A: Obter Caminho do Proto

```python
from keeps_learn_nexus_proto import get_proto_path, get_proto_dir

# Obter caminho de um proto específico
users_proto = get_proto_path('users')
workspaces_proto = get_proto_path('workspaces')

print(f"Users proto: {users_proto}")
print(f"Workspaces proto: {workspaces_proto}")
```

### Opção B: Usar com gRPC

```python
from grpc_tools import protoc
from keeps_learn_nexus_proto import get_proto_dir

# Compilar proto files
protoc.main((
    'grpc_tools.protoc',
    '-I' + get_proto_dir(),
    '--python_out=.',
    '--grpc_python_out=.',
    'users.proto',
))
```

### Opção C: Usar com FastAPI + gRPC

```python
from keeps_learn_nexus_proto import get_proto_path
import grpc
from concurrent import futures

# Usar o caminho do proto
proto_path = get_proto_path('users')

# Configurar seu servidor gRPC
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
# ... adicionar seus serviços
```

## 4. Estrutura de Arquivos

Os arquivos proto estão em:

```
site-packages/keeps_learn_nexus_proto/
├── __init__.py
└── ../protos/
    ├── users.proto
    ├── workspaces.proto
    ├── certificate-manager/
    ├── custom-sections/
    ├── konquest/
    ├── myaccount/
    ├── notification/
    ├── search/
    └── sisyphus/
```

## 5. Atualizar Quando Houver Novas Versões

```bash
pip install --upgrade keeps-learn-nexus-proto
```

## 6. Verificar Versão Instalada

```bash
pip show keeps-learn-nexus-proto
```

## Benefícios

✓ Nenhum token necessário  
✓ Qualquer desenvolvedor consegue usar  
✓ Fácil atualizar versão  
✓ Compartilhado entre múltiplos projetos  
✓ Sem duplicação de código  
✓ Funciona com Python 3.7+  

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'keeps_learn_nexus_proto'"

Verifique se o pacote está instalado:

```bash
pip list | grep keeps-learn-nexus-proto
```

Se não estiver, instale:

```bash
pip install keeps-learn-nexus-proto
```

### Erro: "Proto file not found"

Verifique o caminho do arquivo proto:

```python
from keeps_learn_nexus_proto import get_proto_dir
import os

proto_dir = get_proto_dir()
print(f"Proto directory: {proto_dir}")
print(f"Files: {os.listdir(proto_dir)}")
```


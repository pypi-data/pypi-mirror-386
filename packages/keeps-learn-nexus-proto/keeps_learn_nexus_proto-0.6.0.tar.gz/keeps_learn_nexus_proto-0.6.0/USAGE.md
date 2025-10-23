# Usage Guide

## Installation

### Node.js / npm

```bash
npm install @keeps-learn/nexus-proto
```

📦 **npm Package**: https://www.npmjs.com/package/@keeps-learn/nexus-proto

### Python / pip

```bash
pip install keeps-learn-nexus-proto
```

📦 **PyPI Package**: https://pypi.org/project/keeps-learn-nexus-proto/

---

## Node.js Usage

### Setup with Nx

First, configure your `project.json` to copy proto files to assets:

```json
{
  "targets": {
    "build": {
      "executor": "@nx/node:build",
      "options": {
        "outputPath": "dist/apps/your-app",
        "main": "apps/your-app/src/main.ts",
        "tsConfig": "apps/your-app/tsconfig.app.json",
        "assets": [
          "apps/your-app/src/assets",
          {
            "input": "node_modules/@keeps-learn/nexus-proto/protos",
            "glob": "**/*",
            "output": "assets/protos"
          }
        ]
      }
    }
  }
}
```

### Option 1: Using Nx Assets (Recommended)

Create `proto-loader.ts`:

```typescript
import { join } from 'path';

const PROTO_BASE = join(__dirname, './assets/protos');

export const PROTO_PATHS = {
  users: join(PROTO_BASE, 'myaccount/users.proto'),
  workspaces: join(PROTO_BASE, 'myaccount/workspaces.proto'),
  missions: join(PROTO_BASE, 'konquest/mission.proto'),
  // Add more as needed
};
```

Then use in your gRPC configuration:

```typescript
import { GrpcOptions, Transport } from '@nestjs/microservices';
import { PROTO_PATHS } from './proto-loader';

export const GRPC_OPTIONS: GrpcOptions = {
  transport: Transport.GRPC,
  options: {
    package: ['users', 'workspaces', 'mission'],
    protoPath: [
      PROTO_PATHS.users,
      PROTO_PATHS.workspaces,
      PROTO_PATHS.missions
    ],
    url: process.env.GRPC_URL || '0.0.0.0:50051',
    loader: {
      keepCase: false,
      longs: String,
      enums: String,
      defaults: true,
      oneofs: true,
    },
  },
};
```

### Option 2: Direct Path (Without Nx Assets)

If not using Nx assets, use direct path:

```typescript
import { join } from 'path';

const PROTO_BASE = join(__dirname, '../node_modules/@keeps-learn/nexus-proto/protos');

export const PROTO_PATHS = {
  users: join(PROTO_BASE, 'myaccount/users.proto'),
  workspaces: join(PROTO_BASE, 'myaccount/workspaces.proto'),
};
```

---

## Python Usage

### Option 1: Get Proto Path

```python
from keeps_learn_nexus_proto import get_proto_path, get_proto_dir

# Get path to a specific proto
users_proto = get_proto_path('users')
workspaces_proto = get_proto_path('workspaces')

print(f"Users proto: {users_proto}")
print(f"Workspaces proto: {workspaces_proto}")
```

### Option 2: Compile Proto Files

```python
from grpc_tools import protoc
from keeps_learn_nexus_proto import get_proto_dir

# Compile proto files
protoc.main((
    'grpc_tools.protoc',
    '-I' + get_proto_dir(),
    '--python_out=.',
    '--grpc_python_out=.',
    'users.proto',
))
```

### Option 3: Use with gRPC Server

```python
from keeps_learn_nexus_proto import get_proto_path
import grpc
from concurrent import futures

# Use the proto path
proto_path = get_proto_path('users')

# Setup your gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
# ... add your services
```

---

## Proto Files Structure

The proto files are located in:

```
node_modules/@keeps-learn/nexus-proto/protos/
site-packages/keeps_learn_nexus_proto/../protos/
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

---

## Update to Latest Version

### Node.js
```bash
npm update @keeps-learn/nexus-proto
```

### Python
```bash
pip install --upgrade keeps-learn-nexus-proto
```

---

## Check Installed Version

### Node.js
```bash
npm list @keeps-learn/nexus-proto
```

### Python
```bash
pip show keeps-learn-nexus-proto
```

---

## Troubleshooting

### Node.js: "Cannot find module"

```bash
npm list @keeps-learn/nexus-proto
```

If not installed:
```bash
npm install @keeps-learn/nexus-proto
```

### Python: "ModuleNotFoundError"

```bash
pip list | grep keeps-learn-nexus-proto
```

If not installed:
```bash
pip install keeps-learn-nexus-proto
```

### Proto file not found

**Node.js:**
```bash
ls -la node_modules/@keeps-learn/nexus-proto/protos/
```

**Python:**
```python
from keeps_learn_nexus_proto import get_proto_dir
import os

proto_dir = get_proto_dir()
print(f"Proto directory: {proto_dir}")
print(f"Files: {os.listdir(proto_dir)}")
```

---

## Benefits

✓ No token required for installation  
✓ Any developer can use it  
✓ Easy to update versions  
✓ Shared across multiple projects  
✓ No code duplication  
✓ Works with Python 3.7+ and Node.js 14+  


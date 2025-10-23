# Como Publicar

## 1. Atualizar versão

Editar `package.json` e atualizar o campo `version`:

```json
{
  "version": "0.2.0"
}
```

## 2. Commit

```bash
git add .
git commit -m "Bump version to 0.2.0"
```

## 3. Tag

```bash
git tag v0.2.0
```

## 4. Push

```bash
git push origin main
git push origin v0.2.0
```

## 5. Pronto!

GitHub Actions publica automaticamente em `npm.pkg.github.com`

Verificar em: https://github.com/keeps/nexus-proto/actions

## Instalar

```bash
npm install @Keeps-Learn/nexus-proto
```

## Usar

```bash
node_modules/@keeps/nexus-proto/protos/users.proto
node_modules/@keeps/nexus-proto/protos/workspaces.proto
```


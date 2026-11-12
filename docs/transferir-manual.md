# Transferir um repositório para uma organização (manual)

Passo a passo para fazer sem o gh-repo-review. Troque `DONO`, `ORG` e `REPO` pelos nomes reais.

## Antes de começar

- Você precisa ser **admin do repositório** e ter permissão para **criar repositórios na organização**.
- A organização **não pode ter** um repositório com o mesmo nome.

## 1. Transferir

**Pelo site**

1. Abra o repositório → **Settings**.
2. No fim da página, em **Danger Zone** → **Transfer ownership**.
3. Escolha **Specify an organization** → selecione `ORG`.
4. Digite o nome do repositório para confirmar → **Transfer**.

**Pelo terminal (gh)**

```
gh api -X POST repos/DONO/REPO/transfer -f new_owner=ORG
```

## 2. Atualizar o remote do clone local

Na pasta do projeto, veja o endereço atual:

```
git remote -v
```

Troque `DONO` por `ORG`, mantendo o mesmo formato:

```
# se começa com https://
git remote set-url origin https://github.com/ORG/REPO.git

# se começa com git@
git remote set-url origin git@github.com:ORG/REPO.git
```

Confira:

```
git remote -v
git fetch
```

> O GitHub redireciona o endereço antigo, então o `push` continua funcionando mesmo sem esse passo. Mas atualize mesmo assim: o redirecionamento deixa de funcionar se um dia for criado um repositório com o mesmo nome na conta antiga.

## 3. Conferir o acesso

Na organização: **REPO → Settings → Collaborators and teams**. Libere o acesso só para quem precisa.

## Desfazer

Repita o passo 1 a partir do repositório na organização, escolhendo a sua conta pessoal como destino.

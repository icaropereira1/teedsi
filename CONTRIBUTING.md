# Como contribuir

Hoje o repositório tem dois contribuidores, e cada um revisa o trabalho do outro:

| Pessoa | GitHub |
| --- | --- |
| Gabriel Camargo | @gabrielcamargo01 |
| João Gabriel Abreu | @joaogabrielabreu |

O dono do repositório é @icaropereira1.

## A regra

**Ninguém faz commit ou push direto na `main`.** Todo trabalho entra por pull request, e o
merge só acontece depois que **o outro contribuidor** aprova.

> Ninguém impõe essa regra além do grupo. Em repositório privado de conta pessoal no plano
> Free, o GitHub não deixa proteger branches, então ele não bloqueia um push direto na `main`.
> Antes de qualquer push, rode `git status` e confira em qual branch você está.

## Branches

Cada tarefa tem a própria branch, criada a partir da `main` atualizada. Use o formato
`tipo/projeto-assunto`:

```text
feat/bigplayer-win-eda
fix/ceo-investigator-cache
docs/bigplayer-status
```

Os tipos são os mesmos dos commits (veja abaixo). Branch é de uma pessoa só: não faça commit
na branch do colega.

## Commits

Use o padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/), com o projeto
como escopo:

```text
feat(bigplayer): carga, split com hold-out trancado e qualidade dos dados
docs(bigplayer): registra decisões (buracos nos dados, nomes dos arquivos)
fix(ceo_investigator): ...
```

Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

## Terminei os ajustes: como abrir o PR

### 1. Feche o que está pendente

```bash
git status
git add <arquivos>          # adicione arquivo por arquivo; evite "git add ."
git commit -m "feat(bigplayer): ..."
```

`git add .` é perigoso aqui porque a raiz tem coisas que não devem ser versionadas (veja
[O que não entra](#o-que-não-entra)).

### 2. Traga a `main` mais recente para a sua branch

```bash
git fetch origin
git rebase origin/main
```

Se aparecer conflito, resolva na sua branch, rode `git add <arquivo>` e depois
`git rebase --continue`. Os conflitos se resolvem na sua branch, nunca na `main`.

### 3. Rode os testes do projeto que você mexeu

```bash
cd bigplayer                # ou ceo_project/ceo_investigator
python -m pytest
```

Se mexeu num notebook, rode-o do começo ao fim. Notebook que só funciona com as células
executadas fora de ordem não é reprodutível.

### 4. Envie a branch

```bash
git push --force-with-lease origin <sua-branch>
```

O rebase reescreve os commits da sua branch, por isso o push precisa de `--force-with-lease`.
Use só na sua própria branch e **nunca na `main`**.

### 5. Abra o PR para a `main` e peça revisão ao colega

Pelo terminal, com o [GitHub CLI](https://cli.github.com/):

```bash
gh pr create --base main --reviewer <github-do-colega>
```

Pelo site, abra `https://github.com/icaropereira1/teedsi`, clique em **Compare & pull request**,
confira se a base é `main` e escolha o colega em **Reviewers**.

O título segue o padrão dos commits (`feat(bigplayer): ...`). A descrição precisa responder:

- **O que muda**, em poucas linhas.
- **Como verificar**: que comando rodar, que notebook executar, que figura conferir.
- **Resultado**, inclusive quando é negativo. "Gate 1 em M1: no-go" também é resultado.

## Revisão e merge

Quem revisa é o outro contribuidor:

1. Leia o diff e rode o que a descrição pede em **Como verificar**.
2. Registre a decisão no GitHub, em **Files changed → Review changes**:
   - **Approve** se pode entrar;
   - **Request changes** se precisa de ajuste, explicando o quê.

   Aprovação dada no chat não fica registrada no PR.
3. Depois de aprovar, **quem revisou faz o merge** com **Create a merge commit**. O autor não faz
   merge do próprio PR.
4. Apague a branch depois do merge (botão **Delete branch** no PR).

Se o revisor pediu ajuste, o autor faz novos commits na mesma branch e dá push. O PR se
atualiza sozinho.

## Depois do merge

Quem vai começar a próxima tarefa atualiza a `main` local e cria uma branch nova a partir dela:

```bash
git switch main
git pull origin main
git switch -c <tipo/projeto-assunto>
```

## O que não entra

- **`data/` da raiz**: os candles brutos (`WINN_M1`, `WDON_M1`) são compartilhados fora do git.
- **Dados derivados** (`bigplayer/data/interim/`, `processed/`, `holdout/`): são regenerados
  pelos notebooks.
- **`.venv/`**.
- **Chaves de API e credenciais**, como a `GEMINI_API_KEY` do `ceo_investigator`. Elas ficam em
  variável de ambiente, nunca em código ou em arquivo commitado.

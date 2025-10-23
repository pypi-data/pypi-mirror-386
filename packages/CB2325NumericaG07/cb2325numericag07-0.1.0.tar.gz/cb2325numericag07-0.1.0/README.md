# CB2325NumericaG07
__Trabalho AV2 de Programação 2. Grupo 07__

## Instruções para os alunos (Tutorial git):
Git é um sistema de controle de versão que ajuda a rastrear mudanças no seu código e a colaborar com outras pessoas.

### 1. Configuração Inicial (Para o primeiro uso)

* Configure seu nome e email (usados para identificar seus commits):
    ```bash
    git config --global user.name "Seu nome"
    git config --global user.email "al.nome.sobrenome@impatech.edu.br"
    ```

### 2. Clonando o Repositório

* **Para o projeto existente (remoto):** Clone o repositório da web:
    ```bash
    git clone https://github.com/Mateus-Band/CB2325NumericaG07.git
    ```

### 3. O Fluxo Básico: Modificar -> Preparar -> Salvar

* **Modifique** seus arquivos normalmente.
* **Prepare (Stage):** Escolha quais mudanças você quer salvar no repositório online.
    * Para preparar um arquivo específico:
        ```bash
        git add <nome_do_arquivo_modificado>
        ```
    * Para preparar todos os arquivos modificados/novos:
        ```bash
        git add .
        ```
* **Salve (Commit):** Crie uma versão permanente das mudanças preparadas, com uma mensagem bem descritiva.
    ```bash
    git commit -m "Sua mensagem clara sobre o que mudou (MUITO IMPORTANTE!)"
    ```
    *PARTE MAISIMPORTANTE, SUA NOTA ESTÁ EM BOA PARTE AQUI!*

### 4. Verificando o Status

* Para ver quais arquivos foram modificados, quais estão preparados (processo de commit) e quais não estão sendo rastreados:
    ```bash
    git status
    ```

### 5. Enviando para o repositórios online (GitHub)

* **Enviar seus commits:** Mande os commits locais para o repositório remoto (ex: GitHub). Geralmente, para a branch `main` ou `master`:
    ```bash
    git push origin main
    ```
* **Receber atualizações:** Baixe as últimas mudanças do repositório remoto e comece seu trabalho local:
    ```bash
    git pull origin main
    ```

### 6. Vendo o Histórico

* Para ver a lista de commits feitos:
    ```bash
    git log
    ```
* Para uma versão mais resumida:
    ```bash
    git log --oneline
    ```

### 7. Desfazendo Coisas (Avançado)

* **Descartar mudanças *não preparadas* em um arquivo:**
    ```bash
    git checkout -- <nome_do_arquivo>
    ```
* **Tirar um arquivo da área de *stage* (mas manter as mudanças):**
    ```bash
    git reset HEAD <nome_do_arquivo>
    ```

### 8. Ajuda!

* Para obter ajuda sobre qualquer comando:
    ```bash
    git help <nome_do_comando>
    # Ex: git help commit
    ```
    *Ou pergunte aos outros :-)*

---

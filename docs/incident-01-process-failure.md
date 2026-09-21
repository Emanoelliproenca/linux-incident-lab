# Incident 01 - Process Failure

## Scenario

A aplicação HTTP do laboratório estava sendo executada na porta `8080`.

Inicialmente, a aplicação era executada manualmente com:

```bash
python3 -m http.server 8080
```

Nesse cenário, o processo dependia só do terminal. Caso o processo fosse encerrado, a aplicação deixava de responder e 
não existia nenhum mecanismo responsável por iniciá-la novamente. Para melhorar esse comportamento, a aplicação foi 
transformada em um serviço gerenciado pelo `systemd`, chamado:

```text
linux-incident.service
```

---

## Investigation

### 1. Testando a aplicação

Para verificar se a aplicação estava respondendo, utilizei:

```bash
curl http://localhost:8080
```

O `curl` realiza requisições para URLs. Nesse caso, ele foi utilizado para realizar uma requisição HTTP para a aplicação local.

Quando a aplicação estava funcionando, ela retornava:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Linux Incident Lab</title>
</head>
<body>
    <h1>Linux Incident Lab</h1>
    <p>Service is running.</p>
</body>
</html>
```

Quando o processo estava parado, o `curl` retornava erro de conexão recusada.

Isso mostrava que não havia uma aplicação respondendo naquela porta.

---

### 2. Verificando a porta

Para verificar se algum processo estava escutando na porta `8080`, utilizei:

```bash
ss -tulpn | grep 8080
```

Quando a aplicação estava funcionando, obtive uma saída semelhante a:

```text
tcp LISTEN 0 5 0.0.0.0:8080 0.0.0.0:* users:(("python3",pid=73005,fd=3))
```

Isso mostrou que:

- existia um socket TCP;
- a porta `8080` estava em estado `LISTEN`;
- o processo responsável era o `python3`;
- o processo possuía um PID associado.

Quando a aplicação estava parada, o comando não retornava resultados para a porta `8080`.

---

### 3. Verificando o processo

Para verificar se um processo específico ainda existia, utilizei:

```bash
ps -p 73005
```

Quando apenas o cabeçalho do comando foi retornado e nenhuma informação sobre o PID apareceu, foi possível
 concluir que aquele processo não estava mais sendo executado.
A investigação seguiu a seguinte lógica:

```text
Aplicação indisponível
        ↓
curl localhost:8080
        ↓
Connection refused
        ↓
ss verifica a porta 8080
        ↓
Nenhum processo em LISTEN
        ↓
ps verifica o PID
        ↓
Processo não existe
        ↓
Processo responsável pela aplicação foi encerrado
```

---

## Configuração como serviço systemd

Para evitar que a aplicação dependesse diretamente de um terminal, ela foi configurada como um serviço `systemd`.

O serviço recebeu o nome:

```text
linux-incident.service
```

A configuração utilizada foi:

```ini
[Unit]
Description=Linux Incident Lab HTTP Service
After=network.target

[Service]
Type=simple
User=emanoelli-proenca
WorkingDirectory=/home/emanoelli-proenca/projetos-devops/linux-incident-lab/app
ExecStart=/usr/bin/python3 -m http.server 8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Antes da configuração, validei o caminho do Python utilizando:

```bash
which python3
```

Resultado:

```text
/usr/bin/python3
```

Após criar o arquivo do serviço, o `systemd` foi recarregado para reconhecer a nova configuração:

```bash
sudo systemctl daemon-reload
```

Depois, o serviço foi iniciado:

```bash
sudo systemctl start linux-incident.service
```

O estado do serviço foi verificado com:

```bash
systemctl status linux-incident.service --no-pager
```

O resultado mostrou:

```text
Active: active (running)
```

O processo principal naquele momento possuía o PID:

```text
73005
```

---

## Validação inicial do serviço

Não utilizei apenas o `systemctl` para concluir que a aplicação estava funcionando.

Primeiro, confirmei que o serviço estava ativo:

```bash
systemctl status linux-incident.service --no-pager
```

Depois, verifiquei se existia um processo escutando na porta `8080`:

```bash
ss -tulpn | grep 8080
```

Resultado:

```text
tcp LISTEN 0 5 0.0.0.0:8080 0.0.0.0:* users:(("python3",pid=73005,fd=3))
```

Por fim, realizei uma requisição HTTP:

```bash
curl http://localhost:8080
```

A aplicação respondeu corretamente. Dessa forma, a validação foi realizada em diferentes camadas:

```text
systemctl
    ↓
O serviço está ativo?

ss
    ↓
Existe um processo escutando na porta 8080?

curl
    ↓
A aplicação realmente responde?
```

---

## Teste de recuperação do serviço

Para verificar se o serviço estava funcionando como planejado, simulei uma falha no processo responsável pela aplicação.

Primeiro, identifiquei o PID principal do serviço:

```bash
systemctl show linux-incident.service -p MainPID
```

Resultado:

```text
MainPID=73005
```

Em seguida, encerrei propositalmente esse processo:

```bash
kill -9 73005
```

O `kill` permite enviar sinais para processos.

Nesse teste, `-9` representa o sinal `SIGKILL`, que encerra imediatamente o processo.

O objetivo era verificar o comportamento configurado no serviço:

```ini
Restart=on-failure
```

Como o processo foi encerrado de forma inesperada, o `systemd` detectou a falha e iniciou automaticamente um novo processo para a aplicação.

---

## Solution

A aplicação foi configurada como um serviço `systemd` utilizando:

```ini
Restart=on-failure
```

Essa configuração permite que o `systemd` tente reiniciar automaticamente o serviço quando o processo termina devido a uma falha.

O comportamento observado foi:

```text
Aplicação
    ↓
PID 73005
    ↓
Processo encerrado com SIGKILL
    ↓
systemd detecta a falha
    ↓
Restart=on-failure
    ↓
Novo processo iniciado
    ↓
PID 74682
    ↓
Aplicação disponível novamente
```

---

## Validation

Após a interrupção do processo, verifiquei novamente o estado do serviço:

```bash
systemctl status linux-incident.service --no-pager
```

O resultado mostrou:

```text
Active: active (running)
```

Porém, o PID havia mudado.

Antes da falha:

```text
PID 73005
```

Após a recuperação:

```text
PID 74682
```

Isso demonstrou que o processo anterior realmente havia sido encerrado e que um novo processo foi iniciado pelo `systemd`.

Também validei novamente a porta:

```bash
ss -tulpn | grep 8080
```

Resultado:

```text
tcp LISTEN 0 5 0.0.0.0:8080 0.0.0.0:* users:(("python3",pid=74682,fd=3))
```

A porta `8080` voltou ao estado `LISTEN`, agora associada ao novo processo.

---

## Análise dos logs

Para entender o que aconteceu durante a falha e confirmar a recuperação automática, utilizei:

```bash
journalctl -u linux-incident.service --since "10 minutes ago" --no-pager
```

Os logs apresentaram:

```text
Main process exited, code=killed, status=9/KILL
Failed with result 'signal'.
Scheduled restart job, restart counter is at 1.
Stopped Linux Incident Lab HTTP Service.
Started Linux Incident Lab HTTP Service.
```

A linha:

```text
Main process exited, code=killed, status=9/KILL
```

mostrou que o processo principal foi encerrado através do sinal `SIGKILL`.

Depois:

```text
Failed with result 'signal'.
```

mostrou que o `systemd` classificou o encerramento como uma falha.

Em seguida:

```text
Scheduled restart job, restart counter is at 1.
```

mostrou que o `systemd` agendou automaticamente a reinicialização do serviço.

Por fim:

```text
Stopped Linux Incident Lab HTTP Service.
Started Linux Incident Lab HTTP Service.
```

confirmou que o serviço foi iniciado novamente.

A sequência do incidente foi:

```text
Processo encerrado
        ↓
systemd detectou a falha
        ↓
Falha registrada no journal
        ↓
Restart automático agendado
        ↓
Serviço iniciado novamente
        ↓
Novo PID criado
        ↓
Porta 8080 voltou para LISTEN
```

---

## What I Learned

Durante este laboratório, pratiquei conceitos importantes de administração de serviços e troubleshooting em Linux.

### Processos e PID

Cada processo em execução possui um identificador chamado PID (Process ID).

Utilizei:

```bash
ps -p <PID>
```

para verificar se determinado processo ainda estava sendo executado.

Quando executei:

```bash
ps -p 67829
```

e apenas o cabeçalho foi apresentado, identifiquei que aquele processo não existia mais.

Também aprendi que, quando um processo é encerrado e um novo processo é iniciado, o novo processo recebe outro PID.

---

### `ps` vs `journalctl`

Aprendi a diferença entre verificar o estado atual dos processos e investigar acontecimentos registrados pelo sistema.

Uma forma simples de lembrar:

```text
ps          → O que está rodando AGORA?
journalctl  → O que aconteceu / foi registrado?
```

O `ps` é utilizado para visualizar processos existentes naquele momento.

O `journalctl` permite consultar os logs armazenados pelo `systemd-journald`, sendo útil para investigar eventos e falhas.

Para visualizar os logs de um serviço específico, utilizei:

```bash
journalctl -u linux-incident.service
```

---

### `curl`

Aprendi a utilizar o `curl` para realizar uma requisição HTTP e verificar se a aplicação realmente estava respondendo.

Exemplo:

```bash
curl http://localhost:8080
```

Quando a aplicação estava disponível, recebi seu conteúdo HTML.

Quando não havia nenhum serviço respondendo na porta `8080`, recebi:

```text
Connection refused
```

Isso me mostrou que um processo ou serviço aparecer como ativo não é, sozinho, garantia de que a aplicação esteja respondendo corretamente.

---

### `ss`

Aprendi a utilizar o `ss` para investigar sockets e portas de rede.

Principais opções utilizadas:

```text
ss    → mostra informações sobre sockets/conexões

-t    → TCP
-u    → UDP
-l    → somente sockets em estado LISTEN
-n    → mostra endereços e portas numericamente
-p    → mostra o processo associado ao socket
```

Exemplo utilizado:

```bash
ss -tulpn | grep 8080
```

Esse comando permitiu verificar:

```text
porta 8080
    ↓
estado LISTEN
    ↓
processo python3
    ↓
PID do processo
```

---

### `systemd` e `systemctl`

Aprendi que o `systemd` pode gerenciar o ciclo de vida de serviços Linux.

Com o `systemctl`, é possível executar operações como:

```bash
systemctl status <serviço>
systemctl start <serviço>
systemctl stop <serviço>
systemctl restart <serviço>
```

Neste laboratório, utilizei:

```bash
systemctl status linux-incident.service
```

para verificar o estado do serviço.

Também aprendi a diferença entre:

```text
active  → o serviço está executando neste momento

enabled → o serviço está configurado para iniciar automaticamente durante o boot
```

Portanto, um serviço pode aparecer como:

```text
active (running)
disabled
```
set 20 22:21:34 VSCOMNTSUPO101 systemd[1]: Started Linux Incident Lab HTTP Service.

Isso significa que ele está funcionando naquele momento, mas não está configurado para iniciar automaticamente quando a máquina for inicializada.

---

### `systemctl daemon-reload`

Aprendi que, após criar ou modificar um arquivo de serviço do `systemd`, é necessário fazer o `systemd` reler as configurações.

Para isso utilizei:

```bash
sudo systemctl daemon-reload
```

Depois disso, o novo serviço pôde ser iniciado e gerenciado pelo `systemctl`.

---

### PID e recuperação automática

O principal conceito praticado neste incidente foi a recuperação automática de um serviço.

Com:

```ini
Restart=on-failure
```

o `systemd` conseguiu detectar que o processo principal havia falhado e iniciou um novo processo automaticamente.

Antes de utilizar o `systemd`, o funcionamento era:

```text
Terminal
    ↓
Python
    ↓
Aplicação :8080

Processo morreu
    ↓
Aplicação ficou indisponível
```

Depois da configuração:

```text
systemd
    ↓
linux-incident.service
    ↓
Python
    ↓
Aplicação :8080

Processo falhou
    ↓
systemd detectou
    ↓
novo processo
    ↓
aplicação voltou
```

---

## Troubleshooting Mental Model

O principal foco neste laboratório foi investigar uma indisponibilidade através de diferentes camadas.

Em vez de simplesmente reiniciar a aplicação, busquei evidências para entender o problema.

O fluxo utilizado foi:

```text
Aplicação apresenta problema
        ↓
curl
        ↓
A aplicação responde?
        ↓
ss
        ↓
Existe algo escutando na porta?
        ↓
ps
        ↓
O processo existe?
        ↓
systemctl
        ↓
Qual é o estado do serviço?
        ↓
journalctl
        ↓
O que aconteceu com o serviço?
        ↓
Identificação da causa
        ↓
Correção
        ↓
Validação
```

Assim, aprendi a seguir uma lógica de troubleshooting baseada em:

```text
Sintoma
   ↓
Investigação
   ↓
Evidência
   ↓
Causa
   ↓
Correção
   ↓
Validação
```

O laboratório também mostrou que diferentes ferramentas respondem perguntas diferentes:

```text
ps
→ O processo existe agora?

systemctl
→ Qual é o estado do serviço?

ss
→ Existe algo escutando na porta?

curl
→ A aplicação realmente responde?

journalctl
→ O que aconteceu com o serviço?
```

Isso evita depender de apenas uma informação para concluir se uma aplicação está funcionando corretamente.

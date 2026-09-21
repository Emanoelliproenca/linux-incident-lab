# Linux Incident Lab

Laboratório prático de Linux criado para simular, investigar e solucionar incidentes em uma aplicação executada como serviço.

O objetivo deste projeto é desenvolver habilidades práticas de **troubleshooting, administração Linux, gerenciamento de processos, systemd, análise de logs e redes**, aplicando uma metodologia de investigação baseada em evidências.

---

## Objetivo

Simular situações próximas às encontradas em ambientes de infraestrutura e operações, investigando problemas através de ferramentas nativas do Linux.

Neste primeiro incidente, uma aplicação HTTP simples foi executada inicialmente de forma manual e posteriormente transformada em um serviço gerenciado pelo `systemd`.

Também foi simulada uma falha no processo da aplicação para analisar como o sistema identifica o problema e realiza sua recuperação automática.

---

## Arquitetura do laboratório

```text
systemd
   ↓
linux-incident.service
   ↓
Python HTTP Server
   ↓
TCP :8080
   ↓
index.html
```

O serviço executa:

```bash
python3 -m http.server 8080
```

A aplicação fica disponível através da porta TCP `8080`.

---

## Incidente simulado

Foi realizada a interrupção proposital do processo responsável pela aplicação.

Fluxo do incidente:

```text
Aplicação funcionando
        ↓
Processo Python em execução
        ↓
Processo encerrado
        ↓
systemd detecta a falha
        ↓
Restart=on-failure
        ↓
Novo processo iniciado
        ↓
Aplicação disponível novamente
```

Durante o teste:

```text
PID anterior: 73005
Novo PID:     74682
```

A alteração do PID confirmou que o processo original foi encerrado e que um novo processo foi iniciado pelo `systemd`.

---

## Troubleshooting

A investigação foi realizada em diferentes camadas.

### Verificação da aplicação

```bash
curl http://localhost:8080
```

Utilizado para verificar se a aplicação realmente estava respondendo através de HTTP.

### Verificação da porta

```bash
ss -tulpn | grep 8080
```

Utilizado para verificar:

- se a porta `8080` estava em estado `LISTEN`;
- qual processo estava utilizando a porta;
- qual era o PID associado ao processo.

Principais opções utilizadas:

```text
-t → TCP
-u → UDP
-l → sockets em LISTEN
-p → processo associado ao socket
-n → endereços e portas em formato numérico
```

### Verificação de processos

```bash
ps -p <PID>
```

Utilizado para verificar se determinado processo ainda estava sendo executado.

### Verificação do serviço

```bash
systemctl status linux-incident.service
```

Utilizado para consultar o estado do serviço gerenciado pelo `systemd`.

### Análise de logs

```bash
journalctl -u linux-incident.service
```

Utilizado para investigar os eventos registrados durante a falha.

Os logs mostraram:

```text
Main process exited, code=killed, status=9/KILL
Failed with result 'signal'.
Scheduled restart job, restart counter is at 1.
Stopped Linux Incident Lab HTTP Service.
Started Linux Incident Lab HTTP Service.
```

Essas informações permitiram acompanhar desde a interrupção do processo até sua recuperação automática.

---

## Serviço systemd

O arquivo do serviço está disponível em:

```text
systemd/linux-incident.service
```

Configuração:

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

A configuração:

```ini
Restart=on-failure
```

permite que o `systemd` tente iniciar novamente o serviço caso o processo seja encerrado devido a uma falha.

---

## Metodologia de troubleshooting

Durante o laboratório, utilizei o seguinte raciocínio:

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

Cada ferramenta responde a uma pergunta diferente durante a investigação:

| Ferramenta | Pergunta |
|---|---|
| `curl` | A aplicação está respondendo? |
| `ss` | Existe algo escutando na porta? |
| `ps` | O processo existe? |
| `systemctl` | Qual é o estado do serviço? |
| `journalctl` | O que aconteceu com o serviço? |

Isso permite investigar um incidente utilizando evidências em vez de simplesmente reiniciar a aplicação sem identificar o problema.

---

## Estrutura do projeto

```text
linux-incident-lab/
│
├── app/
│   └── index.html
│
├── docs/
│   └── incident-01-process-failure.md
│
├── systemd/
│   └── linux-incident.service
│
└── README.md
```

### `app/`

Contém a aplicação HTTP utilizada no laboratório.

### `docs/`

Contém a documentação detalhada dos incidentes simulados, incluindo investigação, evidências, causa e validação.

### `systemd/`

Contém o arquivo utilizado para configurar a aplicação como serviço Linux.

---

## Tecnologias e ferramentas

- Linux
- Ubuntu
- systemd
- systemctl
- journalctl
- Python
- HTTP
- TCP/IP
- curl
- ss
- ps
- Git
- GitHub

---

## Principais aprendizados

Durante o desenvolvimento deste laboratório pratiquei:

- gerenciamento de processos Linux e PID;
- investigação de portas e sockets;
- requisições HTTP com `curl`;
- criação e gerenciamento de serviços com `systemd`;
- análise de logs com `journalctl`;
- diferença entre processo, serviço e aplicação;
- recuperação automática com `Restart=on-failure`;
- investigação de incidentes baseada em evidências;
- versionamento com Git e publicação no GitHub.

Um dos principais aprendizados foi entender que apenas verificar se um serviço está `active (running)` não é suficiente para afirmar que uma aplicação está saudável.

Uma validação pode envolver diferentes camadas:

```text
systemctl
    ↓
Serviço está ativo?

ss
    ↓
Porta está em LISTEN?

curl
    ↓
Aplicação responde?

journalctl
    ↓
O que aconteceu?
```

---

## Documentação do incidente

A investigação completa do primeiro incidente está documentada em:

[`docs/incident-01-process-failure.md`](docs/incident-01-process-failure.md)

---

## Autora

**Emanoelli Proença**

Estudante de Análise e Desenvolvimento de Sistemas, com experiência em suporte técnico e operações e foco no desenvolvimento de conhecimentos em **Infraestrutura, Cloud e DevOps**.

Este projeto faz parte do meu roadmap prático de evolução em infraestrutura e DevOps.

## Descrição do Problema
Atualmente, é possível notar que, devido ao aumento da população brasileira, os serviços da área da saúde para a população podem sofrer uma precarização, uma vez que a mão de obra e a tecnologia podem não acompanhar esse crescimento. Como uma das consequências, ocorre uma possível falta de acompanhamento de pacientes ao longo prazo, tendo em vista que, um médico/clínica que recebe dezenas de pacientes por dia pode ser incapaz de armazenar e interpretar todas as informações relevantes de maneira eficiente. Para resolver esse problema, proponho um registro do estado do paciente a curto, médio e possivelmente a longo prazo, para armazenar as informações relevantes do paciente, de maneira que o médico e o paciente possam colocar informações sobre o estado desse. Além disso, nesse sistema, também terá a presença de um agente de IA, que irá monitorar esse registro, podendo dar um resumo sobre o que aconteceu nas consultas passadas e no tempo entre elas, avisar ao médico sobre algum evento importante, ajudar o paciente a se automonitorar e poder auxiliar 


## Descrição do Projeto
Este projeto implementa um MVP de acompanhamento longitudinal de pacientes, com registro de consultas, agenda, comunicação via WhatsApp e apoio clínico ao médico. O objetivo é reduzir a perda de informação entre consultas e agilizar a tomada de decisão clínica com resumos, sugestões e busca de evidências científicas.

## Descrição da arquitetura do sistema:
O sistema possuirá 3 agentes, o 'agente_paciente', o 'agente_medico' e 'agente_contexto'. 

O agente_paciente receberá e mandará mensagens por meio do whatsapp, usando a API waha, com o papel de atender o paciente e com a ferramenta 'post_estado', que é capaz de mandar para o arquivo que está com todos os dados uma observação dada pelo paciente. Além disso, também terá a função 'mandar_alerta', que manda um alerta ao medico ao perceber uma situação emergencial vindo do registro do paciente. Além disso, também terá o 'agente_contexto' como subagente.

O 'agente_medico' terá o papel de auxiliar o médico a vizualizar a situação do paciente, com as ferramentas 'dar_sugestao', que vai analisar todo o processo e dá uma sugestão ao médico sobre o que fazer, e 'dar_resumo', que vai analisar todo o processo do paciente e dar um resumo ao medico. Além disso, também possuirá a ferramenta usada no projeto passado, de retornar artigos relacionados ao quadro do paciente, e também terá o 'agente_contexto' como subagente.

O 'agente_contexto' terá o papel de recuperar as informações do registro do paciente de maneira padronizada e unificada, para enviar para os outros agentes.



## Tecnologias Utilizadas
- Python 3
- Streamlit (UI do prontuário e chatbot do médico)
- Google ADK (agentes)
- FastAPI (webhook de WhatsApp)
- Waha (gateway WhatsApp)
- Mistral (embeddings)
- Qdrant (busca vetorial)

## Instalação de Dependências
1. Crie e ative o ambiente virtual.
2. Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

## Configuração (.env)
Crie/ajuste o arquivo `Projeto_final/.env` com as variáveis necessárias:

```
WAHA_URL=http://localhost:3000
WAHA_SESSION=default
WAHA_API_KEY=

MISTRAL_API_KEY=
QDRANT_URL=
QDRANT_API_KEY=
GROQ_API_KEY=
```

Configure o webhook do Waha para apontar para:

```
http://SEU_HOST:8000/webhook
```

### Implementação da Validação de Dados Essencial com Pydantic
No fluxo de cadastro de pacientes, os dados críticos (nome, CPF, idade, WhatsApp, sexo e histórico) passam por validação básica antes de serem persistidos. Essa validação garante formato mínimo, campos obrigatórios e consistência dos dados.

### Aplicação de Embeddings para uma Funcionalidade Específica
O MVP utiliza embeddings para buscar artigos relevantes relacionados ao quadro do paciente. A geração de embeddings e a consulta vetorial são usadas para recuperar conteúdos semelhantes e apoiar o médico com evidências científicas.

### Orquestração de Multiagentes para a Funcionalidade Principal
O sistema opera com múltiplos agentes especializados (paciente, médico e contexto), cada um com responsabilidades claras. Atualmente não há orquestrador central: as chamadas aos agentes são feitas diretamente a partir da UI e do webhook. 

### Criação de uma Interface de Usuário Simples com Streamlit
O MVP conta com uma interface simples em Streamlit para cadastro de pacientes, registro de consultas e interação com o agente médico via chat. As instruções de execução estão descritas neste README. 

### Consideração da Integração com Comunicação
A comunicação com o paciente é feita via WhatsApp, com webhook que recebe mensagens e envia respostas através do Waha. A configuração necessária está descrita nas seções de `.env` e execução.

### Desenvolvimento e Teste do MVP
O MVP foi desenvolvido com integração entre UI, webhook, agentes e busca de evidências por embeddings. A validação de dados com Pydantic faz parte do fluxo de cadastro. 


## Detalhamento Técnico
O MVP utiliza múltiplos agentes (Google ADK) com funções especializadas:
- Agente paciente: recebe mensagens via WhatsApp (Waha), registra observações e pode acionar alertas.
- Agente médico: gera resumos e sugestões com base no prontuário e permite buscar artigos científicos relacionados ao caso.
- Agente contexto: normaliza e entrega dados estruturados do prontuário para os demais agentes.

Embeddings e similaridade:
- Embeddings gerados com `mistral-embed` (Mistral).
- Similaridade vetorial via Qdrant, retornando os 3 artigos mais relevantes.
 - O script de geração de embeddings está em `Desafio/Embeddings.py` e foi copiado para `Projeto_final/Embeddings.py`.

RAG e sumarização:
- O agente médico utiliza o contexto do prontuário e os artigos recuperados para responder às perguntas do médico de forma contextual.

Multi-agents e orquestração:
- Os agentes são instanciados via Google ADK e usados diretamente (sem orquestrador), com o UI acionando o agente médico e o webhook acionando o agente paciente.

Integrações:
- Streamlit para UI.
- FastAPI para o webhook do WhatsApp.
- Waha como gateway WhatsApp.
- Qdrant para busca vetorial.
- Mistral para embeddings.

## Resultados Obtidos
Exemplos práticos:
- O médico pede um resumo: "resumo do CPF 12345678901" e recebe um resumo consolidado do prontuário.
- O médico pede sugestão: "sugestao para CPF 12345678901" e recebe uma orientação inicial.
- O médico pede evidências: "artigos sobre hipertensao resistente" e recebe artigos relevantes via busca vetorial.
- O paciente envia observações via WhatsApp, que são registradas no prontuário e exibidas na UI.

## Instruções de Uso
1. Clonar o repositório e entrar na pasta do projeto:

```bash
git clone <URL_DO_REPOSITORIO>
cd Fastcamp_de_agentes_inteligentes/Projeto_final
```

2. Criar e ativar o ambiente virtual, depois instalar dependências:

```bash
pip install -r requirements.txt
```

3. Configurar o `.env` (veja a seção "Configuração (.env)").

4. Executar a UI:

```bash
streamlit run UI.py
```

5. Executar o webhook do WhatsApp:

```bash
uvicorn api:app --reload --port 8000
```

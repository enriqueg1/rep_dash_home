# 💰 Home Finanças - Dashboard Financeiro Residencial

Este é um dashboard financeiro residencial moderno e premium desenvolvido em **Python** utilizando a biblioteca **Streamlit**. Ele se conecta de forma robusta e em tempo real a uma planilha ou arquivo CSV hospedado no **Google Drive** por meio da API oficial do Google utilizando uma **Service Account** (Conta de Serviço).

## 🚀 Recursos Principais

- **Visual Premium**: Design minimalista e sofisticado utilizando tipografia moderna (`Plus Jakarta Sans`), gradientes dinâmicos e cards de métricas responsivos com efeitos glassmorphic.
- **Integração com Google Drive API**: Carregamento seguro diretamente da nuvem usando arquivo `credentials.json` e ID do arquivo.
- **Gráficos Interativos**: Visualização dinâmica em Plotly da distribuição de gastos por categoria e comparação entre despesas pagas e pendentes.
- **Tabela de Contas Ordenada**: Listagem automatizada das próximas contas a vencer ordenada pela data de vencimento mais próxima com formatação regional de moedas e datas.
- **Tratamento de Erros Robusto**: Alertas informativos detalhados caso ocorram falhas de conexão, credenciais incorretas ou erros de formatação de colunas.
- **Modo de Demonstração Integrado**: Permite rodar e testar a aplicação imediatamente usando dados locais pré-configurados caso você ainda não tenha configurado as chaves do Google API.

---

## 📋 Estrutura do Arquivo CSV

Para que o dashboard funcione perfeitamente, o seu arquivo CSV no Google Drive deve possuir exatamente a seguinte estrutura e nomes de colunas:

| Descrição | Valor | Vencimento | Efetivação | Categoria | Conta |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Aluguel | 2200,00 | 10/05/2026 | 10/05/2026 | Habitação | Corrente |
| Energia Elétrica | 185,40 | 22/05/2026 | - | Serviços Públicos | Corrente |

### Regras de Negócio e Processamento:
1. **Pendente / A Pagar**: Um registro é considerado "Pendente" se a coluna `Efetivação` estiver vazia (NaN), contiver `-`, ou for um espaço em branco.
2. **Paga**: Um registro é considerado "Pago" se a coluna `Efetivação` contiver uma data válida (ex: `10/05/2026`).
3. **Valores Numéricos**: A coluna `Valor` é limpa automaticamente, removendo símbolos de moeda (`R$`), pontos de milhar e convertendo vírgulas em pontos decimais.
4. **Formato de Datas**: A coluna `Vencimento` e `Efetivação` devem seguir o padrão brasileiro **DD/MM/AAAA**.

---

## 🔑 Passo a Passo para Configurar a Google Drive API

Siga estas etapas para gerar suas credenciais e integrar com o Google Drive:

### 1. Criar um Projeto e Service Account no Google Cloud
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um novo projeto ou selecione um existente.
3. No menu lateral, acesse **APIs e Serviços** > **Biblioteca**.
4. Procure por **Google Drive API** e clique em **Ativar**.
5. No menu lateral, acesse **APIs e Serviços** > **Credenciais**.
6. Clique em **+ Criar Credenciais** e selecione **Conta de serviço** (Service Account).
7. Preencha os detalhes da conta de serviço e clique em **Criar e Continuar** (pode pular os passos opcionais de atribuição de papéis).
8. Após criada, clique sobre o e-mail da conta de serviço gerada na tabela.
9. Vá até a aba **Chaves** (Keys), clique em **Adicionar Chave** > **Criar nova chave**.
10. Selecione o formato **JSON** e clique em **Criar**. O download do arquivo começará automaticamente.
11. Renomeie o arquivo baixado para `credentials.json` e salve-o na pasta raiz deste projeto.

### 2. Compartilhar seu CSV com a Service Account
1. Abra o arquivo `credentials.json` e localize o campo `"client_email"` (ex: `sua-conta-de-servico@seu-projeto.iam.gserviceaccount.com`).
2. Acesse o seu Google Drive e encontre o arquivo CSV das suas finanças.
3. Clique com o botão direito no arquivo > **Compartilhar**.
4. Cole o e-mail da service account copiado no passo 1 e certifique-se de dar a permissão de **Leitor** (Viewer).
5. Salve o compartilhamento.

### 3. Obter o ID do Arquivo
1. Com o arquivo CSV aberto no Google Drive ou na visualização da URL de compartilhamento, copie o ID longo presente na URL.
   * *Exemplo de URL:* `https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view?usp=sharing`
   * *O ID do arquivo é:* `1A2B3C4D5E6F7G8H9I0J`
2. Cole esse ID na barra lateral do dashboard do Streamlit.

---

## 🛠️ Como Instalar e Executar o Dashboard Localmente

Certifique-se de ter o Python 3.9+ instalado no seu computador.

1. Abra o seu terminal de comando na pasta do projeto.
2. Instale as dependências listadas no `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o servidor de desenvolvimento do Streamlit:
   ```bash
   streamlit run app.py
   ```
4. O navegador abrirá automaticamente em [http://localhost:8501](http://localhost:8501) exibindo o painel financeiro.

---

## 💡 Dicas de Uso

- **Troca Rápida de Fontes**: Use a barra lateral para alternar rapidamente entre o **Modo Demonstração** (com dados pré-carregados para ver o app funcionando instantaneamente) e o **Modo Produção** (conectado à sua planilha real).
- **Upload Dinâmico**: Você pode carregar o arquivo `credentials.json` diretamente pelo navegador usando o carregador de arquivos na barra lateral, sem precisar colocá-lo na pasta antes de rodar o app.
- **Gráficos Responsivos**: Clique nos itens da legenda dos gráficos interativos para filtrar ou focar em categorias específicas em tempo real.

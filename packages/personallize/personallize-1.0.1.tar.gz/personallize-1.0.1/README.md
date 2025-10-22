# Personallize

Uma biblioteca Python com ferramentas essenciais para desenvolvimento de RPA (Robotic Process Automation) e/ou ML (Machine Learning), oferecendo recursos para conexão com bancos de dados, logging, estruturação de projetos, ORM e monitoramento de performance.

## 📋 Requisitos

- Python >= 3.13
- Selenium >= 4.0.0
- SQLAlchemy >= 2.0.0
- Rich >= 12.0.0

## 📦 Instalação

### Com pip

```bash
pip install personallize
```

### Com uv (recomendado)

```bash
uv add personallize
```

### Para desenvolvimento

```bash
# Com pip
pip install personallize[dev]

# Com uv
uv add personallize --optional dev
```

## 🚀 Uso Básico

```python
from personallize import Connection, Credentials, LogManager

# Exemplo de uso da conexão com banco de dados
credentials = Credentials(
    host='localhost',
    database='exemplo.db',
    username='user',
    password='password'
)
conn = Connection('sqlite', credentials)

# Exemplo de uso do sistema de logging simples
log_manager = LogManager()
logger, exception_decorator = log_manager.get_simple_logger(__name__)
logger.info("Aplicação iniciada")

# Exemplo de uso do sistema de logging avançado (complex_log)
from personallize.complex_log import LogManager as ComplexLogManager, LogConfig

# Configuração simples (apenas console)
config = LogConfig.simple()
complex_manager = ComplexLogManager(config)
logger, decorator = complex_manager.get_simple_logger("my_app")
logger.info("Sistema iniciado com logging avançado")

# Usando get_logger (com nomeação automática de arquivos por data/hora)
logger, decorator = complex_manager.get_logger("my_app", "custom_logs")
logger.info("Log com estrutura automática de diretórios")

# Configuração para produção (com arquivo e queue)
prod_config = LogConfig.production()
prod_manager = ComplexLogManager(prod_config)
logger, decorator = prod_manager.get_simple_logger("prod_app", "app.log")
logger.info("Sistema em produção")
```

## 🚀 Recursos

### 📊 Connection

Módulo flexível para conexão com diversos bancos de dados:

- SQLite
- MySQL
- PostgreSQL
- SQL Server

### 📝 Logs

Sistema de logging com duas opções:

**Simple Log (`simple_log`):**
- Logging básico e direto
- Ideal para projetos simples

**Complex Log (`complex_log`):**
- Sistema avançado com configurações flexíveis
- Presets: `simple()`, `development()`, `production()`
- Suporte a queue para logging assíncrono
- Gerar logs em arquivo
- Personalização completa de formatos e níveis de log
- Decorators para captura de exceções
- **Métodos disponíveis:**
  - `get_simple_logger()`: Logging direto com nome de arquivo específico
  - `get_logger()`: Logging com estrutura automática de diretórios por data/hora
  - `get_logger_with_config()`: Logging com configuração explícita

### 🏗️ Make Structure

Gerador de estruturas de projeto:

- MVC simplificado
- Estrutura para projetos ML
- Estruturas personalizadas via configuração

*Nota: Este módulo está temporariamente desabilitado na versão atual.*

### 🔄 ORM

Mapeamento Objeto-Relacional simplificado:

- Criação de entidades a partir de DataFrames
- Mapeamento de tabelas existentes

*Nota: Este módulo está temporariamente desabilitado na versão atual.*

### ⚡ Performance

Decorators para monitoramento de performance:

- Medição de tempo de execução
- Monitoramento de uso de memória RAM

*Nota: Este módulo está temporariamente desabilitado na versão atual.*

### 🌐 WebDriver

Ferramentas para automação web:

- Gerenciamento customizado do ChromeDriver
- Manipulação avançada de WebDriver
- Integração com Selenium

*Nota: Este módulo está temporariamente desabilitado na versão atual.*

## 📋 Requisitos

- Python >= 3.13
- Selenium >= 4.0.0
- SQLAlchemy >= 2.0.0
- Rich >= 12.0.0

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**Miguel Tenório**

- Email: `deepydev42@gmail.com`
- GitHub: [@MiguelTenorio42](https://github.com/MiguelTenorio42)

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, sinta-se à vontade para submeter um Pull Request.

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
from personallize import Connection, LogManager, FactoryEntity
import personallize as pz

# Exemplo de uso da conexão com banco de dados
conn = Connection('sqlite', database='exemplo.db')

# Exemplo de uso do sistema de logging
logger = pz.get_logger(__name__)
logger.info("Aplicação iniciada")
```

## 🚀 Recursos

### 📊 Connection

Módulo flexível para conexão com diversos bancos de dados:

- SQLite
- MySQL
- PostgreSQL
- SQL Server

### 📝 Logs

Sistema de logging avançado com capacidade de:

- Gerar logs em arquivo
- Registrar logs em banco de dados (quando integrado com Connection)
- Personalização de formatos e níveis de log

### 🏗️ Make Structure

Gerador de estruturas de projeto:

- MVC simplificado
- Estrutura para projetos ML
- Estruturas personalizadas via configuração

### 🔄 ORM

Mapeamento Objeto-Relacional simplificado:

- Criação de entidades a partir de DataFrames
- Mapeamento de tabelas existentes

### ⚡ Performance

Decorators para monitoramento de performance:

- Medição de tempo de execução
- Monitoramento de uso de memória RAM

### 🌐 WebDriver

Ferramentas para automação web:

- Gerenciamento customizado do ChromeDriver
- Manipulação avançada de WebDriver
- Integração com Selenium

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

# match-comments-service

Este repositório contém o serviço **match-comments**, desenvolvido com **FastAPI**. O serviço é responsável pelo gerenciamento de partidas ao vivo, comentários de lances e chats ao vivo relacionados às partidas.

## Funcionalidades

- **Gerenciamento de Partidas Ao Vivo:** Gerencia os jogos não iniciados e aovivo, ao finalizar sincroniza os resultados com o serviço de competições.
- **Comentários dos Lances:** Permite registrar e exibir comentários em tempo real sobre os lances das partidas.
- **Chat ao Vivo:** Comunicação em tempo real entre os usuários durante as partidas.

## Tecnologias

- [FastAPI](https://fastapi.tiangolo.com/)
- Python 3.x

## Como executar

1. Clone o repositório:
   ```bash
   git clone https://github.com/ifsports/match-comments-service.git
   cd match-comments-service
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o serviço:
   ```bash
   uvicorn main:app --reload
   ```

O serviço estará disponível em [http://localhost:8000](http://localhost:8000).

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## Licença

Este projeto está sob a licença MIT.

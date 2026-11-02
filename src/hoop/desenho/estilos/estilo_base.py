from abc import ABC, abstractmethod


class EstiloGrafico(ABC):
    """Um estilo tem duas responsabilidades separadas:

    - extração de valor (``extrair``): lê a grandeza do eixo y de um
      resultado (``ResultadoMecanico``/``ResultadoCondutividade``) ou de um
      modelo já calculado pela API antiga; é o que ``hoop.homogenizacao.varredura.varrer`` recebe;
    - configuração de eixo (``titulo``, ``rotulo_x``, ``rotulo_y`` e
      ``configurar_eixos``): usada apenas pelo pacote ``hoop.desenho``.

    Para adicionar novo estilo: criar subclasse + EstiloRegistry.registrar().
    """

    analise_tipo = 'mecanica'
    rotulo_x = 'Fração Volumétrica de Inclusão (fi)'

    @property
    @abstractmethod
    def nome(self) -> str:
        """Identificador string do estilo (ex: 'fixar_fracao')."""

    @property
    @abstractmethod
    def titulo(self) -> str:
        """Título do gráfico."""

    @property
    @abstractmethod
    def rotulo_y(self) -> str:
        """Rótulo do eixo y."""

    @abstractmethod
    def extrair(self, modelo) -> float:
        """Devolve a grandeza do eixo y lida de um resultado (ou modelo já calculado)."""

    def configurar_eixos(self, ax, titulo: str = None) -> None:
        """Aplica título, xlabel e ylabel ao eixo matplotlib recebido."""
        ax.set_title(titulo or self.titulo)
        ax.set_xlabel(self.rotulo_x)
        ax.set_ylabel(self.rotulo_y)

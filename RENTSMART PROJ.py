"""RentSmart - Sistema de Orçamento de Locação da R.M Imóveis.

Calcula o orçamento de locação (apartamento, casa ou estúdio), mostra o
resumo na tela e gera um CSV com a projeção dos 12 primeiros meses.
"""

import csv
from abc import ABC, abstractmethod
import os


def formatar_moeda(valor):
    """Formata um número como moeda brasileira. Ex.: 1140.5 -> 'R$ 1.140,50'."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


# ---------------------------------------------------------------------------
# Imóveis
# ---------------------------------------------------------------------------
class Imovel(ABC):
    """Classe base: o aluguel é sempre base + adicionais - desconto."""

    def __init__(self, nome, aluguel_base):
        self._nome = nome
        self._aluguel_base = aluguel_base

    @property
    def nome(self):
        return self._nome

    @property
    def aluguel_base(self):
        return self._aluguel_base

    @abstractmethod
    def calcular_adicionais(self):
        """Cada tipo de imóvel calcula seus próprios adicionais."""

    def calcular_desconto(self):
        """Por padrão não há desconto."""
        return 0.0

    def calcular_aluguel_mensal(self):
        total = self._aluguel_base + self.calcular_adicionais()
        return round(total - self.calcular_desconto(), 2)

    def detalhar(self):
        """Linhas (descrição, valor) usadas no resumo do orçamento."""
        linhas = [(f"Aluguel-base ({self._nome})", self._aluguel_base)]
        linhas += self._detalhar_adicionais()
        desconto = self.calcular_desconto()
        if desconto > 0:
            linhas.append(("Desconto de 5% (sem crianças)", -desconto))
        return linhas

    @abstractmethod
    def _detalhar_adicionais(self):
        """Linhas de cada adicional aplicado."""


class Apartamento(Imovel):
    ALUGUEL_BASE = 700.00
    ADICIONAL_2_QUARTOS = 200.00
    ADICIONAL_GARAGEM = 300.00
    PERCENTUAL_DESCONTO = 0.05

    def __init__(self, quartos, garagem, tem_criancas):
        if quartos not in (1, 2):
            raise ValueError("Apartamento aceita 1 ou 2 quartos.")
        super().__init__("Apartamento", self.ALUGUEL_BASE)
        self._quartos = quartos
        self._garagem = garagem
        self._tem_criancas = tem_criancas

    def calcular_adicionais(self):
        return sum(valor for _, valor in self._detalhar_adicionais())

    def calcular_desconto(self):
        if self._tem_criancas:
            return 0.0
        base_desconto = self._aluguel_base + self.calcular_adicionais()
        return round(base_desconto * self.PERCENTUAL_DESCONTO, 2)

    def _detalhar_adicionais(self):
        linhas = []
        if self._quartos == 2:
            linhas.append(("Adicional de 2 quartos", self.ADICIONAL_2_QUARTOS))
        if self._garagem:
            linhas.append(("Vaga de garagem", self.ADICIONAL_GARAGEM))
        return linhas


class Casa(Imovel):
    ALUGUEL_BASE = 900.00
    ADICIONAL_2_QUARTOS = 250.00
    ADICIONAL_GARAGEM = 300.00

    def __init__(self, quartos, garagem):
        if quartos not in (1, 2):
            raise ValueError("Casa aceita 1 ou 2 quartos.")
        super().__init__("Casa", self.ALUGUEL_BASE)
        self._quartos = quartos
        self._garagem = garagem

    def calcular_adicionais(self):
        return sum(valor for _, valor in self._detalhar_adicionais())

    def _detalhar_adicionais(self):
        linhas = []
        if self._quartos == 2:
            linhas.append(("Adicional de 2 quartos", self.ADICIONAL_2_QUARTOS))
        if self._garagem:
            linhas.append(("Vaga de garagem", self.ADICIONAL_GARAGEM))
        return linhas


class Estudio(Imovel):
    ALUGUEL_BASE = 1200.00
    PACOTE_VAGAS = 250.00      # inclui as 2 primeiras vagas
    VAGAS_NO_PACOTE = 2
    VAGA_ADICIONAL = 60.00

    def __init__(self, vagas):
        if vagas < self.VAGAS_NO_PACOTE:
            raise ValueError("O estúdio tem no mínimo 2 vagas (pacote inicial).")
        super().__init__("Estúdio", self.ALUGUEL_BASE)
        self._vagas = vagas

    def calcular_adicionais(self):
        return sum(valor for _, valor in self._detalhar_adicionais())

    def _detalhar_adicionais(self):
        linhas = [("Pacote de 2 vagas de estacionamento", self.PACOTE_VAGAS)]
        extras = self._vagas - self.VAGAS_NO_PACOTE
        if extras > 0:
            linhas.append((f"{extras} vaga(s) adicional(is) x {formatar_moeda(self.VAGA_ADICIONAL)}",
                           extras * self.VAGA_ADICIONAL))
        return linhas


# ---------------------------------------------------------------------------
# Orçamento e exportação
# ---------------------------------------------------------------------------
class Orcamento:
    TAXA_CONTRATUAL = 2000.00
    MAX_PARCELAS = 5

    def __init__(self, imovel, parcelas_taxa):
        if not 1 <= parcelas_taxa <= self.MAX_PARCELAS:
            raise ValueError("A taxa pode ser paga em 1 a 5 parcelas.")
        self._imovel = imovel
        self._parcelas_taxa = parcelas_taxa

    def valor_parcela_taxa(self, numero_parcela):
        """Valor da parcela (1..n). A última absorve a diferença de centavos."""
        taxa_centavos = round(self.TAXA_CONTRATUAL * 100)
        parcela_centavos = taxa_centavos // self._parcelas_taxa
        if numero_parcela == self._parcelas_taxa:
            parcela_centavos = taxa_centavos - parcela_centavos * (self._parcelas_taxa - 1)
        return parcela_centavos / 100

    def projetar_12_meses(self):
        """Lista de (mês, aluguel, parcela da taxa, total do mês)."""
        aluguel = self._imovel.calcular_aluguel_mensal()
        projecao = []
        for mes in range(1, 13):
            parcela = self.valor_parcela_taxa(mes) if mes <= self._parcelas_taxa else 0.0
            projecao.append((mes, aluguel, parcela, round(aluguel + parcela, 2)))
        return projecao

    def gerar_resumo(self):
        linhas = ["", "=" * 54, "          ORÇAMENTO DE LOCAÇÃO - R.M IMÓVEIS", "=" * 54,
                  "ALUGUEL MENSAL"]
        for descricao, valor in self._imovel.detalhar():
            sinal = "-" if valor < 0 else " "
            linhas.append(f"  {descricao:<40}{sinal}{formatar_moeda(abs(valor)):>12}")
        linhas.append("-" * 54)
        linhas.append(f"  {'Aluguel mensal':<41}{formatar_moeda(self._imovel.calcular_aluguel_mensal()):>12}")
        linhas.append("")
        linhas.append("TAXA CONTRATUAL (cobrada à parte do aluguel)")
        linhas.append(f"  {'Valor total da taxa':<41}{formatar_moeda(self.TAXA_CONTRATUAL):>12}")
        if self._parcelas_taxa == 1:
            linhas.append(f"  {'Pagamento':<41}{'à vista':>12}")
        else:
            linhas.append(f"  {'Parcelamento':<41}{self._parcelas_taxa:>10}x")
            linhas.append(f"  {'Valor da parcela':<41}{formatar_moeda(self.valor_parcela_taxa(1)):>12}")
            ultima = self.valor_parcela_taxa(self._parcelas_taxa)
            if ultima != self.valor_parcela_taxa(1):
                linhas.append(f"  {'Última parcela (ajuste de centavos)':<41}{formatar_moeda(ultima):>12}")
        total = sum(item[3] for item in self.projetar_12_meses())
        linhas.append("")
        linhas.append(f"  {'TOTAL PREVISTO EM 12 MESES':<41}{formatar_moeda(total):>12}")
        linhas.append("=" * 54)
        return "\n".join(linhas)


class ExportadorCSV:
    def __init__(self, caminho="projecao_12_meses.csv"):
        # Salva na mesma pasta do rentsmart.py, não importa de onde o programa seja executado
        pasta = os.path.dirname(os.path.abspath(__file__))
        self._caminho = os.path.join(pasta, caminho)

    @property
    def caminho(self):
        return self._caminho

    def exportar(self, projecao):
        """Grava o CSV (separador ';' e decimal ',' para abrir direto no Excel BR)."""
        with open(self._caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(["mes", "aluguel", "parcela_taxa", "total_mes"])
            for mes, aluguel, parcela, total in projecao:
                escritor.writerow([mes] + [f"{v:.2f}".replace(".", ",") for v in (aluguel, parcela, total)])


# ---------------------------------------------------------------------------
# Interação com o usuário
# ---------------------------------------------------------------------------
class InterfaceUsuario:
    @staticmethod
    def ler_opcao(pergunta, minimo, maximo):
        """Repete a pergunta até receber um inteiro entre minimo e maximo."""
        while True:
            texto = input(pergunta).strip()
            if texto.isdigit() and minimo <= int(texto) <= maximo:
                return int(texto)
            print(f"  Entrada inválida. Digite um número de {minimo} a {maximo}.")

    @staticmethod
    def ler_numero_minimo(pergunta, minimo):
        """Repete a pergunta até receber um inteiro maior ou igual a minimo."""
        while True:
            texto = input(pergunta).strip()
            if texto.isdigit() and int(texto) >= minimo:
                return int(texto)
            print(f"  Entrada inválida. Digite um número inteiro maior ou igual a {minimo}.")

    @staticmethod
    def ler_sim_nao(pergunta):
        """Repete a pergunta até receber S ou N. Retorna True para sim."""
        while True:
            texto = input(pergunta + " (S/N): ").strip().lower()
            if texto in ("s", "sim"):
                return True
            if texto in ("n", "nao", "não"):
                return False
            print("  Entrada inválida. Responda com S ou N.")

    def montar_imovel(self):
        print("Tipo de imóvel:\n  1 - Apartamento\n  2 - Casa\n  3 - Estúdio")
        tipo = self.ler_opcao("Escolha (1-3): ", 1, 3)
        if tipo == 1:
            quartos = self.ler_opcao("Número de quartos (1 ou 2): ", 1, 2)
            garagem = self.ler_sim_nao("Deseja vaga de garagem?")
            criancas = self.ler_sim_nao("Possui crianças?")
            return Apartamento(quartos, garagem, criancas)
        if tipo == 2:
            quartos = self.ler_opcao("Número de quartos (1 ou 2): ", 1, 2)
            garagem = self.ler_sim_nao("Deseja vaga de garagem?")
            return Casa(quartos, garagem)
        vagas = self.ler_numero_minimo("Total de vagas de estacionamento (mínimo 2): ", 2)
        return Estudio(vagas)

    def ler_parcelas(self):
        return self.ler_opcao("Parcelas da taxa contratual (1 a 5): ", 1, Orcamento.MAX_PARCELAS)


def main():
    print("RentSmart - R.M Imóveis\n")
    interface = InterfaceUsuario()
    imovel = interface.montar_imovel()
    parcelas = interface.ler_parcelas()

    orcamento = Orcamento(imovel, parcelas)
    print(orcamento.gerar_resumo())

    exportador = ExportadorCSV()
    exportador.exportar(orcamento.projetar_12_meses())
    print(f"\nProjeção de 12 meses gravada em: {exportador.caminho}")


if __name__ == "__main__":
    main()
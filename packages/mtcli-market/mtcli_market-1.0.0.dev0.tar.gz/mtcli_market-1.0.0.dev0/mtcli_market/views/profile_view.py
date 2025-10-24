from typing import Any

import click


def exibir_profile(
    resultado: dict[str, Any], symbol: str, compact: bool = False
) -> None:
    """Exibe o resultado do profile em formato textual acessível.

    - compact=False: descrição textual detalhada, pensada para leitores de tela.
    - compact=True: saída mais curta, adequada para parsing/integração.
    """
    if not resultado:
        click.echo(f"Nenhum dado para exibir para o ativo {symbol}.")
        return

    profile = resultado.get("profile", {})
    tpo = resultado.get("tpo", {})

    poc = resultado.get("poc")
    vah = resultado.get("vah")
    val = resultado.get("val")
    hvn = resultado.get("hvn", [])
    lvn = resultado.get("lvn", [])
    ib = resultado.get("ib")
    total_vol = resultado.get("total_volume")
    total_tpo = resultado.get("total_tpo")

    # Cabeçalho
    click.echo(
        f"Market Profile para {symbol}. Base: {resultado.get('by')}. Bloco: {resultado.get('block')}."
    )

    if compact:
        # saída programática simples
        click.echo("DISTRIBUICAO:")
        for price, vol in profile.items():
            click.echo(f"{price}:{vol}")
        click.echo(f"POC:{poc}")
        click.echo(f"VA:{val}:{vah}")
        if ib:
            click.echo(f"IB:{ib['low']}:{ib['high']}")
        return

    # Verbose (descritivo)
    click.echo(
        "Distribuicao de perfil (preco : valor) — do preço mais alto para o mais baixo:"
    )
    for price, vol in profile.items():
        click.echo(f"{price} : {vol}")

    if total_vol is not None:
        click.echo(f"Total acumulado (soma das unidades do profile): {total_vol}.")
    if total_tpo is not None and resultado.get("by") == "time":
        click.echo(f"Total de TPOs (visitas de preço): {total_tpo}.")

    if poc is not None:
        click.echo(f"Point of Control (POC): o preço com maior atividade é {poc}.")
    if val is not None and vah is not None:
        click.echo(
            f"Value Area: faixa entre {val} (baixo) e {vah} (alto), cobrindo aproximadamente {resultado.get('va_percent') * 100}% do total."
        )

    if hvn:
        hvn_list = ", ".join(str(p) for p in hvn)
        click.echo(f"Nodos de alto volume (HVN): {hvn_list}.")
    if lvn:
        lvn_list = ", ".join(str(p) for p in lvn)
        click.echo(f"Nodos de baixo volume (LVN): {lvn_list}.")

    if ib:
        click.echo(f"Initial Balance (IB): de {ib['low']} a {ib['high']}.")

    # Complementos: exibir TPOs se disponíveis
    if tpo:
        click.echo(
            "Contagem de visitas por faixa (TPO) — do preço mais alto para o mais baixo:"
        )
        for price, cnt in tpo.items():
            click.echo(f"{price} : {cnt}")

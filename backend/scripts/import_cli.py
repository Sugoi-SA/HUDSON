import argparse

from app.config import STORAGE_ROOT
from app.db import get_session
from app.services.importer import import_source


def main():
    parser = argparse.ArgumentParser(description="Importa um diretorio de origem para o HUDSON S1 com Metadados e Ronda (v2.0)")
    parser.add_argument("--source", required=True, help="Diretorio de origem a varrer recursivamente")
    parser.add_argument("--wbs", default="INDEFINIDO", help="Codigo do empreendimento/WBS para a Cota HUDSON")
    parser.add_argument("--ronda", default=None, help="Identificador unico da rodada de captura (UUID ou codigo)")
    parser.add_argument("--usuario", default="sistema", help="Usuario responsavel pela captura")
    args = parser.parse_args()

    with get_session() as session:
        summary = import_source(
            session,
            args.source,
            STORAGE_ROOT,
            obra_wbs=args.wbs,
            ronda_id=args.ronda,
            usuario_captura=args.usuario,
        )

    print("=" * 60)
    print("HUDSON IMPORT CLI v2.0 — RELATÓRIO DE RONDA")
    print("=" * 60)
    print(f"Ronda ID:                   {summary.ronda_id}")
    print(f"Total de arquivos varridos: {summary.total}")
    print(f"Novos itens custodiados:    {summary.novos}")
    print(f"  indexados (com texto):    {summary.indexados}")
    print(f"  desbloqueados:            {summary.desbloqueados}")
    print(f"  sem texto extraido:       {summary.sem_texto}")
    print(f"  sem estante mapeada:      {summary.sem_estante}")
    print(f"Duplicados (ja custodiados):{summary.duplicados}")
    if summary.erros:
        print(f"Erros ({len(summary.erros)}):")
        for erro in summary.erros:
            print(f"  - {erro}")
    print("=" * 60)


if __name__ == "__main__":
    main()

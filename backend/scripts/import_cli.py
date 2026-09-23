import argparse

from app.config import STORAGE_ROOT
from app.db import get_session
from app.importer import import_source


def main():
    parser = argparse.ArgumentParser(description="Importa um diretorio de origem para o HUDSON S1 (v0)")
    parser.add_argument("--source", required=True, help="Diretorio de origem a varrer recursivamente")
    parser.add_argument("--wbs", default="INDEFINIDO", help="Codigo do empreendimento/WBS para a Cota HUDSON")
    args = parser.parse_args()

    with get_session() as session:
        summary = import_source(session, args.source, STORAGE_ROOT, args.wbs)

    print(f"Total de arquivos varridos: {summary.total}")
    print(f"Novos itens custodiados:    {summary.novos}")
    print(f"  indexados (com texto):    {summary.indexados}")
    print(f"  sem texto extraido:       {summary.sem_texto}")
    print(f"  sem estante mapeada:      {summary.sem_estante}")
    print(f"Duplicados (ja custodiados): {summary.duplicados}")
    if summary.erros:
        print(f"Erros ({len(summary.erros)}):")
        for erro in summary.erros:
            print(f"  - {erro}")


if __name__ == "__main__":
    main()

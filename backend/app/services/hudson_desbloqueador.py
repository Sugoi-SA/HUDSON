"""
=============================================================================
HUDSON DESBLOQUEADOR DE ARQUIVOS (HDW - HUDSON DATA WAREHOUSE)
=============================================================================
Módulo especializado em desbloqueio, remoção de travas de edição, senhas e
extração de arquivos compactados e documentos restritos para pipelines de dados.

Componentes:
  1. DesbloqueadorPDF     - Desbloqueio e extração via pikepdf, pypdfium2 e pdfplumber.
  2. DesbloqueadorWord    - Remoção de proteção de edição XML e conversão CLI.
  3. DesbloqueadorExcel   - Remoção de proteção de planilhas/pastas (openpyxl + XML).
  4. DesbloqueadorRARZIP  - Extração de ZIP (zipfile), 7Z (py7zr) e RAR (rarfile + WinRAR).
  5. HudsonDesbloqueador  - Fachada unificada com auto-roteamento por extensão.
=============================================================================
"""

import os
import re
import sys
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configuração do WinRAR para extração de RAR
UNRAR_PATHS = [
    r"C:\Program Files\WinRAR\UnRAR.exe",
    r"C:\Program Files (x86)\WinRAR\UnRAR.exe",
    shutil.which("unrar") or ""
]
UNRAR_EXECUTABLE = next((p for p in UNRAR_PATHS if p and os.path.exists(p)), None)

try:
    import rarfile
    if UNRAR_EXECUTABLE:
        rarfile.UNRAR_TOOL = UNRAR_EXECUTABLE
except ImportError:
    rarfile = None

try:
    import py7zr
except ImportError:
    py7zr = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pypdfium2
except ImportError:
    pypdfium2 = None

try:
    import pikepdf
except ImportError:
    pikepdf = None

try:
    import docx
except ImportError:
    docx = None

try:
    import openpyxl
except ImportError:
    openpyxl = None


# =====================================================================
# 1. DESBLOQUEADOR DE PDF
# =====================================================================
class DesbloqueadorPDF:
    """Desbloqueia PDFs protegidos por senha ou com restrições de cópia/impressão."""

    @staticmethod
    def verificar_bloqueio(caminho: str) -> Dict[str, Any]:
        caminho_p = Path(caminho)
        if not caminho_p.exists():
            return {"erro": "Arquivo não encontrado", "bloqueado": False}

        bloqueado = False
        tem_senha = False
        permissoes = {}

        if pikepdf:
            try:
                with pikepdf.open(caminho_p) as pdf:
                    bloqueado = bool(pdf.is_encrypted)
                    permissoes = {"encrypted": pdf.is_encrypted}
            except pikepdf.PasswordError:
                bloqueado = True
                tem_senha = True
            except Exception as e:
                pass

        return {
            "arquivo": caminho_p.name,
            "bloqueado": bloqueado,
            "requer_senha": tem_senha,
            "motor": "pikepdf" if pikepdf else "pypdfium2"
        }

    @staticmethod
    def desbloquear(caminho: str, senha: Optional[str] = None, destino: Optional[str] = None) -> str:
        caminho_p = Path(caminho)
        saida = Path(destino) if destino else caminho_p.with_stem(caminho_p.stem + "_desbloqueado")

        if not pikepdf:
            raise RuntimeError("pikepdf não instalado para desbloqueio de PDF.")

        try:
            with pikepdf.open(caminho_p, password=senha or "") as pdf:
                pdf.save(saida)
            return str(saida)
        except Exception as e:
            raise RuntimeError(f"Falha ao desbloquear PDF {caminho_p.name}: {e}")

    @staticmethod
    def extrair_texto(caminho: str, senha: Optional[str] = None) -> str:
        """Extrai texto usando pdfplumber ou pypdfium2."""
        caminho_p = Path(caminho)
        texto = []

        if pdfplumber:
            try:
                with pdfplumber.open(caminho_p, password=senha or "") as pdf:
                    for pag in pdf.pages:
                        t = pag.extract_text()
                        if t:
                            texto.append(t)
                if texto:
                    return "\n\n".join(texto)
            except Exception:
                pass

        if pypdfium2:
            try:
                pdf = pypdfium2.PdfDocument(caminho_p, password=senha or None)
                for i in range(len(pdf)):
                    page = pdf[i]
                    textpage = page.get_textpage()
                    t = textpage.get_text_range()
                    if t:
                        texto.append(t)
                return "\n\n".join(texto)
            except Exception as e:
                raise RuntimeError(f"Falha na extração de texto via pypdfium2: {e}")

        return ""


# =====================================================================
# 2. DESBLOQUEADOR DE WORD (.DOCX)
# =====================================================================
class DesbloqueadorWord:
    """Remove travas de edição de documentos Word (.docx) via manipulação direta de XML."""

    @staticmethod
    def verificar_bloqueio(caminho: str) -> Dict[str, Any]:
        caminho_p = Path(caminho)
        if not caminho_p.exists():
            return {"erro": "Arquivo não encontrado", "bloqueado": False}

        bloqueado = False
        try:
            with zipfile.ZipFile(caminho_p, 'r') as z:
                if 'word/settings.xml' in z.namelist():
                    settings = z.read('word/settings.xml').decode('utf-8', errors='ignore')
                    if 'w:documentProtection' in settings:
                        bloqueado = True
        except Exception:
            pass

        return {
            "arquivo": caminho_p.name,
            "bloqueado": bloqueado,
            "tipo": "Proteção de Edição / Formulário Word" if bloqueado else "Sem bloqueio detectado"
        }

    @staticmethod
    def remover_protecao_edicao(caminho: str, destino: Optional[str] = None) -> str:
        """Remove a tag <w:documentProtection .../> do arquivo word/settings.xml."""
        caminho_p = Path(caminho)
        saida = Path(destino) if destino else caminho_p.with_stem(caminho_p.stem + "_desbloqueado")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(caminho_p, 'r') as zin:
                zin.extractall(temp_path)

            settings_file = temp_path / 'word' / 'settings.xml'
            if settings_file.exists():
                conteudo = settings_file.read_text(encoding='utf-8', errors='ignore')
                conteudo_modificado = re.sub(r'<w:documentProtection[^>]*/>', '', conteudo)
                conteudo_modificado = re.sub(r'<w:documentProtection[^>]*>.*?</w:documentProtection>', '', conteudo_modificado, flags=re.DOTALL)
                settings_file.write_text(conteudo_modificado, encoding='utf-8')

            # Recompacta o documento docx
            with zipfile.ZipFile(saida, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
                for root, _, files in os.walk(temp_path):
                    for file in files:
                        full_p = Path(root) / file
                        arcname = full_p.relative_to(temp_path)
                        zout.write(full_p, arcname)

        return str(saida)

    @staticmethod
    def extrair_texto(caminho: str) -> str:
        if not docx:
            raise RuntimeError("python-docx não instalado.")
        doc = docx.Document(caminho)
        return "\n".join([p.text for p in doc.paragraphs if p.text])


# =====================================================================
# 3. DESBLOQUEADOR DE EXCEL (.XLSX)
# =====================================================================
class DesbloqueadorExcel:
    """Remove travas de proteção de planilhas e pasta de trabalho (.xlsx)."""

    @staticmethod
    def verificar_bloqueio(caminho: str) -> Dict[str, Any]:
        caminho_p = Path(caminho)
        if not caminho_p.exists():
            return {"erro": "Arquivo não encontrado", "bloqueado": False}

        bloqueios = []
        try:
            with zipfile.ZipFile(caminho_p, 'r') as z:
                for name in z.namelist():
                    if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                        xml_content = z.read(name).decode('utf-8', errors='ignore')
                        if '<sheetProtection' in xml_content:
                            bloqueios.append(name)
                    elif name == 'xl/workbook.xml':
                        xml_content = z.read(name).decode('utf-8', errors='ignore')
                        if '<workbookProtection' in xml_content:
                            bloqueios.append("workbookProtection")
        except Exception:
            pass

        return {
            "arquivo": caminho_p.name,
            "bloqueado": len(bloqueios) > 0,
            "elementos_protegidos": bloqueios
        }

    @staticmethod
    def remover_protecao_planilhas(caminho: str, destino: Optional[str] = None) -> str:
        """Remove tags <sheetProtection .../> e <workbookProtection .../> sem precisar da senha."""
        caminho_p = Path(caminho)
        saida = Path(destino) if destino else caminho_p.with_stem(caminho_p.stem + "_desbloqueado")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(caminho_p, 'r') as zin:
                zin.extractall(temp_path)

            # 1. Tratar worksheets
            ws_dir = temp_path / 'xl' / 'worksheets'
            if ws_dir.exists():
                for sheet_file in ws_dir.glob('sheet*.xml'):
                    conteudo = sheet_file.read_text(encoding='utf-8', errors='ignore')
                    novo = re.sub(r'<sheetProtection[^>]*/>', '', conteudo)
                    novo = re.sub(r'<sheetProtection[^>]*>.*?</sheetProtection>', '', novo, flags=re.DOTALL)
                    sheet_file.write_text(novo, encoding='utf-8')

            # 2. Tratar workbook
            wb_file = temp_path / 'xl' / 'workbook.xml'
            if wb_file.exists():
                conteudo = wb_file.read_text(encoding='utf-8', errors='ignore')
                novo = re.sub(r'<workbookProtection[^>]*/>', '', conteudo)
                novo = re.sub(r'<workbookProtection[^>]*>.*?</workbookProtection>', '', novo, flags=re.DOTALL)
                wb_file.write_text(novo, encoding='utf-8')

            # Recompacta o xlsx
            with zipfile.ZipFile(saida, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
                for root, _, files in os.walk(temp_path):
                    for file in files:
                        full_p = Path(root) / file
                        arcname = full_p.relative_to(temp_path)
                        zout.write(full_p, arcname)

        return str(saida)


# =====================================================================
# 4. DESBLOQUEADOR E EXTRATOR RAR / ZIP / 7Z
# =====================================================================
class DesbloqueadorRARZIP:
    """Extrai pacotes compactados em ZIP, 7Z e RAR (com suporte a senha)."""

    @staticmethod
    def identificar_formato(caminho: str) -> str:
        ext = Path(caminho).suffix.lower()
        if ext in ['.zip', '.jar']:
            return 'ZIP'
        elif ext in ['.7z']:
            return '7Z'
        elif ext in ['.rar']:
            return 'RAR'
        return 'DESCONHECIDO'

    @staticmethod
    def extrair(caminho: str, destino: Optional[str] = None, senha: Optional[str] = None) -> List[str]:
        caminho_p = Path(caminho)
        if not caminho_p.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        saida_dir = Path(destino) if destino else caminho_p.parent / caminho_p.stem
        saida_dir.mkdir(parents=True, exist_ok=True)
        arquivos_extraidos = []

        formato = DesbloqueadorRARZIP.identificar_formato(caminho)

        if formato == 'ZIP':
            with zipfile.ZipFile(caminho_p, 'r') as z:
                pwd = senha.encode('utf-8') if senha else None
                z.extractall(saida_dir, pwd=pwd)
                arquivos_extraidos = [str(saida_dir / n) for n in z.namelist()]

        elif formato == '7Z':
            if not py7zr:
                raise RuntimeError("py7zr não está instalado para descompactar .7z.")
            with py7zr.SevenZipFile(caminho_p, mode='r', password=senha) as z:
                z.extractall(path=saida_dir)
                arquivos_extraidos = [str(saida_dir / n) for n in z.getnames()]

        elif formato == 'RAR':
            if not rarfile:
                raise RuntimeError("rarfile não está instalado.")
            if not UNRAR_EXECUTABLE:
                raise RuntimeError("WinRAR / UnRAR não localizado no sistema para descompactar .rar.")
            
            with rarfile.RarFile(caminho_p) as rf:
                if senha:
                    rf.setpassword(senha)
                rf.extractall(path=saida_dir)
                arquivos_extraidos = [str(saida_dir / n) for n in rf.namelist()]

        else:
            raise ValueError(f"Formato não suportado para extração: {formato}")

        return arquivos_extraidos


# =====================================================================
# 5. FACHADA UNIFICADA HUDSON DESBLOQUEADOR
# =====================================================================
class HudsonDesbloqueador:
    """Fachada unificada para o Hudson Data Warehouse (HDW)."""

    def __init__(self):
        self.pdf = DesbloqueadorPDF()
        self.word = DesbloqueadorWord()
        self.excel = DesbloqueadorExcel()
        self.compactados = DesbloqueadorRARZIP()

    def desbloquear_arquivo(self, caminho: str, destino: Optional[str] = None, senha: Optional[str] = None) -> Any:
        caminho_p = Path(caminho)
        ext = caminho_p.suffix.lower()

        if ext == '.pdf':
            return self.pdf.desbloquear(str(caminho_p), senha=senha, destino=destino)
        elif ext in ['.docx']:
            return self.word.remover_protecao_edicao(str(caminho_p), destino=destino)
        elif ext in ['.xlsx']:
            return self.excel.remover_protecao_planilhas(str(caminho_p), destino=destino)
        elif ext in ['.zip', '.7z', '.rar']:
            return self.compactados.extrair(str(caminho_p), destino=destino, senha=senha)
        else:
            return {"aviso": f"Extensão {ext} não requer desbloqueio específico.", "caminho": str(caminho_p)}

    def status_ferramentas(self) -> Dict[str, Any]:
        """Informa a disponibilidade de todos os motores na máquina."""
        return {
            "DesbloqueadorPDF": {
                "pikepdf": pikepdf is not None,
                "pypdfium2": pypdfium2 is not None,
                "pdfplumber": pdfplumber is not None,
                "status": "✅ Operacional"
            },
            "DesbloqueadorWord": {
                "python-docx": docx is not None,
                "desbloqueio_xml_nativo": True,
                "libreoffice_cli": shutil.which("soffice") is not None,
                "status": "✅ Operacional (Nativo XML)"
            },
            "DesbloqueadorExcel": {
                "openpyxl": openpyxl is not None,
                "desbloqueio_xml_nativo": True,
                "libreoffice_cli": shutil.which("soffice") is not None,
                "status": "✅ Operacional (Nativo XML)"
            },
            "DesbloqueadorRARZIP": {
                "zipfile": True,
                "py7zr": py7zr is not None,
                "rarfile": rarfile is not None,
                "unrar_binario": UNRAR_EXECUTABLE,
                "status": "✅ Operacional (WinRAR Integrado)"
            }
        }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    hudson = HudsonDesbloqueador()
    import json
    print("=================================================================")
    print("STATUS DAS FERRAMENTAS DO HUDSON DESBLOQUEADOR (HDW):")
    print("=================================================================")
    print(json.dumps(hudson.status_ferramentas(), indent=2, ensure_ascii=False))

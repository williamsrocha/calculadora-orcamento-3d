# calculadora3d_v18.py — DT 3D STUDIO
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                HRFlowable, Table, TableStyle, Image as RLImage)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
import zipfile
import re
import os
import sys
from datetime import date


# ─────────────────────────── helpers ────────────────────────────────────────

def converter_horas(valor):
    valor = valor.strip().lower()
    if ":" in valor:
        h, m = valor.split(":")
        return int(h) + int(m) / 60
    if "h" in valor:
        match = re.search(r"(\d+)\s*h\s*(\d+)?", valor)
        if match:
            horas   = int(match.group(1))
            minutos = int(match.group(2)) if match.group(2) else 0
            return horas + minutos / 60
    if "min" in valor:
        return float(valor.replace("min", "").strip()) / 60
    if valor.endswith("m"):
        return float(valor[:-1].strip()) / 60
    return float(valor.replace(",", "."))


def formatar_tempo(horas_decimais):
    horas_total = int(horas_decimais)
    minutos     = round((horas_decimais - horas_total) * 60)
    if minutos == 60:
        horas_total += 1
        minutos      = 0
    if horas_total < 24:
        return f"{horas_total}h {minutos:02d}min"
    dias  = horas_total // 24
    horas = horas_total % 24
    label = "dia" if dias == 1 else "dias"
    return f"{dias} {label} {horas}h {minutos:02d}min"


def formatar_peso(gramas):
    """Abaixo de 1000 g exibe em g; acima exibe apenas em kg. Padrão brasileiro."""
    if gramas < 1000:
        return f"{gramas:.2f} g".replace(".", ",")
    return f"{gramas / 1000:.3f} kg".replace(".", ",")


def arredondar_preco(valor):
    """Arredonda para múltiplo de R$5 com mínimo de R$5."""
    return max(round(valor / 5) * 5, 5)


def moeda(valor):
    """Formata valor em R$ no padrão brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def limpar_nome(nome_raw):
    """Remove todas as extensões 3mf/gcode/stl encadeadas (ex: .gcode.3mf) e troca underscores por espaços."""
    nome = re.sub(r"(\.(gcode|3mf|stl))+$", "", nome_raw, flags=re.IGNORECASE)
    return nome.replace("_", " ").strip()


# ─────────────────────────── main ───────────────────────────────────────────

def main():
    ultimo_relatorio = {}

    janela = tk.Tk()
    janela.title("DT 3D STUDIO — Calculadora v19")
    janela.resizable(True, True)
    janela.minsize(560, 480)
    # Centraliza na tela com tamanho compacto
    janela.update_idletasks()
    w, h   = 600, 580
    sw, sh = janela.winfo_screenwidth(), janela.winfo_screenheight()
    x, y   = (sw - w) // 2, (sh - h) // 2
    janela.geometry(f"{w}x{h}+{x}+{y}")

    BG     = "#f4f4f8"
    ACCENT = "#1a1a2e"
    GREEN  = "#2d6a4f"
    GOLD   = "#b5770d"

    janela.configure(bg=BG)

    # Caminho da pasta assets — procura em vários locais até encontrar
    _candidatos_assets = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)),   "assets"),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "assets"),
        os.path.join(os.getcwd(), "assets"),
    ]
    ASSETS = next((p for p in _candidatos_assets if os.path.isdir(p)), _candidatos_assets[0])
    print(f"[ASSETS] {ASSETS}  —  existe: {os.path.isdir(ASSETS)}")

    # ── Ícone da barra de título ─────────────────────────────────────────────
    _ico = os.path.join(ASSETS, "icone_dt3dstudio.ico")
    if os.path.isfile(_ico):
        # janela.after garante que o ícone carrega após a janela estar pronta (necessário no Windows)
        janela.after(100, lambda: janela.iconbitmap(_ico))
    else:
        print(f"[ICO] Não encontrado: {_ico}")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background=BG, font=("Segoe UI", 9))
    style.configure("TEntry", font=("Segoe UI", 9), padding=2)

    # ── Cabeçalho: logo + nome sempre visíveis ───────────────────────────────
    _png = os.path.join(ASSETS, "icone_dt3dstudio.png")
    if os.path.isfile(_png):
        try:
            from PIL import Image, ImageTk
            img_raw  = Image.open(_png).resize((52, 52), Image.LANCZOS)
            logo_img = ImageTk.PhotoImage(img_raw)
            lbl_logo = tk.Label(janela, image=logo_img, bg=BG)
            lbl_logo.image = logo_img   # evita garbage collection
            lbl_logo.pack(pady=(6, 1))
        except Exception as e:
            print(f"[PNG] {e}")
    else:
        print(f"[PNG] Não encontrado: {_png}")

    # Nome da empresa — sempre exibido, com ou sem logo
    ttk.Label(janela, text="DT 3D STUDIO",
              font=("Segoe UI", 12, "bold"),
              foreground=ACCENT, background=BG).pack()
    ttk.Label(janela, text="Calculadora de Orçamento 3D",
              font=("Segoe UI", 8), foreground="#888888",
              background=BG).pack(pady=(0, 1))

    ttk.Separator(janela, orient="horizontal").pack(fill="x", padx=14, pady=3)

    # ── Frame de campos ──────────────────────────────────────────────────────
    frame_campos = tk.Frame(janela, bg=BG)
    frame_campos.pack(padx=14, fill="x")
    frame_campos.columnconfigure(0, weight=1)
    frame_campos.columnconfigure(1, weight=1)
    frame_campos.columnconfigure(2, weight=1)

    def campo(parent, texto, row, col, default=""):
        ttk.Label(parent, text=texto, font=("Segoe UI", 8)).grid(
            row=row * 2, column=col, sticky="w",
            padx=(0 if col == 0 else 10, 0))
        e = ttk.Entry(parent, font=("Segoe UI", 9), justify="center")
        e.grid(row=row * 2 + 1, column=col, sticky="ew", pady=(0, 6),
               padx=(0 if col == 0 else 10, 0))
        if default:
            e.insert(0, default)
        return e

    # linha 0 — nome da peça (span 3)
    ttk.Label(frame_campos, text="Nome da peça:", font=("Segoe UI", 8)).grid(
        row=0, column=0, sticky="w")
    entry_nome_peca = ttk.Entry(frame_campos, font=("Segoe UI", 9), justify="center")
    entry_nome_peca.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 6))

    # linha 1 — peso | bobina | quantidade
    entry_peso       = campo(frame_campos, "Peso usado (g):",       1, 0)
    entry_bobina     = campo(frame_campos, "Preço da bobina (R$):", 1, 1)
    entry_quantidade = campo(frame_campos, "Quantidade:",           1, 2, "1")

    # linha 2 — tempo | tarifa | lucro
    entry_horas   = campo(frame_campos, "Tempo de impressão:",      2, 0)
    entry_energia = campo(frame_campos, "Tarifa energia (R$/kWh):", 2, 1, "0,88")
    entry_lucro   = campo(frame_campos, "Lucro desejado (%):",      2, 2, "50")

    # linha 3 — observações (multilinha, span 3)
    ttk.Label(frame_campos, text="Observações:", font=("Segoe UI", 8)).grid(
        row=6, column=0, sticky="w")
    entry_obs = tk.Text(frame_campos, height=2, width=60,
                        font=("Segoe UI", 9), relief="solid", bd=1)
    entry_obs.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(0, 6))

    ttk.Separator(janela, orient="horizontal").pack(fill="x", padx=14, pady=3)

    # ── Botões ───────────────────────────────────────────────────────────────
    frame_btns = tk.Frame(janela, bg=BG)
    frame_btns.pack(pady=4)

    def mk_btn(parent, texto, cmd, cor=ACCENT, col=0):
        b = tk.Button(parent, text=texto, command=cmd,
                      bg=cor, fg="white",
                      font=("Segoe UI", 8, "bold"),
                      relief="flat", padx=8, pady=4, width=13)
        b.grid(row=0, column=col, padx=4)
        return b

    # ── 4 Cards de resultado ─────────────────────────────────────────────────
    frame_cards = tk.Frame(janela, bg=BG)
    frame_cards.pack(pady=6, padx=14, fill="x")
    for i in range(4):
        frame_cards.columnconfigure(i, weight=1)

    def make_card(parent, titulo, cor, col):
        lbl = tk.Label(parent, text=f"{titulo}\n—",
                       bg=cor, fg="white",
                       font=("Segoe UI", 9, "bold"),
                       height=2, relief="flat")
        lbl.grid(row=0, column=col, padx=3, sticky="ew")
        return lbl

    lbl_custo     = make_card(frame_cards, "CUSTO TOTAL",     "#555577", 0)
    lbl_comercial = make_card(frame_cards, "PREÇO COMERCIAL", ACCENT,    1)
    lbl_atacado   = make_card(frame_cards, "PREÇO ATACADO",   GREEN,     2)
    lbl_lucro     = make_card(frame_cards, "LUCRO LÍQUIDO",   GOLD,      3)

    ttk.Separator(janela, orient="horizontal").pack(fill="x", padx=14, pady=3)

    # ── Área de resultado detalhado ──────────────────────────────────────────
    resultado = scrolledtext.ScrolledText(
        janela, height=7,
        font=("Courier New", 9),
        state="disabled",
        bg="#eeeeee", relief="flat",
        padx=8, pady=4,
    )
    resultado.pack(fill="x", expand=False, padx=14, pady=(0, 4))

    # ─────────────────────────── funções ────────────────────────────────────

    def limpar():
        nonlocal ultimo_relatorio
        for e in (entry_nome_peca, entry_peso, entry_bobina, entry_horas):
            e.delete(0, tk.END)
        entry_quantidade.delete(0, tk.END)
        entry_quantidade.insert(0, "1")
        entry_obs.delete("1.0", tk.END)
        resultado.config(state="normal")
        resultado.delete("1.0", tk.END)
        resultado.config(state="disabled")
        lbl_custo.config(text="CUSTO TOTAL\n—")
        lbl_comercial.config(text="PREÇO COMERCIAL\n—")
        lbl_atacado.config(text="PREÇO ATACADO\n—")
        lbl_lucro.config(text="LUCRO LÍQUIDO\n—")
        ultimo_relatorio = {}

    def calcular():
        nonlocal ultimo_relatorio

        # Valida cada campo individualmente com mensagem clara
        campos = [
            (entry_peso.get().strip(),     "Peso usado (g)"),
            (entry_bobina.get().strip(),   "Preço da bobina (R$)"),
            (entry_horas.get().strip(),    "Tempo de impressão"),
            (entry_energia.get().strip(),  "Tarifa de energia (R$/kWh)"),
            (entry_lucro.get().strip(),    "Lucro desejado (%)"),
            (entry_quantidade.get().strip(),"Quantidade"),
        ]
        for valor, nome in campos:
            if not valor:
                messagebox.showwarning('Campo obrigatório',
                    f'O campo "{nome}" está vazio.\nPreencha antes de calcular.')
                return

        try:
            peso_g           = float(entry_peso.get().replace(",", "."))
            preco_bobina     = float(entry_bobina.get().replace(",", "."))
            horas_unit       = converter_horas(entry_horas.get())
            tarifa           = float(entry_energia.get().replace(",", "."))
            lucro_percentual = float(entry_lucro.get().replace(",", "."))
            quantidade       = int(entry_quantidade.get().strip())
        except Exception:
            messagebox.showerror("Valor inválido",
                "Um dos campos contém um valor inválido.\n"
                "Use números com vírgula ou ponto decimal.\n"
                "Ex: 78,66  ou  94.90")
            return

        peso_total  = peso_g    * quantidade
        horas_total = horas_unit * quantidade

        custo_material = peso_total  * (preco_bobina / 1000)
        custo_energia  = horas_total * 0.1 * tarifa
        custo_desgaste = custo_material * 0.10
        custo_maquina  = horas_total * 2.0
        subtotal       = custo_material + custo_energia + custo_desgaste + custo_maquina

        preco_final     = subtotal * (1 + lucro_percentual / 100)
        lucro_bruto     = preco_final - subtotal
        preco_comercial = arredondar_preco(preco_final)
        preco_atacado   = max(round(preco_comercial * 0.90, 2), 5.0)
        lucro_liquido   = preco_comercial - subtotal

        obs_texto = entry_obs.get("1.0", tk.END).strip() or "—"

        ultimo_relatorio = {
            "nome_peca":        limpar_nome(entry_nome_peca.get().strip()) or "—",
            "obs":              obs_texto,
            "peso_g":           peso_g,
            "peso_total":       peso_total,
            "horas_unit":       horas_unit,
            "horas_total":      horas_total,
            "quantidade":       quantidade,
            "custo_material":   custo_material,
            "custo_energia":    custo_energia,
            "custo_desgaste":   custo_desgaste,
            "custo_maquina":    custo_maquina,
            "subtotal":         subtotal,
            "lucro_percentual": lucro_percentual,
            "lucro_bruto":      lucro_bruto,
            "lucro_liquido":    lucro_liquido,
            "preco_final":      preco_final,
            "preco_comercial":  preco_comercial,
            "preco_atacado":    preco_atacado,
        }

        texto = (
            f"Peça:        {ultimo_relatorio['nome_peca']}\n"
            f"Qtd:         {quantidade}x\n"
            f"Peso unit.:  {formatar_peso(peso_g)}\n"
            f"Peso total:  {formatar_peso(peso_total)}\n"
            f"Tempo unit.: {formatar_tempo(horas_unit)}\n"
            f"Tempo total: {formatar_tempo(horas_total)}\n"
            f"{'─'*46}\n"
            f"Custo material:    {moeda(custo_material)}\n"
            f"Custo energia:     {moeda(custo_energia)}\n"
            f"Custo desgaste:    {moeda(custo_desgaste)}\n"
            f"Custo máquina:     {moeda(custo_maquina)}\n"
            f"{'─'*46}\n"
            f"Custo total:       {moeda(subtotal)}\n"
            f"Lucro aplicado:    {lucro_percentual:.0f}%\n"
            f"Valor adicionado:  {moeda(lucro_bruto)}\n"
            f"Preço calculado:   {moeda(preco_final)}\n"
            f"{'─'*46}\n"
            f"PREÇO COMERCIAL:   {moeda(preco_comercial)}\n"
            f"PREÇO ATACADO:     {moeda(preco_atacado)}\n"
            f"LUCRO LÍQUIDO:     {moeda(lucro_liquido)}"
        )

        resultado.config(state="normal")
        resultado.delete("1.0", tk.END)
        resultado.tag_configure("bold", font=("Courier New", 9, "bold"))
        # Divide o texto para aplicar negrito apenas na linha de custo material
        idx = texto.find("Custo material:")
        fim_linha = texto.find("\n", idx) + 1
        resultado.insert(tk.END, texto[:idx])
        resultado.insert(tk.END, texto[idx:fim_linha], "bold")
        resultado.insert(tk.END, texto[fim_linha:])
        resultado.config(state="disabled")

        lbl_custo.config(    text=f"CUSTO TOTAL\n{moeda(subtotal)}")
        lbl_comercial.config(text=f"PREÇO COMERCIAL\n{moeda(preco_comercial)}")
        lbl_atacado.config(  text=f"PREÇO ATACADO\n{moeda(preco_atacado)}")
        lbl_lucro.config(    text=f"LUCRO LÍQUIDO\n{moeda(lucro_liquido)}")

    def importar_bambu():
        try:
            arquivos = filedialog.askopenfilenames(
                title="Selecione um ou mais arquivos 3MF",
                filetypes=[("Arquivos 3MF", "*.3mf")])
            if not arquivos:
                return

            peso_total_g  = 0.0
            horas_total   = 0.0
            nomes         = []
            erros         = []
            importados    = 0

            for arquivo in arquivos:
                nome_sem_ext = limpar_nome(arquivo.split("/")[-1].split("\\")[-1])
                try:
                    with zipfile.ZipFile(arquivo, "r") as zip_ref:
                        for nome in zip_ref.namelist():
                            if nome.endswith("slice_info.config"):
                                conteudo = zip_ref.read(nome).decode(errors="ignore")
                                peso  = re.search(r'key="weight"\s+value="([0-9.]+)"', conteudo)
                                tempo = re.search(r'key="prediction"\s+value="([0-9.]+)"', conteudo)
                                if peso:
                                    peso_total_g += float(peso.group(1))
                                if tempo:
                                    horas_total  += float(tempo.group(1)) / 3600
                                nomes.append(nome_sem_ext)
                                importados += 1
                                break
                except Exception as e:
                    erros.append(f"{nome_sem_ext}: {e}")

            if importados == 0:
                messagebox.showerror("Erro", "Nenhum arquivo válido foi importado.\n" + "\n".join(erros))
                return

            # Preenche os campos com os dados acumulados
            entry_peso.delete(0, tk.END)
            entry_peso.insert(0, f"{peso_total_g:.2f}")

            entry_horas.delete(0, tk.END)
            entry_horas.insert(0, formatar_tempo(horas_total))

            nome_final = " + ".join(nomes) if len(nomes) > 1 else nomes[0]
            entry_nome_peca.delete(0, tk.END)
            entry_nome_peca.insert(0, nome_final)

            msg = f"{importados} arquivo(s) importado(s) com sucesso!\n"
            msg += f"Peso total somado: {peso_total_g:.2f} g\n"
            msg += f"Tempo total somado: {formatar_tempo(horas_total)}\n"
            if erros:
                msg += f"\n⚠️ {len(erros)} arquivo(s) com erro:\n" + "\n".join(erros)
            msg += "\nPreencha o preço da bobina e clique em Calcular."
            messagebox.showinfo("Importação concluída", msg)

        except Exception as erro:
            messagebox.showerror("Erro", str(erro))

    def exportar_pdf():
        if not ultimo_relatorio:
            messagebox.showwarning("Aviso", "Calcule um orçamento antes de exportar.")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not arquivo:
            return

        d    = ultimo_relatorio
        hoje = date.today().strftime("%d/%m/%Y")

        doc = SimpleDocTemplate(arquivo,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm,   bottomMargin=2.5*cm)

        estilos = getSampleStyleSheet()

        titulo_s   = ParagraphStyle("T",  parent=estilos["Title"],  fontSize=16,
            textColor=colors.HexColor("#1a1a2e"), alignment=TA_CENTER,
            spaceAfter=2, leading=20)
        sub_s      = ParagraphStyle("S",  parent=estilos["Normal"], fontSize=10,
            textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=0)
        plabel_s   = ParagraphStyle("PL", parent=estilos["Normal"], fontSize=11,
            textColor=colors.white, alignment=TA_CENTER, spaceBefore=4)
        pvalor_s   = ParagraphStyle("PV", parent=estilos["Normal"], fontSize=22,
            textColor=colors.white, alignment=TA_CENTER, fontName="Helvetica-Bold")
        obs_s      = ParagraphStyle("O",  parent=estilos["Normal"], fontSize=9,
            textColor=colors.HexColor("#555555"), leading=14)
        validade_s = ParagraphStyle("V",  parent=estilos["Normal"], fontSize=8,
            textColor=colors.HexColor("#aaaaaa"), alignment=TA_CENTER, spaceBefore=10)
        rodape_s   = ParagraphStyle("R",  parent=estilos["Normal"], fontSize=8,
            textColor=colors.HexColor("#888888"), alignment=TA_CENTER, spaceBefore=4)

        # ── Cabeçalho centralizado: logo → título → subtítulo ─────────────
        _png_pdf = os.path.join(ASSETS, "icone_dt3dstudio.png")

        if os.path.isfile(_png_pdf):
            logo_rl  = RLImage(_png_pdf, width=2.4*cm, height=2.4*cm)
            t_header = Table(
                [[logo_rl],
                 [Paragraph("DT 3D STUDIO", titulo_s)],
                 [Paragraph("Orçamento Personalizado", sub_s)]],
                colWidths=[17*cm],
            )
            t_header.setStyle(TableStyle([
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ]))
            elementos = [t_header]
        else:
            elementos = [
                Paragraph("DT 3D STUDIO", titulo_s),
                Paragraph("Orçamento Personalizado", sub_s),
            ]

        elementos += [
            Spacer(1, 8),
            HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")),
            Spacer(1, 10),
        ]

        # ── Nome da peça (bloco separado, acima da tabela) ──────────────
        estilo_label = ParagraphStyle("lbl", parent=estilos["Normal"],
            fontSize=10, textColor=colors.HexColor("#888888"))
        estilo_valor = ParagraphStyle("val", parent=estilos["Normal"],
            fontSize=10, textColor=colors.HexColor("#1a1a2e"), leading=15)

        nomes_formatados = d["nome_peca"].replace(" + ", "<br/>")

        bloco_nome = Table(
            [[Paragraph("Nome da peça:", estilo_label),
              Paragraph(nomes_formatados, estilo_valor)]],
            colWidths=[3.5*cm, 13.5*cm],
        )
        bloco_nome.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ]))

        # ── Tabela de dados (Data, Qtd, Peso, Tempo) ─────────────────────
        tabela_info = Table(
            [
                ["Data:",        hoje,
                 "Quantidade:",   f"{d['quantidade']}x"],
                ["Peso unit.:",  formatar_peso(d["peso_g"]),
                 "Peso total:",   formatar_peso(d["peso_total"])],
                ["Tempo unit.:", formatar_tempo(d["horas_unit"]),
                 "Tempo total:", formatar_tempo(d["horas_total"])],
            ],
            colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm],
        )
        tabela_info.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("TEXTCOLOR",     (0, 0), (0, -1),  colors.HexColor("#888888")),
            ("TEXTCOLOR",     (2, 0), (2, -1),  colors.HexColor("#888888")),
            ("TEXTCOLOR",     (1, 0), (1, -1),  colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR",     (3, 0), (3, -1),  colors.HexColor("#1a1a2e")),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        elementos += [
            bloco_nome,
            tabela_info,
            Spacer(1, 10),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")),
            Spacer(1, 14),
        ]

        # ── Cards de preço (apenas o que o cliente precisa ver) ───────────
        def card_pdf(label, valor, cor):
            t = Table(
                [[Paragraph(label, plabel_s), Paragraph(moeda(valor), pvalor_s)]],
                colWidths=[8.5*cm, 8.5*cm], rowHeights=[1.8*cm],
            )
            t.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), cor),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING",  (0, 0), (0, -1),  16),
                ("RIGHTPADDING", (-1, 0), (-1, -1), 16),
            ]))
            return t

        elementos += [
            card_pdf("PREÇO COMERCIAL",          d["preco_comercial"],
                     colors.HexColor("#1a1a2e")),
            Spacer(1, 8),
            card_pdf("PREÇO ATACADO  (10% desc.)", d["preco_atacado"],
                     colors.HexColor("#2d6a4f")),
            Spacer(1, 14),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")),
            Spacer(1, 10),
            Paragraph("<b>Observações:</b>", obs_s),
            Paragraph(d["obs"].replace("\n", "<br/>"), obs_s),
            Spacer(1, 6),
            Paragraph("Validade deste orçamento: 7 dias.", validade_s),
            Spacer(1, 14),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")),
            Spacer(1, 6),
            Paragraph(
                "WhatsApp: (19) 99611-9937  |  "
                "Instagram: @dt3dstudios  |  "
                "E-mail: adm.dt3dstudio@gmail.com",
                rodape_s),
        ]

        doc.build(elementos)
        messagebox.showinfo("PDF", "Orçamento exportado com sucesso!")

    # ── Botões ───────────────────────────────────────────────────────────────
    mk_btn(frame_btns, "📂 Importar Bambu", importar_bambu, ACCENT,    0)
    mk_btn(frame_btns, "⚙️  Calcular",       calcular,       ACCENT,    1)
    mk_btn(frame_btns, "📄 Exportar PDF",   exportar_pdf,   ACCENT,    2)
    mk_btn(frame_btns, "🗑️  Limpar",          limpar,         "#888888", 3)

    janela.mainloop()


if __name__ == "__main__":
    main()

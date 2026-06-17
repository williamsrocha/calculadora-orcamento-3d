# 🖨️ DT 3D STUDIO — Calculadora de Orçamento 3D

Aplicação desktop desenvolvida em Python para calcular orçamentos de impressão 3D de forma rápida e profissional, com exportação de orçamento em PDF.

---

## 📋 Funcionalidades

- **Importação automática de arquivos `.3mf`** (Bambu Slicer) — suporta múltiplos arquivos de uma vez, somando peso e tempo automaticamente
- **Cálculo completo de custos**: material, energia, desgaste de máquina e lucro
- **Preço comercial e preço atacado** gerados automaticamente com arredondamento inteligente
- **Exportação de orçamento em PDF** com layout profissional, logo da empresa e validade de 7 dias
- **Interface limpa e intuitiva** com cards de resultado em destaque

---

## 🖥️ Interface

A calculadora conta com os seguintes campos de entrada:

| Campo | Descrição |
|---|---|
| Nome da peça | Preenchido automaticamente ao importar `.3mf` |
| Peso usado (g) | Extraído automaticamente do arquivo Bambu |
| Preço da bobina (R$) | Informado manualmente |
| Quantidade | Número de unidades a produzir |
| Tempo de impressão | Extraído automaticamente (aceita `2h30`, `2:30`, `150min`) |
| Tarifa de energia (R$/kWh) | Padrão: R$ 0,88 |
| Lucro desejado (%) | Padrão: 50% |
| Observações | Campo livre para notas ao cliente |

---

## 📄 PDF Gerado

O orçamento exportado contém:

- Logo e nome da empresa
- Nome(s) da(s) peça(s), data, quantidade, peso e tempo
- Preço comercial e preço atacado em destaque
- Observações e validade do orçamento
- Rodapé com contatos da empresa

---

## 🚀 Como executar

### Pré-requisitos

- Python 3.10 ou superior
- Pip instalado

### Instalação das dependências

```bash
pip install reportlab pillow pyinstaller
```

### Executando o projeto

```bash
python calculadora3d_v20.py
```

### Gerando o `.exe` (Windows)

```bash
pyinstaller --onefile --windowed --icon=assets\icone_dt3dstudio.ico --add-data "assets;assets" --name "DT3DStudio_Calculadora" calculadora3d_v20.py
```

O executável será gerado em `dist\DT3DStudio_Calculadora.exe`.

---

## 📁 Estrutura do projeto

```
CALCULADORA BAMBU/
│
├── calculadora3d_v20.py     # Código principal
├── README.md                # Este arquivo
│
└── assets/
    ├── icone_dt3dstudio.ico # Ícone da janela e do .exe
    └── icone_dt3dstudio.png # Logo exibida na tela e no PDF
```

---

## 🧮 Fórmula de cálculo

```
Custo material  = (peso_total × preço_bobina) ÷ 1000
Custo energia   = horas_total × 0,1 kWh × tarifa
Custo desgaste  = custo_material × 10%
Custo máquina   = horas_total × R$ 2,00/h

Custo total     = soma dos quatro itens acima
Preço final     = custo_total × (1 + lucro%)
Preço comercial = arredondado para múltiplo de R$ 5
Preço atacado   = preço_comercial × 90%
```

---

## 🛠️ Tecnologias utilizadas

- [Python 3.10+](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html) — interface gráfica
- [ReportLab](https://www.reportlab.com/) — geração de PDF
- [Pillow](https://python-pillow.org/) — exibição do logo na interface
- [PyInstaller](https://pyinstaller.org/) — empacotamento em `.exe`

---

## 👨‍💻 Autor

Desenvolvido para o **DT 3D STUDIO**

---

## 📌 Observações

- O arquivo `.exe` não está incluído no repositório. Para gerá-lo, siga as instruções da seção **Gerando o `.exe`**.
- A pasta `assets` é necessária para exibir o logo na interface e no PDF. Sem ela, o programa funciona normalmente, mas sem imagens.

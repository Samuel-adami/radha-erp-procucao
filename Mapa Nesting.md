# Mapa de Fluxo do Nesting Poligonal

A seguir está um passo‑a‑passo do “fluxo interno” do módulo de produção que leva desde os arquivos de entrada (.dxt e .dxf) até a chamada de `arranjar_poligonos_svgnest` e a extração final de coordenadas para o nesting poligonal.

---

## 1. Localização do arquivo DXT na pasta do lote

Tanto em `gerar_nesting_preview` quanto em `gerar_nesting`, a primeira coisa é descobrir qual é o arquivo `.dxt` na pasta do lote. A rotina percorre os arquivos da pasta e retorna o primeiro com extensão “.dxt” (ignorando maiúsculas/minúsculas):

```python
def _encontrar_dxt(pasta: Path) -> Optional[Path]:
    """Retorna o primeiro arquivo .dxt encontrado ignorando o case."""
    for arq in pasta.iterdir():
        if arq.is_file() and arq.suffix.lower() == ".dxt":
            return arq
    return None
```

E o uso dentro de `gerar_nesting_preview` (fluxo de preview, sem gerar arquivos):

```python
dxt_path = _encontrar_dxt(pasta)
if not dxt_path:
    raise FileNotFoundError("Arquivo DXT não encontrado na pasta do lote")
pecas = _ler_dxt_polygons(dxt_path)
```

De forma análoga em `gerar_nesting` (fluxo que vai gerar DXF, gcode, XML, imagens etc.):

```python
dxt_path = _encontrar_dxt(pasta)
if not dxt_path:
    raise FileNotFoundError("Arquivo DXT não encontrado na pasta do lote")

pecas = _ler_dxt_polygons(dxt_path)
```

---

## 2. Leitura do DXT e extração dos metadados das peças

O arquivo `.dxt` é um XML que descreve cada peça (`Part`, com campos `Length`, `Width`, `Filename`, etc.). A função abaixo faz o parse desse XML e retorna uma lista de dicionários com os metadados básicos de cada peça:

```python
def _ler_dxt(dxt_path: Path) -> List[Dict]:
    """Parse DXT e return piece metadata with cached DXF dimensions."""
    root = ET.fromstring(dxt_path.read_text(encoding="utf-8", errors="ignore"))
    pecas = []
    pasta = dxt_path.parent

    for part in root.findall(".//Part"):
        fields = {
            f.find("Name").text: f.find("Value").text
            for f in part.findall("Field")
            if f.find("Name") is not None and f.find("Value") is not None
        }
        if not fields:
            continue
        try:
            filename = fields.get("Filename", "")
            length = float(fields.get("Length", 0))
            width = float(fields.get("Width", 0))

            if filename:
                if filename not in medidas_cache:
                    medidas_cache[filename] = _medidas_dxf(pasta / filename)
                medidas = medidas_cache.get(filename)
                if medidas:
                    length, width = medidas

            pecas.append(
                {
                    "PartName": fields.get("PartName", "SemNome"),
                    "Length": length,
                    "Width": width,
                    "Thickness": float(fields.get("Thickness", 0)),
                    "Program1": fields.get("Program1", ""),
                    "Material": fields.get("Material", "Desconhecido"),
                    "Filename": filename,
                    "Client": fields.get("Client", ""),
                    "Project": fields.get("Project", ""),
                }
            )
        except ValueError:
            continue
    return pecas
```

---

## 3. Cálculo das dimensões reais a partir do DXF (cache de bounding‑box)

Para corrigir eventuais discrepâncias entre os campos `Length`/`Width` do XML e o contorno real no DXF, existe uma função que lê o arquivo DXF e calcula a bounding‑box dos contornos externos (`borda_externa`, `contorno`) guardando em cache:

```python
def _medidas_dxf(path: Path) -> Optional[Tuple[float, float]]:
    """Return DXF outer dimensions using a global cache."""
    path = path.resolve()
    if path in DXF_DIMENSIONS_CACHE:
        return DXF_DIMENSIONS_CACHE[path]
    try:
        doc = ezdxf.readfile(path)
    except Exception:
        DXF_DIMENSIONS_CACHE[path] = None
        return None
    msp = doc.modelspace()
    xs: List[float] = []
    ys: List[float] = []
    for ent in msp:
        layer = str(ent.dxf.layer).lower()
        if layer in ("borda_externa", "contorno"):
            try:
                if ent.dxftype() == "LINE":
                    xs.extend([float(ent.dxf.start.x), float(ent.dxf.end.x)])
                    ys.extend([float(ent.dxf.start.y), float(ent.dxf.end.y)])
                elif ent.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                    if ent.dxftype() == "POLYLINE":
                        for v in ent.vertices:
                            xs.append(float(v.dxf.location.x))
                            ys.append(float(v.dxf.location.y))
                    else:
                        for pt in ent.get_points("xy"):
                            xs.append(float(pt[0]))
                            ys.append(float(pt[1]))
                elif ent.dxftype() == "CIRCLE":
                    cx = float(ent.dxf.center.x)
                    cy = float(ent.dxf.center.y)
                    r = float(ent.dxf.radius)
                    xs.extend([cx - r, cx + r])
                    ys.extend([cy - r, cy + r])
                elif ent.dxftype() == "ARC":
                    arc = ConstructionArc(
                        ent.dxf.center,
                        ent.dxf.radius,
                        ent.dxf.start_angle,
                        ent.dxf.end_angle,
                    )
                    bbox = arc.bounding_box
                    xs.extend([float(bbox.extmin.x), float(bbox.extmax.x)])
                    ys.extend([float(bbox.extmin.y), float(bbox.extmax.y)])
            except Exception:
                continue
    if not xs or not ys:
        DXF_DIMENSIONS_CACHE[path] = None
        return None
    dims = max(xs) - min(xs), max(ys) - min(ys)
    DXF_DIMENSIONS_CACHE[path] = dims
    return dims
```

---

## 4. Construção dos polígonos das peças (`_ler_dxt_polygons`)

Agora que temos os metadados e as dimensões, monta‑se o verdadeiro **polígono** de cada peça usando **Shapely**. A rotina testa se há um `Filename` (DXF); se houver, abre o arquivo, coleta contornos externos e furos/usinagens, faz union/difference e guarda em cache. Caso contrário, gera um retângulo simples.

```python
def _ler_dxt_polygons(dxt_path: Path) -> List[Dict]:
    """Parse DXT e attach shapely polygons para cada peça."""
    pecas = _ler_dxt(dxt_path)
    pasta = dxt_path.parent

    for p in pecas:
        poly: Optional[Polygon] = None
        filename = p.get("Filename")
        if filename:
            path = (pasta / filename).resolve()
            if path not in DXF_POLYGON_CACHE:
                try:
                    doc = ezdxf.readfile(path)
                    msp = doc.modelspace()
                    contornos: List[Polygon] = []
                    furos:   List[Polygon] = []
                    for ent in msp:
                        layer = str(ent.dxf.layer).lower()
                        poly_ent = _entity_polygon(ent)
                        if not poly_ent:
                            continue
                        if layer in {"borda_externa","contorno"}:
                            contornos.append(poly_ent)
                        elif layer.startswith("furo") or layer.startswith("usinar"):
                            furos.append(poly_ent)
                    if contornos:
                        p_union: Polygon = unary_union(contornos)
                        for f in furos:
                            p_union = p_union.difference(f)
                        if isinstance(p_union, MultiPolygon):
                            p_union = max(p_union.geoms, key=lambda g: g.area)
                        DXF_POLYGON_CACHE[path] = p_union
                    else:
                        DXF_POLYGON_CACHE[path] = None
                except Exception:
                    DXF_POLYGON_CACHE[path] = None
            poly = DXF_POLYGON_CACHE.get(path)

        if poly is None:
            poly = box(0,0,p["Length"],p["Width"])
        p["polygon"] = poly

    return pecas
```

### 4.1. Aproximação de entidades CAD a polígonos Shapely

```python
def _entity_polygon(ent) -> Optional[Polygon]:
    """Return a shapely polygon approximation of a DXF entity."""
    try:
        if ent.dxftype() in {"LWPOLYLINE","POLYLINE"}:
            pts = [(float(p[0]),float(p[1])) for p in ent.get_points("xy")]
            if len(pts) >= 3:
                return Polygon(pts)
        elif ent.dxftype() == "LINE":
            start, end = ent.dxf.start, ent.dxf.end
            return Polygon([(start.x,start.y),(end.x,end.y)])
        elif ent.dxftype() == "CIRCLE":
            return Point(ent.dxf.center.x, ent.dxf.center.y).buffer(ent.dxf.radius, resolution=32)
        elif ent.dxftype() == "ARC":
            # Aproximação em polígono de arco
            ...
    except Exception:
        return None
    return None
```

---

## 5. Agrupamento por material e configurações de chapas

Em `gerar_nesting_preview` ou `gerar_nesting`, as peças são agrupadas por material e carregam-se configurações de chapas (comprimento, largura, veio) e refilos:

```python
pecas_por_material: Dict[str,List[Dict]] = {}
for p in pecas:
    material = p.get("Material","Desconhecido")
    pecas_por_material.setdefault(material,[]).append(p)

if estoque is None:
    estoque = _carregar_estoque(list(pecas_por_material.keys()))

espaco   = float(config_maquina.get("espacoEntrePecas",0)) if config_maquina else 0
ref_inf  = _cfg_val(config_maquina,"refiloInferior","refilo_inferior")
ref_sup  = _cfg_val(config_maquina,"refiloSuperior","refilo_superior")
ref_esq  = _cfg_val(config_maquina,"refiloEsquerda","refilo_esquerda")
ref_dir  = _cfg_val(config_maquina,"refiloDireita","refilo_direita")
area_larg= largura_chapa - ref_esq - ref_dir
area_alt = altura_chapa  - ref_inf - ref_sup

for material, lista in pecas_por_material.items():
    cfg = chapas_cfg.get(material,{})
    rot = False if cfg.get("possui_veio") else True
    largura = float(cfg.get("comprimento", area_larg))
    altura  = float(cfg.get("largura",   area_alt))

    chapas_polys = arranjar_poligonos_svgnest(
        lista,
        largura,
        altura,
        espaco,
        rot,
        estoque.get(material) if estoque else None,
        config_maquina=config_maquina,
        config_layers=config_layers,
        ferramentas=ferramentas,
    )
```

---

## 6. Montagem do SVG de entrada em `arranjar_poligonos_svgnest`

```python
# 1) cria <svg> com <rect> para a chapa e <polygon> para peças e operações internas
svg = ET.Element("svg", { ... })
ET.SubElement(svg,"rect",{...})
for idx,p in enumerate(pecas):
    pts = " ".join(f"{x},{y}" for x,y in p["polygon"].exterior.coords)
    ET.SubElement(svg,"polygon",{"id":str(idx),"points":pts,...})
    for op in p.get("operacoes",[]):
        # operação interna como <polygon>
        ...
```

---

## 7. Invocação do svgnest e leitura do SVG resultante

```python
# svgnest-python inspeciona arquivos de entrada com sufixo de índice (0,1,...) mesmo para uma única cópia
svgnest.nest({svg_path: 1}, wbin, hbin)
with open(os.path.join(tempdir, "combined.svg"), encoding="utf-8") as f:
    resultado_svg = f.read()
```

---

## 8. Extração de transformações (translate/rotate) do SVG de saída

```python
root = ET.fromstring(resultado_svg)
placas: List[List[Dict]] = [[]]
for elem in root.findall(".//*[@id]"):
    tid = elem.attrib["id"]
    tx=ty=theta=0.0
    tr = elem.attrib.get("transform","")
    # parse translate(x,y) e rotate(angle)
    ...
    nova = pecas[pid].copy()
    if isinstance(nova.get("polygon"),Polygon) and rotacionar:
        pm = nova["polygon"]
        pr = affinity.rotate(pm,theta,origin=(0,0))
        nova["polygon"] = affinity.translate(pr,tx,ty)
    nova.update({"x":tx+ref_esq,"y":ty+ref_inf,"rotationAngle":theta if rotacionar else 0})
    placas[0].append(nova)
return placas
```

---

## 9. Pós‑processamento em `gerar_nesting`

```python
for placa in chapas_polys:
    if not placa: continue
    for p in placa:
        # ajusta x/y de refilos e extrai operações via _ops_from_dxf()
        if p.get("Filename") and config_layers:
            dxf_ops = _ops_from_dxf(...)
            for d in dxf_ops:
                operacoes.append(d)
```

---

### Resumo do fluxo `entrada → polygons → nesting → coordenadas`

| Etapa                      | Função / Arquivo                      |
|----------------------------|---------------------------------------|
| 1. Localizar DXT           | `_encontrar_dxt`                      |
| 2. Ler DXT                 | `_ler_dxt`                            |
| 3. Medidas DXF             | `_medidas_dxf`                        |
| 4. Polígonos Shapely       | `_ler_dxt_polygons`                   |
| 4.1 Entidades → Polígonos  | `_entity_polygon`                     |
| 5. Configurações de chapas | `gerar_nesting[_preview]`             |
| 6. Identificar retângulos  | `arranjar_poligonos`                  |
| 7. Empacotar retângulos    | `rectpack.newPacker`                  |
| 8. Nesting orgânico        | `nest2D.nest`                         |
| 9. Extração pós-nesting    | `_ops_from_dxf` e `gerar_nesting`     |

**Fonte:** Código-fonte do módulo `nesting.py` em produção.

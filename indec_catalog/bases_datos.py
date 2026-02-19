"""Scraper y parser para la página Institucional Bases de datos del INDEC."""

import re
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup, Tag

from indec_catalog.config import BASES_DATOS_URL, BASE_URL, DATA_EXTENSIONS, HTTP_TIMEOUT
from indec_catalog.models import Catalog
from indec_catalog.parser import _normalize_url

FALLBACK_TITLE = "Bases de datos"


def _is_level1_title(el: Tag) -> bool:
    """
    Título de nivel 1 (subtema): sección principal dentro del tab.
    Incluye h3–h6 y <p> con clase fontsize20/fontsize24/font-color-violeta o style font-size:20px.
    """
    if not el.get_text(strip=True):
        return False
    if el.name in ("h3", "h4", "h5", "h6"):
        return True
    if el.name != "p":
        return False
    classes = el.get("class") or []
    if isinstance(classes, str):
        classes = [classes]
    if (
        any("fontsize20" in c for c in classes)
        or any("fontsize24" in c for c in classes)
        or any("font-color-violeta" in c for c in classes)
    ):
        return True
    style = (el.get("style") or "").lower()
    if "font-size" in style and "20px" in style:
        return True
    return False


def _is_level2_title(el: Tag) -> bool:
    """
    Título de nivel 2 (agrupamiento): subsección dentro del tab.
    Ej.: div.sub_enc_salud_tit ("Documentos metodológicos", "Bases de microdatos", etc.).
    """
    return (
        el.name == "div"
        and el.get("class") is not None
        and "sub_enc_salud_tit" in (el.get("class") or [])
        and bool(el.get_text(strip=True))
    )


def _normalize_section_text(text: str) -> str:
    """Quita el carácter ▾ y espacios extra del texto de sección."""
    if not text:
        return text
    return re.sub(r"\s*▾\s*$", "", text).strip()


def _first_level1_text_in_tab(tab: Tag) -> str:
    """Devuelve el texto del primer título L1 en el tab (p. ej. 'Encuesta Permanente de Hogares (EPH)')."""
    for tag in tab.find_all(_is_level1_title):
        return _normalize_section_text(tag.get_text(strip=True))
    return FALLBACK_TITLE


def _link_inside_any(link: Tag, candidates: List[Tag]) -> bool:
    """True si link es descendiente de alguno de los tags en candidates."""
    for c in candidates:
        if link in c.descendants or link == c:
            return True
    return False


def _agrupamiento_enlace_li(link: Tag) -> str:
    """
    Para enlaces dentro de la estructura ul/li.enlaces_li con div.enlace_li_tit:
    devuelve la cadena de títulos (enlace_li_tit) desde el enlace hacia arriba,
    más el texto del li.a-color2 que agrupa el enlace (p. ej. 'Bases del tercer trimestre 2024').
    """
    parts: List[str] = []
    parent = link.parent
    while parent and parent.name:
        if parent.name == "div" and parent.get("class") and "enlace_li_tit" in (parent.get("class") or []):
            t = _normalize_section_text(parent.get_text(strip=True))
            if t:
                parts.append(t)
        parent = parent.parent if hasattr(parent, "parent") else None

    # li.a-color2 que es padre del ul que contiene el enlace: texto antes del <ul>
    a_parent = link.parent
    while a_parent and getattr(a_parent, "name", None) != "ul":
        a_parent = a_parent.parent if hasattr(a_parent, "parent") else None
    if a_parent and getattr(a_parent, "parent", None):
        li_cont = a_parent.parent
        if li_cont and getattr(li_cont, "get", None) and (li_cont.get("class") or []) and "a-color2" in (li_cont.get("class") or []):
            # texto directo antes del primer <ul>
            before_ul: List[str] = []
            for child in getattr(li_cont, "children", []):
                if getattr(child, "name", None) == "ul":
                    break
                if hasattr(child, "get_text"):
                    before_ul.append(child.get_text(strip=True))
                else:
                    before_ul.append(str(child).strip() if hasattr(child, "strip") else "")
            text_before = " ".join(filter(None, before_ul)).strip()
            if text_before:
                parts.append(_normalize_section_text(text_before))
    parts.reverse()
    return " | ".join(parts) if parts else ""


def _get_preceding_strong(a: Tag, tab: Tag) -> str | None:
    """
    Devuelve el texto del último <strong> que precede al enlace dentro del mismo tab,
    o None si no hay. Se usa como nivel 3 para enriquecer agrupamiento (p. ej. tab1 EPH:
    "Tercer trimestre 2025.", "Base individual y hogar...").
    """
    def inside_tab(tag: Tag) -> bool:
        return tag == tab or tab in list(tag.parents)

    prev_strong = [
        t
        for t in a.find_all_previous("strong")
        if inside_tab(t) and t.get_text(strip=True)
    ]
    if not prev_strong:
        return None
    return _normalize_section_text(prev_strong[0].get_text(strip=True))


def _get_hierarchy_for_link(a: Tag, tab: Tag) -> Tuple[str, str]:
    """
    Para un enlace dentro de tab, devuelve (subtema, agrupamiento) según la jerarquía
    del DOM:
    - L1 (subtema): p/h con título principal (fontsize20, font-color-violeta, h3–h6).
    - L2/L3 (agrupamiento): div.sub_enc_salud_tit y, si existe, el último <strong>
      precedente (p. ej. "Bases de microdatos | Tercer trimestre 2025.").
    """
    def inside_tab(tag: Tag) -> bool:
        return tag == tab or tab in list(tag.parents)

    prev_l1 = [
        t
        for t in a.find_all_previous(_is_level1_title)
        if inside_tab(t)
    ]
    prev_l2 = [
        t
        for t in a.find_all_previous(_is_level2_title)
        if inside_tab(t)
    ]
    strong_text = _get_preceding_strong(a, tab)

    subtema = _normalize_section_text(prev_l1[0].get_text(strip=True)) if prev_l1 else FALLBACK_TITLE
    if prev_l2:
        agrupamiento = _normalize_section_text(prev_l2[0].get_text(strip=True))
        if strong_text:
            agrupamiento = agrupamiento + " | " + strong_text
    elif strong_text:
        agrupamiento = strong_text
    else:
        agrupamiento = subtema
    return subtema, agrupamiento


def _get_hierarchy_for_link_tab1(
    a: Tag,
    tab: Tag,
    first_5_enlaces_li: List[Tag],
    first_l1_text: str,
) -> Tuple[str, str]:
    """
    Jerarquía específica para el div id=tab1 (Mercado laboral).
    - Enlaces dentro de los primeros 5 li.enlaces_li → subtema = primer L1 del tab (EPH).
    - Resto → subtema = último p fontsize20/fontsize24 font-color-violeta precedente;
      agrupamiento = cadena div.enlace_li_tit + texto li.a-color2 cuando aplica.
    """
    def inside_tab(tag: Tag) -> bool:
        return tag == tab or tab in list(tag.parents)

    if _link_inside_any(a, first_5_enlaces_li):
        subtema = first_l1_text
        prev_l2 = [t for t in a.find_all_previous(_is_level2_title) if inside_tab(t)]
        strong_text = _get_preceding_strong(a, tab)
        if prev_l2:
            agrupamiento = _normalize_section_text(prev_l2[0].get_text(strip=True))
            if strong_text:
                agrupamiento = agrupamiento + " | " + strong_text
        elif strong_text:
            agrupamiento = strong_text
        else:
            agrupamiento = subtema
        return subtema, agrupamiento

    # 6.º li.enlaces_li en adelante: L1 = último p fontsize20/24 font-color-violeta
    prev_l1 = [t for t in a.find_all_previous(_is_level1_title) if inside_tab(t)]
    subtema = _normalize_section_text(prev_l1[0].get_text(strip=True)) if prev_l1 else FALLBACK_TITLE
    agrup = _agrupamiento_enlace_li(a)
    if agrup:
        agrupamiento = agrup
    else:
        prev_l2 = [t for t in a.find_all_previous(_is_level2_title) if inside_tab(t)]
        strong_text = _get_preceding_strong(a, tab)
        if prev_l2:
            agrupamiento = _normalize_section_text(prev_l2[0].get_text(strip=True))
            if strong_text:
                agrupamiento = agrupamiento + " | " + strong_text
        elif strong_text:
            agrupamiento = strong_text
        else:
            agrupamiento = subtema
    return subtema, agrupamiento


def _extract_sections_with_links(tab: Tag, base_url: str) -> List[Tuple[str, str, List[Dict[str, str]]]]:
    """
    Dentro de un tabContent, extrae enlaces de datos y para cada uno determina
    subtema y agrupamiento según la jerarquía del DOM (L1=subtema, L2/L3=agrupamiento).
    L3 es el texto del <strong> precedente cuando existe (p. ej. tab1 EPH).
    Devuelve lista de (subtema, agrupamiento, archivos) para agrupar después.
    """
    # Agrupar por (subtema, agrupamiento) para juntar enlaces del mismo bloque
    groups: Dict[Tuple[str, str], List[Dict[str, str]]] = {}

    is_tab1 = tab.get("id") == "tab1"
    first_5_enlaces_li: List[Tag] = []
    first_l1_tab1 = FALLBACK_TITLE
    if is_tab1:
        all_li = tab.find_all("li", class_="enlaces_li")
        first_5_enlaces_li = all_li[:5]
        first_l1_tab1 = _first_level1_text_in_tab(tab)

    for a in tab.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href:
            continue
        href_lower = href.lower()
        if not any(href_lower.endswith(ext) for ext in DATA_EXTENSIONS):
            continue

        if is_tab1:
            subtema, agrupamiento = _get_hierarchy_for_link_tab1(
                a, tab, first_5_enlaces_li, first_l1_tab1
            )
        else:
            subtema, agrupamiento = _get_hierarchy_for_link(a, tab)
        key = (subtema, agrupamiento)
        archivo = {
            "nombre_archivo": a.get_text(strip=True),
            "url": _normalize_url(href, base_url),
        }
        groups.setdefault(key, []).append(archivo)

    return [(st, ag, archs) for (st, ag), archs in groups.items()]


def scrape_bases_datos(
    url: str = BASES_DATOS_URL,
    base_url: str = BASE_URL,
) -> List[Catalog]:
    """
    Descarga la página Bases de datos, parsea secciones y extrae enlaces de datos.

    Jerarquía: tema="Bases de datos"; subtema=L1 (p/h título); agrupamiento=L2
    (div.sub_enc_salud_tit) y, si existe, L3 (último <strong> precedente, p. ej.
    "Bases de microdatos | Tercer trimestre 2025."). Así cada archivo queda con
    metadata completa (incl. texto de strong en tab1 EPH).

    Args:
        url: URL de la página Bases de datos.
        base_url: URL base para normalizar enlaces.

    Returns:
        Lista de Catalog con tema "Bases de datos", subtema/agrupamiento por subsección.

    Raises:
        requests.RequestException: Si falla la petición HTTP.
    """
    response = requests.get(url, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"

    soup = BeautifulSoup(response.content, "html.parser")
    tema = "Bases de datos"

    tabs = soup.find_all("div", class_="tabContent")
    results: List[Catalog] = []

    for tab in tabs:
        sections = _extract_sections_with_links(tab, base_url)
        for subtema, agrupamiento, archivos in sections:
            if not archivos:
                continue
            results.append(
                Catalog(
                    tema=tema,
                    subtema=subtema,
                    agrupamiento=agrupamiento,
                    archivos=archivos,
                )
            )

    return results


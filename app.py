import re
import requests
import streamlit as st

st.set_page_config(page_title="Evaluación de Investigación", page_icon="📊")
st.title("Buscador de Métricas por DOI")


def limpiar_doi(doi_input: str) -> str:
    """Elimina prefijos de URL para dejar únicamente el identificador DOI."""
    doi = doi_input.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi


def obtener_openalex(doi: str) -> tuple:
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            citas = data.get("cited_by_count", "N/D")
            fwci = data.get("fwci", "N/D")
            return citas, fwci
    except Exception:
        pass
    return "No encontrado", "No encontrado"


def obtener_dimensions(doi: str) -> tuple:
    url = f"https://metrics-api.dimensions.ai/doi/{doi}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            citas = data.get("times_cited", "N/D")
            fcr = data.get("fcr", "N/D")
            return citas, fcr
    except Exception:
        pass
    return "No encontrado", "No encontrado"


def obtener_scopus(doi: str) -> tuple:
    api_key = st.secrets.get("ELSEVIER_API_KEY", "")
    inst_token = st.secrets.get("ELSEVIER_INST_TOKEN", "")
    if not api_key:
        return "Requiere API Key", "Requiere API Key (SciVal)"

    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token

    try:
        # 1. Citas en Scopus Search API
        url_scopus = f"https://api.elsevier.com/content/search/scopus?query=DOI({doi})"
        r = requests.get(url_scopus, headers=headers, timeout=10)
        citas, eid = "N/D", None
        if r.status_code == 200:
            entries = r.json().get("search-results", {}).get("entry", [])
            if entries and "error" not in entries[0]:
                citas = entries[0].get("citedby-count", "N/D")
                eid = entries[0].get("eid")

        # 2. FWCI en SciVal (requiere permisos de SciVal API o cálculo vía PlumX/SciVal)
        fwci = "Pendiente endpoint SciVal" if eid else "N/D"
        return citas, fwci
    except Exception:
        return "Error de conexión", "Error de conexión"


def obtener_wos_incites(doi: str) -> tuple:
    wos_key = st.secrets.get("CLARIVATE_API_KEY", "")
    if not wos_key:
        return "Requiere API Key", "Requiere API Key (InCites)"

    headers = {"X-ApiKey": wos_key, "Accept": "application/json"}
    try:
        # Consulta mediante Web of Science Starter / InCites API
        url_wos = f"https://api.clarivate.com/apis/wos-starter/v1/documents?q=DO={doi}"
        r = requests.get(url_wos, headers=headers, timeout=10)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            if hits:
                citas = (
                    hits[0].get("citations", [{}])[0].get("count", "N/D")
                )
                return citas, "Requiere endpoint InCites con UT"
    except Exception:
        pass
    return "No encontrado", "No encontrado"


# Interfaz de búsqueda
doi_usuario = st.text_input(
    "Introduce el DOI del artículo:", placeholder="10.1038/s41586-020-2649-2"
)

if doi_usuario:
    doi_limpio = limpiar_doi(doi_usuario)
    with st.spinner(f"Consultando bases de datos para {doi_limpio}..."):
        oa_citas, oa_fwci = obtener_openalex(doi_limpio)
        dim_citas, dim_fcr = obtener_dimensions(doi_limpio)
        sco_citas, sco_fwci = obtener_scopus(doi_limpio)
        wos_citas, wos_cnci = obtener_wos_incites(doi_limpio)

    resultado_texto = (
        f"Resultados para el DOI {doi_limpio}:\n\n"
        f"- OpenAlex: {oa_citas} citas | FWCI: {oa_fwci}\n"
        f"- Dimensions: {dim_citas} citas | FCR: {dim_fcr}\n"
        f"- Web of Science: {wos_citas} citas | CNCI: {wos_cnci}\n"
        f"- Scopus: {sco_citas} citas | FWCI: {sco_fwci}"
    )

    st.subheader("Informe de métricas")
    st.text_area("Resumen extraído:", value=resultado_texto, height=160)

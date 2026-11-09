import re
import requests
import streamlit as st

st.set_page_config(page_title="Evaluación de Investigación", page_icon="📊")
st.title("Buscador y Diagnóstico de Métricas por DOI")

# Cajas seguras en la barra lateral (no se guardan en GitHub)
st.sidebar.header("Configuración de APIs")
scopus_key = st.sidebar.text_input("API Key de Scopus", type="password")
wos_key = st.sidebar.text_input("API Key de WoS", type="password")

doi_input = st.text_input(
    "Introduce el DOI del artículo:", value="10.1038/s41586-020-2649-2"
)

if st.button("Consultar métricas") and doi_input:
    doi = re.sub(
        r"^https?://(dx\.)?doi\.org/",
        "",
        doi_input.strip(),
        flags=re.IGNORECASE,
    )

    with st.spinner("Consultando bases de datos..."):
        # 1. OpenAlex
        oa_citas, oa_fwci = "No encontrado", "No encontrado"
        r_oa = requests.get(
            f"https://api.openalex.org/works/https://doi.org/{doi}", timeout=10
        )
        if r_oa.status_code == 200:
            oa_citas = r_oa.json().get("cited_by_count", "N/D")
            oa_fwci = r_oa.json().get("fwci", "N/D")

        # 2. Dimensions
        dim_citas, dim_fcr = "No encontrado", "No encontrado"
        r_dim = requests.get(
            f"https://metrics-api.dimensions.ai/doi/{doi}", timeout=10
        )
        if r_dim.status_code == 200:
            dim_citas = r_dim.json().get("times_cited", "N/D")
            dim_fcr = r_dim.json().get("fcr", "N/D")

        # 3. Scopus + SciVal
        sco_citas, sco_fwci = "Falta API Key", "Falta API Key"
        if scopus_key:
            headers_els = {
                "X-ELS-APIKey": scopus_key.strip(),
                "Accept": "application/json",
            }
            r_sco = requests.get(
                f"https://api.elsevier.com/content/search/scopus?query=DOI({doi})",
                headers=headers_els,
                timeout=10,
            )
            if r_sco.status_code == 200:
                entries = (
                    r_sco.json().get("search-results", {}).get("entry", [])
                )
                if entries and "error" not in entries[0]:
                    sco_citas = entries[0].get("citedby-count", "Restringido")
                    scopus_id = (
                        entries[0]
                        .get("dc:identifier", "")
                        .replace("SCOPUS_ID:", "")
                    )
                    # Prueba SciVal FWCI
                    r_scival = requests.get(
                        f"https://api.elsevier.com/analytics/scival/publication/metrics?metricTypes=FieldWeightedCitationImpact&publicationIds={scopus_id}&byYear=false",
                        headers=headers_els,
                        timeout=10,
                    )
                    if r_scival.status_code == 200:
                        res = r_scival.json().get("results", [])
                        sco_fwci = (
                            res[0].get("metrics", [{}])[0].get("value", "N/D")
                            if res
                            else "N/D"
                        )
                    else:
                        sco_fwci = f"Sin acceso SciVal (Error {r_scival.status_code})"
                else:
                    sco_citas, sco_fwci = "DOI no encontrado", "N/D"
            else:
                sco_citas = f"Error {r_sco.status_code} (Revisa IP/Clave)"
                sco_fwci = "N/D"

        # 4. WoS + InCites
        wos_citas, wos_cnci = "Falta API Key", "Falta API Key"
        if wos_key:
            headers_wos = {
                "X-ApiKey": wos_key.strip(),
                "Accept": "application/json",
            }
            r_wos = requests.get(
                f"https://api.clarivate.com/apis/wos-starter/v1/documents?q=DO=({doi})",
                headers=headers_wos,
                timeout=10,
            )
            if r_wos.status_code == 200:
                hits = r_wos.json().get("hits", [])
                if hits:
                    citas_list = hits[0].get("citations", [])
                    wos_citas = (
                        citas_list[0].get("count", "Plan sin citas")
                        if citas_list
                        else "N/D"
                    )
                    ut = hits[0].get("uid", "").replace("WOS:", "")
                    # Prueba InCites CNCI
                    r_inc = requests.get(
                        f"https://api.clarivate.com/api/incites/DocumentLevelMetricsByUT/json?UT={ut}",
                        headers=headers_wos,
                        timeout=10,
                    )
                    if r_inc.status_code == 200:
                        rval = r_inc.json().get("api", [{}])[0].get("rval", [])
                        wos_cnci = rval[0].get("JNCI", "N/D") if rval else "N/D"
                    else:
                        wos_cnci = (
                            f"Sin acceso InCites (Error {r_inc.status_code})"
                        )
                else:
                    wos_citas, wos_cnci = "DOI no encontrado", "N/D"
            else:
                wos_citas = f"Error {r_wos.status_code}"
                wos_cnci = "N/D"

    informe = (
        f"Resultados para el DOI {doi}:\n\n"
        f"- OpenAlex: {oa_citas} citas | FWCI: {oa_fwci}\n"
        f"- Dimensions: {dim_citas} citas | FCR: {dim_fcr}\n"
        f"- Web of Science: {wos_citas} citas | CNCI: {wos_cnci}\n"
        f"- Scopus: {sco_citas} citas | FWCI: {sco_fwci}"
    )
    st.text_area("Informe de métricas:", value=informe, height=180)

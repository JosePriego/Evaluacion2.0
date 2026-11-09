import requests

# Las claves se piden por pantalla al ejecutar; no quedan guardadas en el código
SCOPUS_API_KEY = input("Introduce tu API Key de Scopus y pulsa Enter: ").strip()
WOS_API_KEY = input("Introduce tu API Key de WoS y pulsa Enter: ").strip()

DOI_PRUEBA = "10.1038/s41586-020-2649-2"
print(f"\n=== DIAGNÓSTICO DE APIS PARA EL DOI: {DOI_PRUEBA} ===\n")

# 1. ELSEVIER (Scopus + SciVal)
if SCOPUS_API_KEY:
    headers_els = {"X-ELS-APIKey": SCOPUS_API_KEY, "Accept": "application/json"}
    url_scopus = f"https://api.elsevier.com/content/search/scopus?query=DOI({DOI_PRUEBA})"
    r_scopus = requests.get(url_scopus, headers=headers_els, timeout=10)

    if r_scopus.status_code == 200:
        entries = r_scopus.json().get("search-results", {}).get("entry", [])
        citas = entries[0].get("citedby-count", "Restringido") if entries else "N/D"
        scopus_id = entries[0].get("dc:identifier", "").replace("SCOPUS_ID:", "") if entries else None
        print(f"[OK] Scopus Citas: {citas} (ID: {scopus_id})")

        if scopus_id:
            url_scival = f"https://api.elsevier.com/analytics/scival/publication/metrics?metricTypes=FieldWeightedCitationImpact&publicationIds={scopus_id}&byYear=false"
            r_scival = requests.get(url_scival, headers=headers_els, timeout=10)
            print(f"[{'OK' if r_scival.status_code == 200 else 'SIN ACCESO'}] SciVal FWCI (Código {r_scival.status_code})")
    else:
        print(f"[FALLO] Scopus Search (Código {r_scopus.status_code})")

# 2. CLARIVATE (WoS + InCites)
if WOS_API_KEY:
    headers_wos = {"X-ApiKey": WOS_API_KEY, "Accept": "application/json"}
    url_wos = f"https://api.clarivate.com/apis/wos-starter/v1/documents?q=DO=({DOI_PRUEBA})"
    r_wos = requests.get(url_wos, headers=headers_wos, timeout=10)

    if r_wos.status_code == 200:
        hits = r_wos.json().get("hits", [])
        ut = hits[0].get("uid", "").replace("WOS:", "") if hits else None
        citas_list = hits[0].get("citations", []) if hits else []
        citas_wos = citas_list[0].get("count", "Restringido") if citas_list else "No incluido"
        print(f"[OK] WoS Starter Citas: {citas_wos} (UT: {ut})")

        if ut:
            url_inc = f"https://api.clarivate.com/api/incites/DocumentLevelMetricsByUT/json?UT={ut}"
            r_inc = requests.get(url_inc, headers=headers_wos, timeout=10)
            print(f"[{'OK' if r_inc.status_code == 200 else 'SIN ACCESO'}] InCites CNCI (Código {r_inc.status_code})")
    else:
        print(f"[FALLO] WoS Starter (Código {r_wos.status_code})")

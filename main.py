from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FirmaRequest(BaseModel):
    firmanavn: str
    orgnr: str
    meta_token: str = ""

@app.post("/api/firma")
async def hent_firmadata(req: FirmaRequest):
    try:
        brreg_data = hent_brreg_info(req.orgnr)
        gulesider_data = søk_gulesider(req.firmanavn)
        meta_ads_data = hent_meta_ads(req.firmanavn, req.meta_token) if req.meta_token else []
        google_results_data = søk_google(req.firmanavn)

        return {
            "brreg": brreg_data,
            "gulesider": gulesider_data,
            "meta_ads": meta_ads_data,
            "google_results": google_results_data
        }
    except Exception as e:
        return { "error": str(e) }

def hent_brreg_info(orgnr):
    url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{orgnr}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def søk_gulesider(firmanavn):
    søkeord = firmanavn.replace(' ', '+')
    url = f"https://www.gulesider.no/firma/{søkeord}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            firma_div = soup.find('div', class_="search-hit-content")
            if firma_div:
                h2_elem = firma_div.find('h2')
                addr_elem = firma_div.find('span', class_='address')
                navn = h2_elem.text.strip() if h2_elem else None
                adresse = addr_elem.text.strip() if addr_elem else None
                return {'navn': navn, 'adresse': adresse}
    except Exception:
        pass
    return None

def hent_meta_ads(sidenavn, access_token):
    if not access_token:
        return []
    url = "https://graph.facebook.com/v18.0/ads_archive"
    params = {
        "search_terms": sidenavn,
        "ad_type": "ALL",
        "fields": "ad_creative_body,ad_delivery_start_time,ad_snapshot_url,page_name",
        "access_token": access_token
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception:
        pass
    return []

def søk_google(firmanavn):
    return [
        {"title": f"{firmanavn} - Offisiell nettside", "link": f"https://{firmanavn.lower().replace(' ', '')}.no"},
        {"title": f"{firmanavn} på Facebook", "link": f"https://facebook.com/{firmanavn.lower().replace(' ', '')}"}
    ]

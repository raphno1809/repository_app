import streamlit as st
import hashlib
import requests
from pathlib import Path

st.set_page_config(page_title="Beauty Contest App", page_icon="🎯")

# ======================
# Helpers
# ======================

@st.cache_data
def load_api_urls(info_path: str = "info.txt"):
    """
    Lit le fichier info.txt et retourne un dict avec les URLs.
    Format attendu de info.txt :
        COMMIT_URL=https://...
        REVEAL_URL=https://...
    """
    info_file = Path(info_path)
    if not info_file.exists():
        raise FileNotFoundError(f"{info_path} not found")

    api_info = {}
    with info_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Ignore lignes vides ou commentaires
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                api_info[key.strip()] = value.strip()

    return api_info


def compute_sha256(uni_id: str, number: int, nonce: str) -> tuple[str, str]:
    """
    Construit le preimage et calcule sha256(f"{uni_id}|{number}|{nonce}")
    Retourne (preimage, hash_hex)
    """
    preimage = f"{uni_id}|{number}|{nonce}"
    hash_hex = hashlib.sha256(preimage.encode("utf-8")).hexdigest()
    return preimage, hash_hex


def commit_to_api(commit_url: str, uni_id: str, commit_hash: str) -> requests.Response:
    """
    Envoie {uni_id, commit} à l'API de commit.
    """
    payload = {
        "uni_id": uni_id,
        "commit": commit_hash
    }
    response = requests.post(commit_url, json=payload, timeout=10)
    return response


def reveal_to_api(reveal_url: str, uni_id: str, number: int, nonce: str) -> requests.Response:
    """
    Envoie {uni_id, number, nonce} à l'API de reveal.
    """
    payload = {
        "uni_id": uni_id,
        "number": number,
        "nonce": nonce
    }
    response = requests.post(reveal_url, json=payload, timeout=10)
    return response


# ======================
# App Streamlit
# ======================

st.title("🎯 Beauty Contest – Commit & Reveal")
st.write(
    "Cette application te permet de **committer** puis de **révéler** ton nombre "
    "pour le Beauty Contest."
)

# Chargement des URLs d'API depuis info.txt
try:
    api_info = load_api_urls("info.txt")  # mets app.py et info.txt dans le même dossier
    COMMIT_URL = api_info.get("COMMIT_URL", "")
    REVEAL_URL = api_info.get("REVEAL_URL", "")
except FileNotFoundError as e:
    st.error(
        "Le fichier `info.txt` n'a pas été trouvé. "
        "Place `app.py` et `info.txt` dans le même dossier, "
        "ou modifie le chemin dans `load_api_urls()`."
    )
    COMMIT_URL = ""
    REVEAL_URL = ""

st.markdown("### 1️⃣ Inputs")

uni_id = st.text_input("NEOMA ID")
number = st.number_input("Ton nombre (entre 0 et 100)", min_value=0, max_value=100, step=1)
nonce = st.text_input("Nonce secret (mot de passe)", type="password")

st.markdown("---")
st.markdown("### 2️⃣ Actions")

col1, col2 = st.columns(2)

with col1:
    commit_clicked = st.button("🔒 Commit")

with col2:
    reveal_clicked = st.button("🔓 Reveal")

st.markdown("---")
st.markdown("### 3️⃣ Résultats")

# ======================
# Commit Phase
# ======================
if commit_clicked:
    if not uni_id or nonce == "":
        st.error("Merci de remplir **NEOMA ID** et **nonce**.")
    elif COMMIT_URL == "":
        st.error("COMMIT_URL introuvable. Vérifie ton `info.txt`.")
    else:
        # Calcul du hash
        preimage, commit_hash = compute_sha256(uni_id, int(number), nonce)

        st.subheader("Commit Phase")
        st.write("**Preimage utilisé pour le hash :**")
        st.code(preimage, language="text")

        st.write("**SHA-256 hash :**")
        st.code(commit_hash, language="text")

        # Envoi à l'API
        try:
            response = commit_to_api(COMMIT_URL, uni_id, commit_hash)
            if response.ok:
                st.success("✅ Commit envoyé avec succès à l'API.")
            else:
                st.error(
                    f"❌ Erreur de l'API (status {response.status_code}). "
                    f"Réponse : {response.text}"
                )
        except Exception as e:
            st.error(f"❌ Erreur lors de l'appel API de commit : {e}")


# ======================
# Reveal Phase
# ======================
if reveal_clicked:
    if not uni_id or nonce == "":
        st.error("Merci de remplir **NEOMA ID** et **nonce**.")
    elif REVEAL_URL == "":
        st.error("REVEAL_URL introuvable. Vérifie ton `info.txt`.")
    else:
        st.subheader("Reveal Phase")

        try:
            response = reveal_to_api(REVEAL_URL, uni_id, int(number), nonce)
            if response.ok:
                st.success("✅ Reveal envoyé avec succès à l'API.")
                st.write("Message de confirmation de l'API :")
                st.code(response.text, language="text")
            else:
                st.error(
                    f"❌ Erreur de l'API (status {response.status_code}). "
                    f"Réponse : {response.text}"
                )
        except Exception as e:
            st.error(f"❌ Erreur lors de l'appel API de reveal : {e}")

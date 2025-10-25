# À propos de ce fork

Ce fork a été créé pour améliorer la flexibilité de la configuration LLM dans `browser-use`.
Ce fork a été fait depuis la version 0.8.0 de browseruse. 

## Fichier modifié
- `browser_use/mcp/server.py`
- `browser_use/config.py`

## Modifications principales
- **Ajout de variables d'environnement manquantes** pour la configuration (notamment pour Azure OpenAI et la sélection du modèle LLM).
- **Modularité du choix du LLM** : il est désormais possible de choisir dynamiquement entre OpenAI et Azure OpenAI via les variables d'environnement, sans modifier le code.
- La logique de sélection du modèle, de la clé API et des endpoints est unifiée et priorise les variables d'environnement officielles.

---

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./static/browser-use-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="./static/browser-use.png">
  <img alt="Shows a black Browser Use Logo in light color mode and a white one in dark color mode." src="./static/browser-use.png"  width="full">
</picture>

<h1 align="center">Enable AI to control your browser</h1>

[![Docs](https://img.shields.io/badge/Docs-📕-blue?style=for-the-badge)](https://docs.browser-use.com)
[![Browser-use cloud](https://img.shields.io/badge/Browser_Use_Cloud-☁️-blue?style=for-the-badge&logo=rocket&logoColor=white)](https://cloud.browser-use.com)

[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Twitter Follow](https://img.shields.io/twitter/follow/Gregor?style=social)](https://x.com/intent/user?screen_name=gregpr07)
[![Twitter Follow](https://img.shields.io/twitter/follow/Magnus?style=social)](https://x.com/intent/user?screen_name=mamagnus00)
[![Merch store](https://img.shields.io/badge/Merch_store-👕-blue)](https://browsermerch.com)
[![Weave Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fapp.workweave.ai%2Fapi%2Frepository%2Fbadge%2Forg_T5Pvn3UBswTHIsN1dWS3voPg%2F881458615&labelColor=#EC6341)](https://app.workweave.ai/reports/repository/org_T5Pvn3UBswTHIsN1dWS3voPg/881458615)





<!-- Keep these links. Translations will automatically update with the README. -->
[Deutsch](https://www.readme-i18n.com/browser-use/browser-use?lang=de) |
[Español](https://www.readme-i18n.com/browser-use/browser-use?lang=es) |
[français](https://www.readme-i18n.com/browser-use/browser-use?lang=fr) |
[日本語](https://www.readme-i18n.com/browser-use/browser-use?lang=ja) |
[한국어](https://www.readme-i18n.com/browser-use/browser-use?lang=ko) |
[Português](https://www.readme-i18n.com/browser-use/browser-use?lang=pt) |
[Русский](https://www.readme-i18n.com/browser-use/browser-use?lang=ru) |
[中文](https://www.readme-i18n.com/browser-use/browser-use?lang=zh)


# 🤖 Quickstart

With uv (Python>=3.11):

```bash
#  We ship every day - use the latest version!
uv pip install browser-use
```

Download chromium using playwright's shortcut:

```bash
uvx playwright install chromium --with-deps --no-shell
```

Get your API key from [Browser Use Cloud](https://cloud.browser-use.com/dashboard/api) and add it to your `.env` file:

```bash
BROWSER_USE_API_KEY=your-key
```

Run your first agent:

```python
from browser_use import Agent, ChatBrowserUse

agent = Agent(
    task="Find the number of stars of the browser-use repo",
    llm=ChatBrowserUse(),
)
agent.run_sync()
```

Check out the [library docs](https://docs.browser-use.com) and [cloud docs](https://docs.cloud.browser-use.com) for more settings.


## Stealth Browser Infrastructure

Want to bypass Cloudflare, or any other anti-bot protection?

Simply go to [Browser Use Cloud](https://docs.cloud.browser-use.com) grab a `BROWSER_USE_API_KEY` and use the `use_cloud` parameter.

```python
from browser_use import Agent, Browser
from browser_use import ChatBrowserUse

# Use Browser-Use cloud browser service
browser = Browser(
    use_cloud=True,  # Automatically provisions a cloud browser
)

agent = Agent(
    task="Your task here",
    llm=ChatBrowserUse(),
    browser=browser,
)
```



# Demos

[Task](https://github.com/browser-use/browser-use/blob/main/examples/use-cases/shopping.py): Add grocery items to cart, and checkout.

[![AI Did My Groceries](https://github.com/user-attachments/assets/a0ffd23d-9a11-4368-8893-b092703abc14)](https://www.youtube.com/watch?v=L2Ya9PYNns8)

<br/><br/>


[Task](https://github.com/browser-use/browser-use/blob/main/examples/use-cases/find_and_apply_to_jobs.py): Read my CV & find ML jobs, save them to a file, and then start applying for them in new tabs, if you need help, ask me.

https://github.com/user-attachments/assets/171fb4d6-0355-46f2-863e-edb04a828d04

<br/><br/>

See [more examples](https://docs.browser-use.com/examples) and give us a star!


<br/><br/>
## MCP Integration

This gives Claude Desktop access to browser automation tools for web scraping, form filling, and more. See the [MCP docs](https://docs.browser-use.com/customize/mcp-server).
```json
{
  "mcpServers": {
    "browser-use": {
      "command": "uvx",
      "args": ["browser-use[cli]", "--mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

<div align="center">
  
**Tell your computer what to do, and it gets it done.**

<img src="https://github.com/user-attachments/assets/06fa3078-8461-4560-b434-445510c1766f" width="400"/>

[![Twitter Follow](https://img.shields.io/twitter/follow/Magnus?style=social)](https://x.com/intent/user?screen_name=mamagnus00)
[![Twitter Follow](https://img.shields.io/twitter/follow/Gregor?style=social)](https://x.com/intent/user?screen_name=gregpr07)

</div>

<div align="center">
Made with ❤️ in Zurich and San Francisco
 </div>

## Variables d'environnement ajoutées et priorités

Deux variables d'environnement ont été ajoutées dans ce fork pour améliorer la modularité et la configuration dynamique :

- `AZURE_AD_TOKEN_PROVIDER` : Provider de token Azure AD (authentification sans clé API, pour Azure OpenAI).
- `LLM_PROVIDER` : Permet de choisir dynamiquement le provider (`openai` ou `azure`).
- `AZURE_OPENAI_API_VERSION` : Permet de définir la version d'API utilisée pour Azure OpenAI (ex : `2025-04-01-preview`).
- `LLM_TEMPERATURE` : Température du modèle LLM. 

Les autres variables (`OPENAI_API_KEY`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `BROWSER_USE_LLM_MODEL`, etc.) existaient déjà dans la configuration officielle et sont simplement respectées/priorisées dans la logique du fork.

## Configuration simplifiée via variables d'environnement

Certaines variables d'environnement **surchargent toujours** les paramètres du fichier `config.json` (priorité : env > config.json). Cela permet une utilisation simplifiée : si vous n'avez pas besoin de personnaliser des paramètres avancés, il suffit de définir ces variables d'environnement pour faire tourner le MCP, sans avoir à créer ou éditer de fichier `config.json`.


**Variables d'environnement qui overrident la config.json :**

- `OPENAI_API_KEY` ou `AZURE_OPENAI_KEY` (clé API LLM)
- `BROWSER_USE_LLM_MODEL` (nom du modèle LLM)
- `AZURE_OPENAI_ENDPOINT` (endpoint Azure OpenAI)
- `AZURE_OPENAI_API_VERSION` (version API Azure)
- `LLM_PROVIDER` (provider LLM, ex: openai, azure)
- `AZURE_AD_TOKEN_PROVIDER` (provider token Azure AD)
- `LLM_TEMPERATURE` (température du modèle LLM)
- `BROWSER_USE_HEADLESS` (mode headless du navigateur)
- `BROWSER_USE_ALLOWED_DOMAINS` (domaines autorisés)
- `BROWSER_USE_PROXY_URL`, `BROWSER_USE_NO_PROXY`, `BROWSER_USE_PROXY_USERNAME`, `BROWSER_USE_PROXY_PASSWORD` (proxy)

**Cas d'usage simplifié :**

> Si vous ne souhaitez pas gérer de fichier `config.json`, il suffit de définir ces variables d'environnement (dans `.env` ou dans votre shell) : le serveur MCP utilisera automatiquement ces valeurs et ignorera celles du fichier de config pour ces paramètres.

Pour toute personnalisation avancée (autres paramètres du navigateur, de l'agent, etc.), éditez le fichier `config.json` généré automatiquement lors du premier lancement.

---

## Tool: retry_with_browser_use_agent

- La description de l'outil `retry_with_browser_use_agent` a été modifiée pour que le LLM l'appelle systématiquement dès qu'une tâche est un peu complexe ou comporte plusieurs étapes.

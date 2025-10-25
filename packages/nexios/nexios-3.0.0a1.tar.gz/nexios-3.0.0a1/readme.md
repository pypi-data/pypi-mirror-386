## `NEXIOS`

> warning ⚠️ **IMPORTANT NOTICE: v3 Branch is Experimental**
The `v3` branch contains experimental features and is **NOT yet stable** for production use. For stable releases, please use the `v2` branch or the latest stable release from PyPI.

- **v2 Branch**: [Switch to v2 branch](https://github.com/nexios-labs/nexios/tree/v2) for production-ready features


Breaking changes may occur in v3 until it reaches stable release. Use at your own risk!

<div align="left">

<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=4CAF50&center=true&width=435&lines=Nexios+ASGI+Framework;Fast%2C+Simple%2C+Flexible" alt="Typing SVG" /></a>

<p align="center">
    <img alt=Support height="350" src="https://nexios-docs.netlify.app/logo.png">
    </p>
    <h1 align="center">Nexios 3.0.0-alpha<br></h1>

   </a>
</p>

<!-- Badges Section -->
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/Downloads-10k/month-brightgreen" alt="Downloads">
  <img src="https://img.shields.io/badge/Contributions-Welcome-orange" alt="Contributions">
  <img src="https://img.shields.io/badge/Active Development-Yes-success" alt="Active Development">
</p>

<p align="center">
<a href="https://github.com/nexios-labs/Nexios?tab=followers"><img title="Followers" src="https://img.shields.io/github/followers/nexios-labs?label=Followers&style=social"></a>
<a href="https://github.com/nexios-labs/Nexios/stargazers/"><img title="Stars" src="https://img.shields.io/github/stars/nexios-labs/Nexios?&style=social"></a>
<a href="https://github.com/nexios-labs/Nexios/network/members"><img title="Fork" src="https://img.shields.io/github/forks/nexios-labs/Nexios?style=social"></a>
<a href="https://github.com/nexios-labs/Nexios/watchers"><img title="Watching" src="https://img.shields.io/github/watchers/nexios-labs/Nexios?label=Watching&style=social"></a>

</br>

<h2 align="center"> Star the repo if u like it🌟</h2>

Nexios is a high-performance Python web framework. Designed for speed, flexibility, and simplicity, Nexios delivers exceptional performance  while maintaining the simplicity and elegance of Python. It supports RESTful APIs, authentication, and integrates easily with any ORM. Built for modern web development, Nexios allows developers to quickly spin up scalable, modular apps with minimal boilerplate—ideal for startups, rapid prototyping, and custom backend solutions. 

---

## `Installation` 📦

**Requirements:**

- Python 3.9 or higher
- pip (Python package manager)

To install **Nexios**, you can use several methods depending on your environment and preferred package manager. Below are the instructions for different package managers:

### 1. **From `pip`** (Standard Python Package Manager)

```bash
# Ensure you have Python 3.9+
python --version

# Install Nexios
pip install nexios

# Or install with specific version
pip install nexios==3.0.0a1
```

## Features ✨

- [x] **Powerful Routing**
- [x] **Automatic OpenAPI Documentation**
- [x] **Session Management**
- [x] **File Router**
- [x] **Authentication**
- [x] **Event Listener for Signals**
- [x] **Middleware Support**
- [x] **Raw ASGI Middleware Support**
- [x] **Express-like Functionality**
- [x] **Pydantic Support**
- [x] **Dependency Injection**
- [x] **In-built Security (CORS, CSRF, SECURE HEADERS)**
- [x] **WebSocket Support**
- [x] **Custom Error Handling**
- [x] **Pagination**
- [x] **HTTP/2 Support**
- [x] **High-Performance Async Processing**


### Basic Example

```py
from nexios import NexiosApp
from nexios.http import Request, Response

app = NexiosApp()

@app.get("/")
async def basic(request: Request, response: Response):
    return {"message": "Hello, world!"}
    # return response.json({"message":"Hello, world!"}) ## This will work for more control


```

### Another Basic Example

```py
from nexios import NexiosApp, Depend
from nexios.http import Request, Response

app = NexiosApp()

async def get_user():
    return {"name": "John Doe"}


@app.get("/users")
async def get_user(request: Request, response: Response, user: Depend(get_user)):

    return {"user": user}
```

Visit http://localhost:4000/docs to view the Swagger API documentation.



## See the full docs

👉 <a href="https://nexios-docs.netlify.app">https://nexios-docs.netlify.app</a>

## Contributors:

<a href="https://github.com/nexios-labs/nexios/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=nexios-labs/nexios" />
</a>

---

> Nexios is currently in active development. The current version is not yet considered stable.We're working towards a stable 3.x.x release. Please be aware that breaking changes may occur in versions before 3.x.

## ☕ Donate to Support Nexios

Nexios is a passion project built to make backend development in Python faster, cleaner, and more developer-friendly. It's fully open-source and maintained with love, late nights, and lots of coffee.

If Nexios has helped you build something awesome, saved you time, or inspired your next project, consider supporting its continued development. Your donation helps cover hosting, documentation tools, and fuels new features and updates.

Every little bit counts — whether it's the cost of a coffee or more. Thank you for believing in the project!

👉 [**Buy Me a Coffee**](https://www.buymeacoffee.com/techwithdul) and support the future of Nexios.

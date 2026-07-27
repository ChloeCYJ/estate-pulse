$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force .\build | Out-Null
Remove-Item -LiteralPath .\build\commercial-ui.js, .\build\commercial-ui.css -Force -ErrorAction SilentlyContinue

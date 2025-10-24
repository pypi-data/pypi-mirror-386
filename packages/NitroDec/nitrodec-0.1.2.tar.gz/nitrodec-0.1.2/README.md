## NitroDec

**Letest Version:** 0.1.2  
**Developer:** [@Nactire](https://t.me/Nactire)  
**Git Repo:** [NitroExpose](https://github.com/yuvrajmodz/NitroDec)


## 🚀 Overview

**NitroDec** is an Advanced Decorator For **Starlette**,  
Supports **Sync** And **Async** Both def Functions.  


## ⚡ Key Features

• Easy To Use  
• Automatically Patch After import  
• Use NitroDec And Boost Your Coding Speed      
• Lightweight And Super Fast  


## 🎲 Supported HTTP Methods

- **GET**, **POST**, **PUT**
- **PATCH**, **DELETE**, **OPTIONS**
- **HEAD**, **TRACE**


## 🛠️ System Requirements

- Python **3.8+**  
- **Ubuntu** Or **Debian** Recommended


## 🌊 Module installation

```bash
pip install NitroDec --break-system-packages
```

## 🧭 Usage Examples

**Async Example**

```bash
from starlette.applications import Starlette
import NitroDec

app = Starlette()

@app.get("/")
async def home(request):
    return {"message": "Hello World"}
```  

**Sync Example**

```bash
import NitroDec
from starlette.applications import Starlette

app = Starlette()

@app.get("/sync")
def sync_route(request):
    return {"message": "This is a sync function, auto-wrapped by NitroDec"}
```

**Post Route With Data**

```bash
from starlette.requests import Request
from starlette.responses import JSONResponse
import NitroDec
from starlette.applications import Starlette

app = Starlette()

@app.post("/echo")
async def echo(request: Request):
    data = await request.json()
    return {"you_sent": data}
```

**Multiple Http Methods (Same Route)**

```bash
import NitroDec
from starlette.applications import Starlette
from starlette.requests import Request

app = Starlette()

@app.get("/multi")
@app.post("/multi")
async def multi_method(request: Request):
    return {"method_used": request.method}
```  


**Start Example Using Uvicorn**

```bash
# 𝘍𝘰𝘳 𝘢𝘱𝘱.𝘱𝘺 𝘞𝘪𝘵𝘩 𝘢𝘱𝘱 𝘝𝘢𝘳𝘪𝘢𝘣𝘭𝘦.
uvicorn app:app --reload
```
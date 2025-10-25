## DecoStar

**Letest Version:** 1.1  
**Developer:** [@Nactire](https://t.me/Nactire)  
**Git Repo:** [DecoStar](https://github.com/yuvrajmodz/DecoStar)


## 🚀 Overview

**DecoStar** is an Advanced Decorator For **Starlette**,  
Supports **Sync** And **Async** Both def Functions.  


## ⚡ Key Features

• Easy To Use  
• Auto **Execute** After import **“patch_starlette_app()”**  
• Use DecoStar And Boost Your Coding Speed      
• Lightweight And Super Fast  


## 🎲 Supported HTTP Methods

- **GET**, **POST**, **PUT**
- **PATCH**, **DELETE**, **OPTIONS**
- **HEAD**, **TRACE**


## 🛠️ System Requirements

- Python **3.8+**  


## 🌊 Module installation

```bash
pip install DecoStar --break-system-packages
```

## 🧭 Usage Examples

**Async Example**

```bash
from starlette.applications import Starlette
import DecoStar

app = Starlette()

@app.get("/")
async def home(request):
    return {"message": "Hello World"}
```  

**Sync Example**

```bash
import DecoStar
from starlette.applications import Starlette

app = Starlette()

@app.get("/sync")
def sync_route(request):
    return {"message": "This is a sync function, auto-wrapped by DecoStar"}
```

**Post Route With Data**

```bash
from starlette.requests import Request
from starlette.responses import JSONResponse
import DecoStar
from starlette.applications import Starlette

app = Starlette()

@app.post("/echo")
async def echo(request: Request):
    data = await request.json()
    return {"you_sent": data}
```

**Multiple Http Methods (Same Route)**

```bash
import DecoStar
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
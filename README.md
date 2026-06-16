<div align="center">
<h1> ✨ CORDE_FashionCoordinator </h1>

 [**🔥 25-2 Prometheus Team10**](https://prometheus-ai.net/)
   
 [**Minsuh Joo**](https://github.com/juminsuh) · [**Ahyeon Kim**](https://github.com/rlakdus) · [**Hannah Kim**](https://github.com/khnwave) · **Eunji Kim** (Designer)

</div>

<h2>Introduction</h2>

The fashion recommendation chatbot based on personal and TPO (Time, Place, Occasion). More detailed information is represented at the [presentation poster](./assets/pme10pannel.pdf). 

<h2>Setup & Run</h2>

1. Clone our repository.

```
git clone https://github.com/juminsuh/CORDE_FashionCoordinator.git
```

2. Create a virtual environment.

```
conda create -n corde python=3.10 -y
conda activate corde
```

3. Install

```
cd demo
pip install -r requirements.txt
```

4. Make a `.env` file at `./backend/` directory and set your `OPENAI_API_KEY` at `.env` file.

5. Open a terminal 1 and run the backend server.
   
```
cd demo/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

6. Open a terminal 2 and run the frontend.
   
```
conda activate corde
cd demo/frontend
python -m http.server 8080
```

7. Open a [browser](http://localhost:8080/home.html).

**🥳 You are ready to use our service!**

<h2>Key Function</h2>

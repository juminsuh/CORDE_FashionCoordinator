<div align="center">
<h1> ✨ CORDE_FashionCoordinator </h1>

 [**🔥 25-2 Prometheus Team10**](https://prometheus-ai.net/)
   
 [**Minsuh Joo**](https://github.com/juminsuh) · [**Ayeon Kim**](https://github.com/rlakdus) · [**Hannah Kim**](https://github.com/khnwave) · **Eunji Kim** (Designer)

</div>

<h2>Introduction</h2>

페르소나와 TPO 기반 개인 맞춤형 코디 추천 챗봇 시스템입니다. 더 자세한 정보는 [판넬](./assets/pme10pannel.pdf)을 통해 확인하실 수 있습니다. 


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

2. Install

```
cd demo
pip install -r requirements.txt
```

3. Make a .env file at ./backend/ directory and set your `OPENAI_API_KEY` at .env file.

4. Open a terminal 1 and run the backend server.
   
```
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

5. Open a terminal 2 and run the frontend.
   
```
cd frontend
python -m http.server 8080
```

6. Open a [browser](http://localhost:8080/home.html).

**🥳 You are ready to use our service!**

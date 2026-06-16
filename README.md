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

<h2>Key Features</h2>

1. We collected item image and metadata (e.g., `sub_category`, `texture`, `pattern`, `fit`, and .etc) from [musinsa](https://www.musinsa.com/main/musinsa/recommend?skip_bf=Y&gf=A) in order to reflect trend and diverse preference of users.

2. We defined 6 personas (3 for male and female respectively) based on survey, which resulted cacusal, formal, and street fashion categories. 

3. We constructed two databases which include style DB and TPO DB, using FAISS vectorstore. We embedded only necessary information `style_name` and `top + mood`, respectively.

4. Based on user's selected persona, TPO, and negatives (fit, pattern, and price), Lookie✨ recommends items sequentially (top -> outer -> bottom -> shoes -> bag: Full Codie! 👚).

5. We retrieved top-5 style-based items and TPO-based items and rerank them by prompting LLM. For overall harmonics between items, LLM rerank the retreived 10 items. If LLM determines style and TPO conflict, it reranks items, priotizing TPO. Otherwise, it reranks items with balanced weights. Finally, Lookie✨ returns top-3 items with friendly and interpretable recommendation reasons. 

6. User can give a feedback if the recommended results are unsatisfactory. User can change `sub_category`, `color`, and `texture` if they want.

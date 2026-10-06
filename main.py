from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

client = OpenAI()

def embed(texts):
    res = client.embeddings.create(model = "text-embedding-3-small", input=texts)
    return [item.embedding for item in res.data]

def cosine(a,b):
    dot = sum(x*y for x,y in zip(a,b))
    na = sum(x*x for x in a)**0.5
    nb = sum(x*x for x in b)**0.5
    return dot/(na*nb)

def main():
    text = open("doc.txt",encoding = "utf-8").read()
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    vectors = embed(chunks)
    question = input("Question :")
    q_vec = embed([question])[0]

    scores = [(cosine(q_vec,v),i) for i,v in enumerate(vectors)]

    scores.sort(reverse=True)

    top = [i for _, i in scores[:3]]
    context = "\n\n".join(f"[chunk {i}]\n{chunks[i]}" for i in top)

    prompt = f"""Sirf neeche diye context se jawab do.
    Har baat ke baad bracket mein chunk number likho, jaise [chunk 2].
    Agar context mein jawab nahi hai to bolo "Jawab document mein nahi mila".

    Context:
    {context}

    question: {question}"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    print("\nJawab:\n", res.choices[0].message.content)


if __name__ == "__main__":
    main()
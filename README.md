# NAChat – mi asistente personal con IA

Esto es NAChat, la IA que armé para mí (y que ahora cualquiera puede usar). La corrí con Groq porque es una locura lo rápido que responde, le metí búsqueda en internet de verdad, y puede leer PDFs o archivos de texto que le suba. También se acuerda de toda la conversación, cosa que al principio no funcionaba y tuve que arreglarlo a los golpes.

La hice porque quería algo que no dependiera de OpenAI ni me pidiera tarjeta de crédito, y que pudiera correr en mi máquina y después subirla a la nube. Al final quedó más decente de lo que pensaba.

## Qué hace esto

- Chateás normal, te responde al toque (gracias a Groq)
- Si le preguntás algo que necesita información actual, busca en internet solo – a veces hay que activarle el checkbox, pero ya medio aprendió a darse cuenta
- Le podés pasar un PDF o un .txt y la IA se aviva y te responde basado en eso
- Los enlaces que te da son de verdad, no esas redirecciones pedorras que te rompen después de dos clics
- Se acuerda de lo que hablaste antes, porque sino es como hablar con una ameba

## Cómo la usé para armarla

No soy programador experto, así que la hice con:

- Python + Streamlit (para que tuviera interfaz web)
- Groq (el modelo `llama-3.1-8b-instant`, que es gratis y rapidísimo)
- DuckDuckGo (para las búsquedas, aunque tuve que pelearme con la librería hasta que aprendí a sacarle los enlaces buenos)
- Lo de los PDFs lo resolví con PyPDF2

## Quién soy y por qué la hice

Me llamo Natanael Ferrer, estoy en Bogotá (Colombia), y la empecé el 10 de junio de 2026. Laburo en Pevaar Software Factory S.A.S., pero esto lo hice por mi cuenta para aprender más que otra cosa. Quería tener una IA personal que no me cobrara por cada pregunta, que supiera quién es su creador y que no se hiciera la misteriosa cuando le pedís un enlace a YouTube.

## Cómo correrla local (por si alguien quiere)

Si alguien más quiere probarla en su máquina (o yo la quiero volver a correr acá):

```bash
git clone https://github.com/nata1808/NAChat.git
cd NAChat
python -m venv venv
.\venv\Scripts\activate    # en Windows
pip install -r requirements.txt
streamlit run app.py

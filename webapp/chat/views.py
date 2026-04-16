import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from . import llm


def index(request):
    return render(request, "chat/index.html")


@csrf_exempt
@require_POST
def chat(request):
    data = json.loads(request.body)
    question = data.get("question", "").strip()
    mode = data.get("mode", "hybrid")

    if not question:
        return JsonResponse({"error": "Soru boş olamaz."}, status=400)

    answer = llm.query(question, mode=mode)
    return JsonResponse({"answer": answer})


@csrf_exempt
@require_POST
def chat_stream(request):
    data = json.loads(request.body)
    question = data.get("question", "").strip()
    mode = data.get("mode", "hybrid")

    if not question:
        return JsonResponse({"error": "Soru boş olamaz."}, status=400)

    def event_stream():
        answer = llm.query(question, mode=mode)
        # Yield answer in chunks to simulate streaming
        chunk_size = 20
        for i in range(0, len(answer), chunk_size):
            chunk = answer[i:i + chunk_size]
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

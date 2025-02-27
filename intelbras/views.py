from django.http import FileResponse
from django.shortcuts import render, redirect
from intelbras.intelbras import Intelbras

# Create your views here.
def homepage(request):
    return render (request, 'homepage.html', {})
    
def intelbras(request):
    if request.method == "GET":
        filename = request.GET.get('f')
        if filename:
            response = FileResponse(open(filename, 'rb'))
            return response

    if request.method == "POST":
        if 'worksheet' in request.FILES:
            uploaded_file = request.FILES['worksheet']
            intelbras = Intelbras('processado')
            output_file = intelbras.run(uploaded_file)
            return render(request, 'upload.html', {'file': output_file})
        else:
            return render(request, 'upload.html', {'error': 'Insira uma planilha para converter! '})
        
    return render(request, 'upload.html', {})
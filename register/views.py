import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from .models import Note, Category



@csrf_exempt
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"message": "Send POST request with username and password"})

    data = json.loads(request.body)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "Username and password required"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password)
    return JsonResponse({"message": "User registered successfully"})

@csrf_exempt
def login_user(request):
    if request.method != "POST":
        return JsonResponse({"message": "Send POST request with username and password"})

    data = json.loads(request.body)
    user = authenticate(
        username=data.get("username"),
        password=data.get("password")
    )

    if not user:
        return JsonResponse({"error": "Invalid credentials"}, status=400)

    login(request, user)
    return JsonResponse({"message": "Login successful"})


def logout_user(request):
    logout(request)
    return JsonResponse({"message": "Logged out successfully"})



@method_decorator(csrf_exempt, name='dispatch')
class CreateNoteView(LoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)

        note = Note.objects.create(
            title=data.get("title"),
            content=data.get("content"),
            user=request.user
        )

        return JsonResponse({"message": "Note created", "id": note.id}, status=201)
        
        
@method_decorator(csrf_exempt, name='dispatch')
class UpdateNoteView(LoginRequiredMixin, View):
    def put(self, request, pk):
        note = Note.objects.filter(id=pk, user=request.user).first()
        if not note:
            return JsonResponse({"error": "Note not found"}, status=404)

        data = json.loads(request.body)
        note.title = data.get("title", note.title)
        note.content = data.get("content", note.content)
        note.save()

        return JsonResponse({"message": "Note updated"})
    
    
@method_decorator(csrf_exempt, name='dispatch')
class DeleteNoteView(LoginRequiredMixin, View):
    def delete(self, request, pk):
        note = Note.objects.filter(id=pk, user=request.user).first()
        if not note:
            return JsonResponse({"error": "Note not found"}, status=404)

        note.delete()
        return JsonResponse({"message": "Note deleted"})

    

class ListNotesView(LoginRequiredMixin, View):
    def get(self, request):
        notes = [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "category": n.category.name if n.category else None,
                "is_favorite": n.is_favorite
            }
            for n in Note.objects.filter(user=request.user)
        ]
        return JsonResponse(notes, safe=False)

    

class ViewNoteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        note = Note.objects.filter(id=pk, user=request.user).first()
        if not note:
            return JsonResponse({"error": "Note not found"}, status=404)

        return JsonResponse({
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "category": note.category.name if note.category else None,
            "is_favorite": note.is_favorite
        })
    


@method_decorator(csrf_exempt, name='dispatch')
class CreateCategoryView(LoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)
        category = Category.objects.create(
            name=data.get("name"),
            user=request.user
        )
        return JsonResponse({"message": "Category created", "id": category.id})


@method_decorator(csrf_exempt, name='dispatch')
class AssignCategoryView(LoginRequiredMixin, View):
    def put(self, request, note_id):
        data = json.loads(request.body)

        note = Note.objects.filter(id=note_id, user=request.user).first()
        category = Category.objects.filter(
            id=data.get("category_id"),
            user=request.user
        ).first()

        if not note or not category:
            return JsonResponse({"error": "Invalid note or category"}, status=404)

        note.category = category
        note.save()

        return JsonResponse({"message": "Category assigned"})
    
    
class SearchNotesView(LoginRequiredMixin, View):
    def get(self, request):
        q = request.GET.get("q", "")
        notes = Note.objects.filter(
            user=request.user
        ).filter(Q(title__icontains=q) | Q(content__icontains=q) | Q(category__name__icontains=q))

        return JsonResponse(
            [{"id": n.id, "title": n.title, "category": n.category.name if n.category else None} for n in notes],
            safe=False
        )


@method_decorator(csrf_exempt, name='dispatch')
class ToggleFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        note = Note.objects.filter(id=pk, user=request.user).first()
        if not note:
            return JsonResponse({"error": "Note not found"}, status=404)

        note.is_favorite = not note.is_favorite
        note.save()

        return JsonResponse({"favorite": note.is_favorite})

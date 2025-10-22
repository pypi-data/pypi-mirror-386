from django.contrib import admin
from .models import Choice, Question
from django.urls import include, path

# admin.site.register(Question)


class QuestionAdmin(admin.ModelAdmin):
    fields = ["pub_date", "question_text"]
    list_display = ["question_text", "pub_date"] #To display the list display as individual fields. STEP1
    

# class ChoiceInline(admin.StackedInline):
#     model = Choice
#     extra = 3

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]
    list_display = ["question_text", "pub_date", "was_published_recently"] #To display the list display as individual fields. STEP2
    list_filter = ["pub_date"]
    search_fields = ["question_text"]


admin.site.register(Question, QuestionAdmin)
# admin.site.register(Choice)



urlpatterns = [
    path("polls/", include("polls.urls")),
    path("admin/", admin.site.urls),
]
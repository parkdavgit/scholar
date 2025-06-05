from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Candidate, Criteria, Score, Scholarship, Reviewer

admin.site.register(Candidate)
admin.site.register(Criteria)
admin.site.register(Score)
admin.site.register(Scholarship)
admin.site.register(Reviewer)
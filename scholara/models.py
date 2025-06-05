from django.db import models
from django.contrib.auth.models import User

class Scholarship(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Criteria(models.Model):
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    weight = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.scholarship.name} - {self.name}"
    
class Reviewer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    scholarships = models.ManyToManyField(Scholarship, related_name='reviewers')

    def __str__(self):
        return f"{self.name}"


class Candidate(models.Model):
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20)
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

class Score(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    criteria = models.ForeignKey(Criteria, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE)
    score = models.FloatField()

    class Meta:
        unique_together = ('candidate', 'criteria', 'reviewer')

    def __str__(self):
        return f"{self.candidate} ({self.reviewer})"

   
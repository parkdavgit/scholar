from django import forms
from .models import Score, Candidate, Criteria

class ScoreForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['candidate', 'criteria', 'score']  # reviewer는 view에서 직접 설정

    def __init__(self, *args, **kwargs):
        reviewer = kwargs.pop('reviewer', None)
        super().__init__(*args, **kwargs)

        if reviewer:
            scholarships = reviewer.scholarships.all()
            self.fields['candidate'].queryset = Candidate.objects.filter(scholarship__in=scholarships)
            self.fields['criteria'].queryset = Criteria.objects.filter(scholarship__in=scholarships)



          
class EditScoreForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['candidate','criteria', 'score']
        widgets = {
            'value': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        # reviewer 인자를 폼 초기화 시 받아옴
        reviewer = kwargs.pop('reviewer', None)
        super().__init__(*args, **kwargs)

        if reviewer:
            if self.instance:
                candidate = self.instance.candidate
                # Reviewer가 맡은 장학금 범위 내에 해당 후보의 카테고리가 있는지 확인
                if candidate.scholarship in reviewer.scholarships.all():
                    self.fields['criteria'].queryset = Criteria.objects.filter(scholarship=candidate.scholarship)
                else:
                    self.fields['criteria'].queryset = Criteria.objects.none()
            else:
                self.fields['criteria'].queryset = Criteria.objects.none()        
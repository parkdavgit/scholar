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
    candidate = forms.ModelChoiceField(queryset=Candidate.objects.none(), label="대상자")
    criteria = forms.ModelChoiceField(queryset=Criteria.objects.all(), label="선정 기준")

    class Meta:
        model = Score
        fields = ['candidate', 'criteria', 'score']

        def __str__(self):
            return f"{self.name}"






    def __init__(self, *args, **kwargs):
        reviewer = kwargs.pop('reviewer', None)
        super().__init__(*args, **kwargs)

        


        if reviewer:
            # 본인이 평가했던 후보자만 선택 가능
            candidates = Candidate.objects.filter(
                scholarship__in=reviewer.scholarships.all(),
                score__reviewer=reviewer
            ).distinct()
            self.fields['candidate'].queryset = candidates
            #self.fields['candidate'].disabled = True
            #self.fields['criteria'].disabled = True



    def __init__(self, *args, reviewer=None, instance=None, **kwargs):
            super().__init__(*args, instance=instance, **kwargs)

            if reviewer:
                # 리뷰어의 후보자만 보여주기 (선택사항)
                self.fields['candidate'].queryset = Candidate.objects.filter(scholarship=reviewer.scholarship)

            if instance:
                # 후보자의 카테고리에 맞는 기준만 보여주기
                candidate = instance.candidate
                self.fields['criteria'].queryset = Criteria.objects.filter(scholarship=candidate.scholarship)

            else:
                # 기본값으로는 기준을 모두 보여주되, 빈 쿼리셋으로도 가능
                self.fields['criteria'].queryset = Criteria.objects.none()            
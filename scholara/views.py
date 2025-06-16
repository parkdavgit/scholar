from django.shortcuts import render, get_object_or_404, redirect
from .forms import ScoreForm, EditScoreForm
import openpyxl
from django.http import HttpResponse
from .models import Scholarship, Candidate, Criteria, Reviewer, Score
from django.contrib.auth.decorators import login_required
#for error handling
from django.contrib import messages

def index(request):
    scholarship =Scholarship.objects.all()
     
    context = { 'scholarship': scholarship}
    return render(request, 'index.html', context)



def scholarship_detail(request, scholarship_id):
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    candidates = Candidate.objects.filter(scholarship=scholarship)
    criteria_list = Criteria.objects.filter(scholarship=scholarship)
    return render(request, 'reviewer_report.html', {
        'scholarship': scholarship,
        'criteria_list': criteria_list,
        'candidates': candidates
    })


@login_required(login_url='index')
def submit_score(request):
    #reviewer = get_object_or_404(Reviewer, user=request.user)
    # 이 경우 만일 request.user가 reviewer에 포함이 되지 않으면 page not found ERROR
    try:
        reviewer = Reviewer.objects.get(user=request.user)
    except Reviewer.DoesNotExist:
        messages.error(request, "선정위원으로 등록된 사용자만 점수를 입력할 수 있습니다.")
        #return redirect('index')  # 또는 로그인 후 이동할 페이지
        return render(request, 'permission_denied.html')
    # 이 경우 만일 request.user가 reviewer에 포함이 되지 않으면 안내 후 전 페이지로 


    if request.method == 'POST':
        form = ScoreForm(request.POST, reviewer=reviewer)
        if form.is_valid():
            score = form.save(commit=False)
            score.reviewer = reviewer
            # 보안 유효성 검사 (장학금 소속 확인)
            if score.candidate.scholarship not in reviewer.scholarships.all():
                return render(request, 'permission_denied.html')

             # ✅ 이미 입력된 점수가 있는지 확인
            candidate = form.cleaned_data['candidate']
            criteria = form.cleaned_data['criteria']
                    
            existing = Score.objects.filter(reviewer=reviewer, candidate=candidate, criteria=criteria).first()
            if existing:
                messages.warning(request, f"이 항목은 이미 점수를 입력하셨습니다. (점수: {existing.score})")
                return redirect('submit_score')




            score.save()

            return redirect('submit_score')
    else:
        form = ScoreForm(reviewer=reviewer)

    return render(request, 'submit_score.html', {'form': form})
# views.py (추가)




@login_required
def edit_score(request, score_id):
    reviewer = Reviewer.objects.filter(user=request.user).first()
    score_instance = get_object_or_404(Score, id=score_id, reviewer=reviewer)

    if request.method == 'POST':
        form = EditScoreForm(request.POST, instance=score_instance, reviewer=reviewer)
        if form.is_valid():
            form.save()
            messages.success(request, "점수가 수정되었습니다.")
            return redirect('my_scores')
    else:
        form = EditScoreForm(instance=score_instance, reviewer=reviewer)

    return render(request, 'edit_score.html', {'form': form})




@login_required(login_url='index')
def my_scores(request):
    reviewer = Reviewer.objects.filter(user=request.user).first()
    if not reviewer:
        return render(request, 'error.html', {'message': '선정위원만 접근할 수 있습니다.'})

    scores = Score.objects.filter(reviewer=reviewer).select_related('candidate', 'criteria').order_by('candidate__name')

    return render(request, 'my_scores.html', {'scores': scores})




def export_scores_excel(request, scholarship_id):
    scholarship = Scholarship.objects.get(id=scholarship_id)
    candidates = Candidate.objects.filter(scholarship=scholarship)
    criteria_list = Criteria.objects.filter(scholarship=scholarship)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Scores"

    criteria_list = list(Criteria.objects.all())
    ws.append(["학생명"] + [c.name for c in criteria_list] + ["총점"])

    for candidate in Candidate.objects.all():
        row = [candidate.name]
        total = 0
        for criteria in criteria_list:
            scores = Score.objects.filter(candidate=candidate, criteria=criteria)
            avg_score = sum(s.score for s in scores) / scores.count() if scores else 0
            row.append(round(avg_score, 2))
            total += avg_score
        row.append(round(total, 2))
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=scholarship_scores.xlsx'
    wb.save(response)
    return response


 
def scholarship_report(request, scholarship_id):
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    candidates = Candidate.objects.filter(scholarship=scholarship)
    criteria_list = Criteria.objects.filter(scholarship=scholarship)

    report_data = []

    for candidate in candidates:
        row = {
            'candidate': candidate,
            'scores': [],
            'total': 0
        }
        total_score = 0
        for criteria in criteria_list:
            scores = Score.objects.filter(candidate=candidate, criteria=criteria)
            avg_score = sum(s.score for s in scores) / scores.count() if scores else 0
            row['scores'].append(round(avg_score, 2))
            total_score += avg_score
        row['total'] = round(total_score, 2)
        report_data.append(row)

    return render(request, 'scholarship_report.html', {
        'scholarship': scholarship,
        'criteria_list': criteria_list,
        'report_data': report_data
    })


def reviewer_report(request, scholarship_id):
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    candidates = Candidate.objects.filter(scholarship=scholarship)
    criteria_list = Criteria.objects.filter(scholarship=scholarship)
    reviewers = scholarship.reviewers.all()

    report_data = []

    for reviewer in reviewers:
        rows = []
        for candidate in candidates:
            row = {
                'candidate': candidate,
                'scores': [],
                'total': 0
            }
            total = 0
            for criteria in criteria_list:
                try:
                    s = Score.objects.get(candidate=candidate, criteria=criteria, reviewer=reviewer)
                    score = s.score
                except Score.DoesNotExist:
                    score = None
                row['scores'].append(score)
                if score is not None:
                    total += score
            row['total'] = total
            rows.append(row)
        report_data.append({'reviewer': reviewer, 'rows': rows})

    return render(request, 'reviewer_report.html', {
        'scholarship': scholarship,
        'criteria_list': criteria_list,
        'report_data': report_data
    })

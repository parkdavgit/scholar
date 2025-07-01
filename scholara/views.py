from django.shortcuts import render, get_object_or_404, redirect
from .forms import ScoreForm, EditScoreForm
import openpyxl
from django.http import HttpResponse
from .models import Scholarship, Candidate, Criteria, Reviewer, Score
from django.contrib.auth.decorators import login_required
#for error handling
from django.contrib import messages
#for comment
from django.shortcuts import render, redirect
from .forms import ReviewCompletionForm
# for admin to check complete
from django.contrib.admin.views.decorators import staff_member_required
#for reviewer total
from django.db.models import Sum
from collections import defaultdict
#for excel 
from openpyxl import Workbook
from openpyxl.utils import get_column_letter


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
#@login_required
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

# ✅ 장학금 추출: reviewer가 평가하는 scholarship 중 첫 번째 사용
    scholarships = reviewer.scholarships.all()
    scholarship_name = scholarships[0].name if scholarships.exists() else '장학금 미지정'
    
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

    return render(request, 'submit_score.html', {'form': form,'scholarship_name': scholarship_name})
# views.py (추가)




@login_required(login_url='index')
def edit_score(request, score_id):
    reviewer = Reviewer.objects.filter(user=request.user).first()
    score_instance = get_object_or_404(Score, id=score_id, reviewer=reviewer)

    if reviewer.is_done:
        return render(request, 'thank_you.html')  # 이미 완료한 경우

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
    reviewer = Reviewer.objects.get(user=request.user)
    my_scores = Score.objects.filter(reviewer=reviewer).select_related('candidate', 'criteria')
    print ("my_scores.count")
    print (my_scores.count())
    # Reviewer가 맡은 장학금들
    assigned_scholarships = reviewer.scholarships.all()

    # 해당 장학금에 속한 후보자 수
    candidates = Candidate.objects.filter(scholarship__in=assigned_scholarships)
    criteria = Criteria.objects.filter(scholarship__in=assigned_scholarships)

    # 총 입력해야 할 수 = 후보자 수 × 기준 수
    total_required = candidates.count() * criteria.count()

    # 실제 입력한 점수 수 (Score 레코드 수)
    total_entered = my_scores.count()


    # 후보자별로 점수 목록 묶기
    grouped_scores = defaultdict(list)
    candidate_totals = {}

    for score in my_scores:
        grouped_scores[score.candidate].append(score)

    # 후보자별 총점 계산
    for candidate, scores in grouped_scores.items():
        total = sum(s.score for s in scores)
        candidate_totals[candidate.id] = total

    grouped_scores = dict(grouped_scores)

    # ✅ 장학금 추출: reviewer가 평가하는 scholarship 중 첫 번째 사용
    scholarships = reviewer.scholarships.all()
    scholarship_name = scholarships[0].name if scholarships.exists() else '장학금 미지정' 
    # 누락 알림
    scholarship = scholarships.first()
    criteria_count = Criteria.objects.filter(scholarship=scholarship).count() if scholarship else 0
   

    return render(request, 'my_scores.html', {
        'grouped_scores': grouped_scores,
        'candidate_totals': candidate_totals,
        'total_required': total_required,
        'total_entered': total_entered,
        'scholarship_name': scholarship_name,  # ✅ 템플릿에 넘기기
        'criteria_count': criteria_count, 
    })




def export_scholarship_scores(request, scholarship_id):
    scholarship = Scholarship.objects.get(id=scholarship_id)
    candidates = Candidate.objects.filter(scholarship=scholarship)
    reviewers = scholarship.reviewers.all()
    criteria = Criteria.objects.filter(scholarship=scholarship)

    # ✅ 점수 미리 캐싱 (딕셔너리로 접근)
    score_map = {}
    for score in Score.objects.filter(candidate__in=candidates, criteria__in=criteria, reviewer__in=reviewers):
        key = (score.candidate.id, score.reviewer.id, score.criteria.id)
        score_map[key] = score.score

    # ✅ 후보자별 총점 계산
    candidate_totals = {}
    for candidate in candidates:
        total = 0
        for reviewer in reviewers:
            for criterion in criteria:
                total += score_map.get((candidate.id, reviewer.id, criterion.id), 0)
        candidate_totals[candidate] = total

    sorted_candidates = sorted(candidate_totals.items(), key=lambda x: x[1], reverse=True)

    # ✅ Excel 만들기
    wb = Workbook()
    ws = wb.active
    ws.title = scholarship.name

    # ✅ 헤더
    headers = ['후보자']
    for reviewer in reviewers:
        for criterion in criteria:
            headers.append(f'{reviewer.name} - {criterion.name}')
    headers.append('총점')
    ws.append(headers)

    # ✅ 데이터 행
    for candidate, total in sorted_candidates:
        row = [candidate.name]
        for reviewer in reviewers:
            for criterion in criteria:
                score = score_map.get((candidate.id, reviewer.id, criterion.id), '')
                row.append(score)
        row.append(total)
        ws.append(row)

    # ✅ 응답 반환
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"{scholarship.name}_점수표.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
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

@login_required
def mark_review_complete(request):
    reviewer = Reviewer.objects.filter(user=request.user).first()

    if not reviewer:
        messages.error(request, "리뷰어 정보가 없습니다.")
        return redirect('home')

    if reviewer.is_done:
        return render(request, 'thank_you.html')  # 이미 완료한 경우

    if request.method == 'POST':
        form = ReviewCompletionForm(request.POST, instance=reviewer)
        if form.is_valid():
            reviewer = form.save(commit=False)
            reviewer.is_done = True
            reviewer.save()
            messages.success(request, "수고하셨습니다. 점수 입력이 완료되었습니다.")
            return render(request, 'thank_you.html')
    else:
        form = ReviewCompletionForm(instance=reviewer)

    return render(request, 'review_complete_form.html', {'form': form})

@staff_member_required
def admin_index(request):
    reviewers = Reviewer.objects.all()
    return render(request, 'admin_index.html', {'reviewers': reviewers})



@login_required(login_url='index')
def submit_score_ex(request):
    
    return render(request, 'sample.html')
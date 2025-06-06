from django.test import TestCase

# python manage.py runserver
# python manage.py makemigrations
# python manage.py migrate
# python manage.py createsuperuser
# PS ddkim projects Plan > mkdir templates
# PS ddkim projects Plan > mkdir static

#  <a href="{% url 'export_scores_excel' scholarship.id %}">엑셀로 내보내기</a>-->
# index에 장학금 종류 리스트하고 링클걸어 detail page 가게 하고 거기서 지원자 선정자 항목 점수 보이게 하기
# {% url 'show_category' scholar.pk %}

 <a href="{% url 'reviewer_score' scholarship.id %}" class="btn btn-primary float-left">점수보기</a>  


<td> <a href="{% url 'edit_score' %}" class="btn btn-secondary float-left">점수수정</a></td>

@login_required
def edit_score(request):
    reviewer = Reviewer.objects.filter(user=request.user).first()
    if not reviewer:
        messages.error(request, "선정위원만 접근할 수 있습니다.")
        return redirect('index')

    score_instance = None
    

    if request.method == 'POST':
        # 후보자와 기준 먼저 가져와서 기존 점수 찾기
        candidate_id = request.POST.get('candidate')
        criteria_id = request.POST.get('criteria')

        try:
            candidate = Candidate.objects.get(id=candidate_id)
            criteria = Criteria.objects.get(id=criteria_id)
            score_instance = Score.objects.get(candidate=candidate, reviewer=reviewer, criteria=criteria)
        except (Candidate.DoesNotExist, Criteria.DoesNotExist, Score.DoesNotExist):
            score_instance = None

        form = EditScoreForm(request.POST, instance=score_instance, reviewer=reviewer)

        if form.is_valid():
            form.save()
            messages.success(request, "점수가 성공적으로 수정되었습니다.")
            return redirect('edit_score')

    else:
        form = EditScoreForm(reviewer=reviewer)

    return render(request, 'edit_score.html', {
        'form': form,
        'score_instance': score_instance,
    }) 


    ##########################################################################
#nginx>scholar.conf

server {
    listen 80;
    server_name   ec2-3-140-240-73.us-east-2.compute.amazonaws.com;
    charset uft-8;
    client_max_body_size 128M;

    location / {
        uwsgi_pass unix:///tmp/scholar.sock;
        include uwsgi_params;
    }
}

#uwsgi>scholar.ini 
[uwsgi]

chdir = /srv/scholar/

module = scholar.wsgi:application

home = /home/ubuntu/myvenv/

uid = ubuntu

gid = ubuntu

socket = /tmp/scholar.sock

chmod-socket = 666

chown-socket = ubuntu:ubuntu



enable-threads = true

master = true

vacuum = true

pidfile = /tmp/scholar.pid

logto = /var/log/uwsgi/scholar/ @(exec://date +%%Y-%%m-%%d).log

log-reopen = true

#uwsgi>uwsgi.service
[Unit]

Description=uWSGI service

After=syslog.target

[Service]

ExecStart=/home/ubuntu/myvenv/bin/uwsgi -i /srv/scholar/.config/uwsgi/scholar.ini

Restart=always

KillSignal=SIGQUIT

Type=notify

StandardError=syslog

NotifyAccess=all

[Install]

WantedBy=multi-user.target






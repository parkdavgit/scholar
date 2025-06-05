from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth


# USER 를 IMPORT 해서 써서 따로 MODEL을 만들 필요가 없다

def register(request):

	if request.method == 'POST':

		first_name = request.POST[ 'first_name']
		last_name = request.POST[ 'last_name']
		username = request.POST[ 'username']
		password1 = request.POST[ 'password1']
		password2 = request.POST[ 'password2']
		email = request.POST[ 'email']

		user=User.objects.create_user(username=username, password=password1, email=email,first_name=first_name, last_name=last_name)
		user.save();
		#print('user created')
		return render(request, 'login.html') 

	else:
		return render(request, 'register.html')


def login(request):
	if request.method == 'POST':
		username = request.POST[ 'username']
		password = request.POST[ 'password']

		user = auth.authenticate(username=username,password=password)

		if user is not None:
			auth.login(request, user)
			return redirect("/")

		else:
			messages.info(request,'Invalid credential')
			return render(request, 'login.html');
		 

	else:
		return render(request, 'login.html');


def logout(request):
	auth.logout(request)
	return redirect("/")
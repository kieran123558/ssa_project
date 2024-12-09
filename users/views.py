from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserTopUp
from .models import Transcation


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created! You can now log in.")
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required(login_url='users:login')
def user(request):
    profile = request.user.profile
    transactions = Transcation.objects.all().filter(user=request.user).order_by('-created_at')
    return render(request, "users/user.html", {
        'user': request.user,
        'balance': profile.balance,
        'transactions': transactions,
    })

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', reverse("users:user"))
            return HttpResponseRedirect(next_url)
        else:
            messages.error(request, "Invalid Credentials.")
    return render(request, "users/login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('users:login')
import requests
from django.conf import settings

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        recaptcha_response = request.POST.get("recaptcha-token")  # Updated
        # Verify reCAPTCHA
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response,
            'remoteip': request.META.get('REMOTE_ADDR'),
        }
        recaptcha_verification = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data
        )
        result = recaptcha_verification.json()
        # Check reCAPTCHA response
        if not result.get("success"):
            messages.error(request, "reCAPTCHA validation failed. Please try again.")
            return redirect("users:login")  # Redirect back to the login page
        # Authenticate user if reCAPTCHA is valid
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the next URL if provided, else default to user profile
            next_url = request.GET.get('next', reverse("users:user"))  # Simplified fallback
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "users/login.html")

def user_view(request):
    profile = request.user.profile
    return render(request, 'users/user.html', {'balance': profile.balance})



def top_up(request):
    Profile = request.user.profile
    if request.method == 'POST':
        form = UserTopUp(request.POST) #takes the user to the form
        if form.is_valid(): #if its valid then it addes the amount
            amount = form.cleaned_data['amount']
            Profile.balance += amount
            Profile.save()
            Transcation.objects.create(user=request.user, amount=amount)#updates the transaction able history 
            messages.success(request, f"${amount} has been successfully added to your balance")
            return redirect('users:user')
    else:
        form = UserTopUp() #if the from isn't valid it reloads the from
    return render(request, 'users/topup.html', {'form': form, 'balance': Profile.balance})

from django.shortcuts import render, redirect
from django.db import connection
from django.template.loader import get_template
from .forms import RaceResultForm

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Query the database to check if the user exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s AND password_hash = %s", [email, password])
            user = cursor.fetchone()

        if user:
            # If user exists, redirect to the "Race Results" page
            request.session['user_id'] = user[0]
            return redirect('race_results')
        else:
            # If user doesn't exist, show an error message
            return render(request, 'app/login.html', {'error': 'Invalid email or password'})
        
    return render(request, 'app/login.html')

def race_results_view(request):
    # Check if user is logged in
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    # Get user's race results
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT result_id, athlete_id, event_id, weather_id, result, place 
            FROM raceresult
            WHERE athlete_id = %s
        """, [user_id])
        
        # Convert query results to a list of dictionaries
        columns = [col[0] for col in cursor.description]
        race_results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Get user's email for display
    user_email = request.session.get('user_email', 'User')
    
    return render(request, 'app/race_results.html', {
        'user_email': user_email,
        'race_results': race_results
    })

def add_race_result_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        form = RaceResultForm(request.POST)
        if form.is_valid():
            event_id = form.cleaned_data['event_id']
            weather_id = form.cleaned_data['weather_id']
            result = form.cleaned_data['result']
            place = form.cleaned_data['place']

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO raceresult (athlete_id, event_id, weather_id, result, place)
                    VALUES (%s, %s, %s, %s, %s)
                """, [user_id, event_id, weather_id, result, place])

            return redirect('race_results')
    else:
        form = RaceResultForm()

    return render(request, 'app/add_race_result.html', {'form': form})
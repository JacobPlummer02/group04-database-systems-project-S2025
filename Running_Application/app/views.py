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

def create_new_user_view(request):
    # Get all team id's and names
    with connection.cursor() as cursor:
        cursor.execute("SELECT team_id, team_name FROM team")
        teams = cursor.fetchall()  # (id, name)

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone')
        role = request.POST.get('role')
        role = role.title()
        team_id = request.POST.get('team_id')

        if password != confirm_password:
            return render(request, 'app/create_new_user.html', {'error': 'Passwords do not match'})

        # Check if user already exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", [email])
            user = cursor.fetchone()

        if user:
            # If user exists, show error message
            return render(request, 'app/create_new_user.html', {
                'error': 'User already exists',
                'teams': teams
            })
        else:
            # If user doesn't exist, create a new user
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (first_name, last_name, dob, gender, email, password_hash, phone, role, team_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [first_name, last_name, dob, gender, email, password, phone, role, team_id])
            return redirect('login')
    return render(request, 'app/create_new_user.html', {'teams': teams})

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
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT e.event_id, e.event_name, e.meet_id, m.meet_name " \
                        "FROM event as e JOIN meet as m " \
                        "ON e.meet_id = m.meet_id")
        events = cursor.fetchall() # (id, name, meet_id, meet_name)
        cursor.execute("SELECT weather_id, temp_f, wind_mph, conditions FROM weatherconditions")
        weather = cursor.fetchall() # (id, temp_f, wind_mph, conditions)

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
        form.fields['event_id'].choices = [
            (event[0], f"{event[1]} ({event[3]})") for event in events
        ]
        form.fields['weather_id'].choices = [
            (weather[0], f"{weather[1]}°F, {weather[2]} mph, {weather[3]}") for weather in weather
        ]

    return render(request, 'app/add_race_result.html', {
        'form': form,
        'events': events,
        'weather': weather
    })


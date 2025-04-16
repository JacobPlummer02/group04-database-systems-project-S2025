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
            request.session['user_first_name'] = user[1]
            request.session['user_last_name'] = user[2]
            request.session['user_gender'] = user[4]
            request.session['user_email'] = user[6]
            request.session['user_role'] = user[8]
            return redirect('dashboard')
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

def dashboard_view(request):
    user_id = request.session.get('user_id')
    team_id = request.session.get('team_id')
    if not user_id:
        return redirect('login')
    with connection.cursor() as cursor:
        cursor.execute("""
                    SELECT email, role
                    FROM users
                    WHERE user_id = %s
                """, [team_id])
    
    user_email = request.session.get('user_email')
    user_role = request.session.get('user_role')

    return render (request, 'app/dashboard.html', {
        'user_email': user_email,
        'user_role': user_role,
    })

def team_management_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    with connection.cursor() as cursor:
        # First, get the user's team_id
        cursor.execute("SELECT team_id FROM users WHERE user_id = %s", [user_id])
        team_result = cursor.fetchone()
        
        if not team_result:
            # Handle case where user doesn't exist
            return render(request, 'app/team_management.html', {
                'user_email': request.session.get('user_email'),
                'team_members': [],
                'error': 'User not found'
            })
        
        team_id = team_result[0]
        
        if not team_id:
            # Handle case where user doesn't have a team
            return render(request, 'app/team_management.html', {
                'user_email': request.session.get('user_email'),
                'team_members': [],
                'error': 'You are not assigned to a team'
            })
        
        # Now get all members of that team
        cursor.execute("""
            SELECT last_name, first_name, gender
            FROM users
            WHERE team_id = %s AND role = %s
        """, [team_id, 'Athlete'])
        
        columns = [col[0] for col in cursor.description]
        team_members = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render(request, 'app/team_management.html', {
        'user_email': request.session.get('user_email'),
        'team_members': team_members,
    })
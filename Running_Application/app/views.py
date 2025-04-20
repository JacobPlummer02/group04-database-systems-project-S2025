from django.shortcuts import render, redirect
from django.db import connection
from django.template.loader import get_template
from .forms import RaceResultForm
from .forms import TrainingLogForm
from datetime import datetime


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
    
    # Initialize filter variables
    event_filter = request.GET.get('event', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    
    query = """
        SELECT 
            e.event_name, 
            m.meet_date,
            r.result, 
            r.place
        FROM RaceResult r
        JOIN Event e ON r.event_id = e.event_id
        JOIN Meet m ON e.meet_id = m.meet_id
        WHERE r.athlete_id = %s
    """
    params = [user_id]

    
    if event_filter:
        query += " AND e.event_name LIKE %s"
        params.append(f"%{event_filter}%")  
    
    if start_date and end_date:
        #parse start and end date
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query += " AND m.meet_date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        except ValueError:
            # handle invalid format
            return render(request, 'app/race_results.html', {
                'error': 'Invalid date format. Please use YYYY-MM-DD.',
            })
    
   
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        
        # Convert query results to a list of dictionaries
        columns = [col[0] for col in cursor.description]
        race_results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    #get user's email for display
    user_email = request.session.get('user_email', 'User')
    
    return render(request, 'app/race_results.html', {
        'user_email': user_email,
        'race_results': race_results,
        'event_filter': event_filter,
        'start_date': start_date if start_date else '',
        'end_date': end_date if end_date else '',
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

    form = RaceResultForm(request.POST if request.method == 'POST' else None)
    form.fields['event_id'].choices = [
        (event[0], f"{event[1]} ({event[3]})") for event in events
    ]
    form.fields['weather_id'].choices = [
        (weather[0], f"{weather[1]}°F, {weather[2]} mph, {weather[3]}") for weather in weather
    ]

    if request.method == 'POST' and form.is_valid():
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

    return render(request, 'app/add_race_result.html', {
        'form': form,
        'events': events,
        'weather': weather
    })

def training_log_view(request):
    # ensure the user is logged in
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    # handle form submission
    if request.method == 'POST':
        form = TrainingLogForm(request.POST)
        if form.is_valid():
            date         = form.cleaned_data['date']
            workout_type = form.cleaned_data['workout_type']
            duration     = form.cleaned_data['duration'] or None
            distance     = form.cleaned_data['distance_miles']
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO traininglog
                      (athlete_id, date, workout_type, duration, distance_miles)
                    VALUES (%s, %s, %s, %s, %s)
                """, [user_id, date, workout_type, duration, distance])
            return redirect('training_log')
    else:
        form = TrainingLogForm()

    # fetch existing logs
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT log_id, date, workout_type, duration, distance_miles
            FROM traininglog
            WHERE athlete_id = %s
            ORDER BY date DESC
        """, [user_id])
        cols = [c[0] for c in cursor.description]
        logs = [dict(zip(cols, row)) for row in cursor.fetchall()]

    return render(request, 'app/training_log.html', {
        'form': form,
        'logs': logs,
    })

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

from django.shortcuts import render, redirect
from django.db import connection
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from .forms import RaceResultForm, PasswordChangeForm
from .forms import TrainingLogForm
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s AND password_hash = %s", [email, password])
            user = cursor.fetchone()

        if user:
            request.session['user_id'] = user[0]
            request.session['user_first_name'] = user[1]
            request.session['user_last_name'] = user[2]
            request.session['user_gender'] = user[4]
            request.session['user_email'] = user[6]
            request.session['user_role'] = user[8]
            return redirect('dashboard')
        else:
            return render(request, 'app/login.html', {'error': 'Invalid email or password'})
        
    return render(request, 'app/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def create_new_user_view(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT team_id, team_name FROM team")
        teams = cursor.fetchall()

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

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", [email])
            user = cursor.fetchone()

        if user:
            return render(request, 'app/create_new_user.html', {
                'error': 'User already exists',
                'teams': teams
            })
        else:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (first_name, last_name, dob, gender, email, password_hash, phone, role, team_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [first_name, last_name, dob, gender, email, password, phone, role, team_id])
            return redirect('login')
    return render(request, 'app/create_new_user.html', {'teams': teams})


def race_results_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    event_filter = request.GET.get('event', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    user_email = request.session.get('user_email')
    user_role = request.session.get('user_role')
    user_name = request.session.get('user_first_name')
    user_lname = request.session.get('user_last_name')

    query = """
        SELECT 
            e.event_name, 
            m.meet_date,
            r.result, 
            r.place,
            w.temp_f,
            w.wind_mph,
            w.conditions
        FROM RaceResult r
        JOIN Event e ON r.event_id = e.event_id
        JOIN Meet m ON e.meet_id = m.meet_id
        JOIN WeatherConditions w ON r.weather_id = w.weather_id
        WHERE r.athlete_id = %s
    """
    params = [user_id]

    if event_filter:
        query += " AND LOWER(e.event_name) LIKE LOWER(%s)"
        params.append(f"%{event_filter}%")

    if start_date and end_date:
        try:
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query += " AND m.meet_date BETWEEN %s AND %s"
            params.extend([start_date_dt, end_date_dt])
        except ValueError:
            return render(request, 'app/race_results.html', {
                'error': 'Invalid date format. Please use YYYY-MM-DD.',
            })

    query += " ORDER BY m.meet_date DESC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        race_results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    user_email = request.session.get('user_email', 'User')

    return render(request, 'app/race_results.html', {
        'user_email': user_email,
        'race_results': race_results,
        'event_filter': event_filter,
        'start_date': start_date,
        'end_date': end_date,
        'user_role': user_role,
        'user_name': user_name,
        'user_lname': user_lname,
    })

def add_race_result_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT e.event_id, e.event_name, e.meet_id, m.meet_name " \
                        "FROM event as e JOIN meet as m " \
                        "ON e.meet_id = m.meet_id")
        events = cursor.fetchall()
        cursor.execute("SELECT weather_id, temp_f, wind_mph, conditions FROM weatherconditions")
        weather = cursor.fetchall()

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
        'weather': weather,
        'user_role': request.session.get('user_role'),
        'user_name': request.session.get('user_first_name'),
        'user_lname': request.session.get('user_last_name'),
    })

def dashboard_view(request):
    user_id = request.session.get('user_id')
    team_id = request.session.get('team_id')
    if not user_id:
        return redirect('login')
    with connection.cursor() as cursor:
        cursor.execute("""
                    SELECT email, role, first_name, last_name
                    FROM users
                    WHERE user_id = %s
                """, [team_id])
    
    user_email = request.session.get('user_email')
    user_role = request.session.get('user_role')
    user_name = request.session.get('user_first_name')
    user_lname = request.session.get('user_last_name')

    return render (request, 'app/dashboard.html', {
        'user_email': user_email,
        'user_role': user_role,
        'user_name': user_name,
        'user_lname': user_lname,
    })

def team_management_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT team_id FROM users WHERE user_id = %s", [user_id])
        team_result = cursor.fetchone()
        
        if not team_result:
            return render(request, 'app/team_management.html', {
                'user_email': request.session.get('user_email'),
                'team_members': [],
                'error': 'User not found'
            })
        
        team_id = team_result[0]
        
        if not team_id:
            return render(request, 'app/team_management.html', {
                'user_email': request.session.get('user_email'),
                'team_members': [],
                'error': 'You are not assigned to a team'
            })
        
        cursor.execute("""
            SELECT last_name, first_name, gender
            FROM users
            WHERE team_id = %s AND role = %s
        """, [team_id, 'Athlete'])
        
        columns = [col[0] for col in cursor.description]
        team_members = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT team_name FROM team WHERE team_id = %s", [team_id])
        team_name = cursor.fetchone()
        if not team_name:
            return render(request, 'app/team_management.html', {
                'user_email': request.session.get('user_email'),
                'team_members': [],
                'error': 'Team not found'
            })
        team_name = team_name[0]
    
    return render(request, 'app/team_management.html', {
        'user_email': request.session.get('user_email'),
        'team_members': team_members,
        'user_role': request.session.get('user_role'),
        'user_name': request.session.get('user_first_name'),
        'user_lname': request.session.get('user_last_name'),
        'team_name': team_name
    })


def my_team_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("SELECT t.team_id, t.team_name, t.coach_id " \
                        "FROM users u JOIN team t ON u.team_id = t.team_id " \
                        "WHERE u.user_id = %s", [user_id])
        result = cursor.fetchone()

        if not result:
            return render(request, 'app/my_team.html', {
                'user_email': request.session.get('user_email'),
                'team_members': [],
                'team_name': 'Unknown Team',
                'error': 'User or team not found.'
            })

        team_id, team_name, coach_id = result

        cursor.execute("""
            SELECT first_name, last_name, email, phone, dob, gender
            FROM users
            WHERE team_id = %s AND role = %s
        """, [team_id, 'Athlete'])
        columns = [col[0] for col in cursor.description]
        team_members = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT first_name, last_name, email, phone
            FROM users
            WHERE user_id = %s
        """, [coach_id])
        coach = cursor.fetchone()
        coach_info = dict(zip(['first_name', 'last_name', 'email', 'phone'], coach)) if coach else None

    return render(request, 'app/my_team.html', {
        'user_email': request.session.get('user_email'),
        'team_members': team_members,
        'team_name': team_name,
        'coach_info': coach_info,
        'user_role': request.session.get('user_role'),
        'user_name': request.session.get('user_first_name'),
        'user_lname': request.session.get('user_last_name')
    })

def training_log_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        form = TrainingLogForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            workout_type = form.cleaned_data['workout_type']
            duration = form.cleaned_data['duration']
            distance = form.cleaned_data['distance_miles']

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO traininglog (athlete_id, date, workout_type, duration, distance_miles)
                    VALUES (%s, %s, %s, %s, %s)
                """, [user_id, date, workout_type, duration, distance])
            return redirect('training_log')
    else:
        form = TrainingLogForm()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT log_id, date, workout_type, duration, distance_miles
            FROM traininglog
            WHERE athlete_id = %s
            ORDER BY date DESC
        """, [user_id])
        columns = [col[0] for col in cursor.description]
        logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return render(request, 'app/training_log.html', {
        'form': form,
        'logs': logs,
        'user_role': request.session.get('user_role'),
        'user_name': request.session.get('user_first_name'),
        'user_lname': request.session.get('user_last_name')
    })

def meet_list_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM meet
        """)
        columns = [col[0] for col in cursor.description]
        meets = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return render(request, 'app/meet_list.html', {
        'meets': meets,
        'user_role': request.session.get('user_role'),
        'user_name': request.session.get('user_first_name'),
        'user_lname': request.session.get('user_last_name')
    })

def meet_details_view(request, meet_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT meet_name, meet_date, location, venue
            FROM meet
            WHERE meet_id = %s
        """, [meet_id])
        meet_info = cursor.fetchone()

        if not meet_info:
            return render(request, 'app/meet_detail.html', {
                'error': 'Meet not found'
            })

        meet_name, meet_date, location, venue = meet_info

        cursor.execute("""
            SELECT e.event_name, r.result, r.place, w.temp_f, w.wind_mph, w.conditions, u.first_name, u.last_name
            FROM event e
            JOIN raceresult r ON e.event_id = r.event_id
            JOIN weatherconditions w ON r.weather_id = w.weather_id
            JOIN users u ON r.athlete_id = u.user_id
            WHERE e.meet_id = %s
            ORDER BY e.event_name
        """, [meet_id])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        if not results:
            return render(request, 'app/meet_detail.html', {
                'error': 'No results found for this meet'
            })
    return render(request, 'app/meet_detail.html', {
        'meet_name': meet_name,
        'meet_date': meet_date,
        'location': location,
        'venue': venue,
        'results': results,
        'user_role': request.session.get('user_role'),
        'user_name': request.session.get('user_first_name'),
        'user_lname': request.session.get('user_last_name')
    })

def add_athlete_view(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if not user_id or user_role != 'Coach':
        return redirect('login')
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT team_id FROM users WHERE user_id = %s", [user_id])
        result = cursor.fetchone()
        if not result:
            return render(request, 'app/add_new_athlete.html', {'error': 'Team not found'})
        team_id = result[0]

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'app/add_new_athlete.html', {
                'error': 'Passwords do not match'
            })

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", [email])
            existing_user = cursor.fetchone()
            if existing_user:
                return render(request, 'app/add_new_athlete.html', {
                    'error': 'User with this email already exists'
                })

            cursor.execute("""
                INSERT INTO users (first_name, last_name, dob, gender, email, password_hash, phone, role, team_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Athlete', %s)
            """, [first_name, last_name, dob, gender, email, password, phone, team_id])
            
        return redirect('team_management')

    return render(request, 'app/add_new_athlete.html', {
        'user_role': request.session.get('user_role'),
        'user_name': request.session.get('user_first_name'),
        'user_lname': request.session.get('user_last_name')
    })


def manage_workouts_view(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    if not user_id or user_role != 'Coach':
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("SELECT team_id FROM users WHERE user_id = %s", [user_id])
        result = cursor.fetchone()
        if not result:
            return render(request, 'app/manage_workouts.html', {'error': 'Team not found'})
        team_id = result[0]

        cursor.execute("SELECT user_id, first_name, last_name FROM users WHERE team_id = %s AND role = 'Athlete'", [team_id])
        athletes = cursor.fetchall()

    if request.method == 'POST':
        athlete_id = request.POST.get('athlete_id')
        form = TrainingLogForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            workout_type = form.cleaned_data['workout_type']
            duration = form.cleaned_data['duration']
            distance = form.cleaned_data['distance_miles']

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO traininglog (athlete_id, date, workout_type, duration, distance_miles)
                    VALUES (%s, %s, %s, %s, %s)
                """, [athlete_id, date, workout_type, duration, distance])
            return redirect('manage_workouts')
    else:
        form = TrainingLogForm()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT t.athlete_id, u.first_name, u.last_name, t.log_id, t.date, t.workout_type, t.duration, t.distance_miles
            FROM traininglog t
            JOIN users u ON t.athlete_id = u.user_id
            WHERE u.team_id = %s
            ORDER BY t.date DESC
        """, [team_id])
        columns = [col[0] for col in cursor.description]
        workouts = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'app/manage_workouts.html', {
        'athletes': athletes,
        'workouts': workouts,
        'form': form,
        'user_role': user_role,
        'user_name': request.session.get('user_first_name'),
        'user_lname': request.session.get('user_last_name')
    })

def profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT first_name, last_name, email, role, dob
                       FROM users
                       WHERE user_id = %s
        """, [user_id])
        user_info = cursor.fetchone()
        if not user_info:
            return render(request, 'app/profile.html', {
                'error': 'User not found'
            })
        first_name, last_name, email, role, dob = user_info
        dob = dob.strftime('%Y-%m-%d') if dob else None

    return render(request, 'app/profile.html', {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'dob': dob,
        'role': role,
    })

def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            user_id = request.session.get('user_id')

            # Verify old password
            with connection.cursor() as cursor:
                cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", [user_id])
                row = cursor.fetchone()
                if not row or old_password != row[0]:
                    form.add_error('old_password', 'Incorrect old password.')
                    return render(request, 'app/change_password.html', {'form': form})

            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = %s 
                    WHERE user_id = %s
                """, [new_password, user_id])
            return redirect('profile')
    else:
        form = PasswordChangeForm()
    return render(request, 'app/change_password.html', {'form': form})
@csrf_exempt
def delete_athlete_view(request):
    if request.method == 'POST':
        if request.session.get('user_role') != 'Coach':
            return redirect('team_management') 
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        coach_id = request.session.get('user_id')
        with connection.cursor() as cursor:
            cursor.execute("SELECT team_id FROM users WHERE user_id = %s", [coach_id])
            team_result = cursor.fetchone()
            if team_result:
                team_id = team_result[0]
                cursor.execute("""
                    DELETE FROM users
                    WHERE first_name = %s AND last_name = %s AND team_id = %s AND role = 'Athlete'
                               """, [first_name, last_name, team_id])

        return redirect('team_management') 
    return redirect('team_management')

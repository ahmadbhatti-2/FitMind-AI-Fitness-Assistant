import { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Check, CircleAlert, Clock3, Dumbbell, LoaderCircle, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import useAuth from '../auth/useAuth';
import api, { apiEndpoints } from '../services/api';
import { exerciseImage, workoutImage } from '../services/visualAssets';

function requestError(error) {
  return error.response?.data?.detail || 'Something went wrong. Check your connection and try again.';
}

function fetchWorkoutData(userId) {
  return Promise.all([
    api.get(apiEndpoints.getWorkoutRec(userId)),
    api.get(apiEndpoints.getWorkoutHistory(userId)),
  ]);
}

export default function Workout() {
  const { user } = useAuth();
  const [workout, setWorkout] = useState(null);
  const [history, setHistory] = useState([]);
  const [performance, setPerformance] = useState({});
  const [sessionEffort, setSessionEffort] = useState('moderate');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadWorkout = useCallback(async () => {
    try {
      const [recommendation, log] = await fetchWorkoutData(user.user_id);
      setWorkout(recommendation.data);
      setPerformance({});
      setHistory(log.data);
    } catch (loadError) {
      setError(requestError(loadError));
    } finally {
      setLoading(false);
    }
  }, [user.user_id]);

  useEffect(() => {
    let active = true;
    fetchWorkoutData(user.user_id)
      .then(([recommendation, log]) => {
        if (!active) return;
        setWorkout(recommendation.data);
        setPerformance({});
        setHistory(log.data);
      })
      .catch((loadError) => {
        if (active) setError(requestError(loadError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [user.user_id]);

  const logWorkout = async (status) => {
    if (!workout || saving) return;
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const loggedPerformance = Object.fromEntries(
        Object.entries(performance)
          .map(([exerciseId, values]) => {
            const record = {};
            ['sets', 'reps', 'weight_kg'].forEach((field) => {
              const value = values[field];
              if (value !== '' && value !== undefined && value !== null) {
                record[field] = Number(value);
              }
            });
            if (values.effort) record.effort = values.effort;
            return [exerciseId, record];
          })
          .filter(([, record]) => Object.keys(record).length > 0),
      );
      await api.post(apiEndpoints.getWorkoutHistory(user.user_id), {
        template_id: workout.id,
        muscle_group: workout.muscle_groups?.join(', ') || 'full_body',
        status,
        difficulty_felt: sessionEffort,
        ...(status === 'completed' && Object.keys(loggedPerformance).length
          ? { performance: loggedPerformance }
          : {}),
      });
      setNotice(status === 'completed' ? 'Workout saved. Great work showing up.' : 'Rest day saved to your training history.');
      await loadWorkout();
    } catch (saveError) {
      setError(requestError(saveError));
    } finally {
      setSaving(false);
    }
  };

  const alreadyLoggedToday = history.some((entry) => entry.date === workout?.recommended_for);
  const sessionImage = workoutImage(workout);
  const refreshWorkout = () => {
    setLoading(true);
    setError('');
    loadWorkout();
  };

  if (loading) return <div className="loading-state"><LoaderCircle className="spin" /> Building your session from your profile…</div>;

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div><span className="eyebrow">TRAIN WITH PURPOSE</span><h1>Today's workout</h1><p>Exercises are filtered against your equipment, experience, and recorded injuries.</p></div>
        <button className="button button-outline" type="button" onClick={refreshWorkout} disabled={loading}><RefreshCw size={16} /> Refresh plan</button>
      </div>

      {error && <div className="inline-message inline-error" role="alert"><CircleAlert size={17} /> <span>{error}</span><button className="inline-retry" type="button" onClick={refreshWorkout}>Try again</button><Link to="/profile">Check your profile</Link></div>}
      {notice && <div className="inline-message inline-success" role="status"><Check size={17} /> {notice}</div>}

      {workout && (
        <>
          <section className="workout-hero">
            {sessionImage && <img className="workout-hero-image" src={sessionImage} alt={`${workout.title} session`} onError={(event) => { event.currentTarget.hidden = true; }} />}
            <div className="workout-hero-icon"><Dumbbell size={28} /></div>
            <div className="workout-hero-copy"><span className="status-pill"><span className="status-dot" /> PERSONALIZED SESSION</span><h2>{workout.title}</h2><p>{workout.reasons?.[0]}</p></div>
            <div className="workout-meta"><span><Clock3 size={17} /> {workout.duration_minutes} min</span><span><Dumbbell size={17} /> {workout.muscle_groups?.join(', ')}</span><span className="capitalize">{workout.difficulty}</span></div>
          </section>

          {workout.safety_note && <p className="safety-note"><CircleAlert size={15} /> {workout.safety_note} Stop if you feel pain and seek professional medical guidance for health concerns.</p>}

          <section className="content-card">
            <div className="content-card-heading"><div><span className="eyebrow">YOUR ROUTINE</span><h2>{workout.exercises?.length || 0} exercises</h2></div><label className="session-effort-control">Overall effort
              <select aria-label="Overall workout effort" value={sessionEffort} onChange={(event) => setSessionEffort(event.target.value)}>
                <option value="easy">Easy</option><option value="moderate">Moderate</option><option value="hard">Hard</option>
              </select>
            </label></div>
            {workout.exercises?.length ? (
              <div className="exercise-list">
                {workout.exercises.map((exercise, index) => (
                  <article className="exercise-row" key={exercise.id}>
                    <span className="exercise-number">{String(index + 1).padStart(2, '0')}</span>
                    {exerciseImage(exercise.name) && <img className="exercise-image" src={exerciseImage(exercise.name)} alt={exercise.name} loading="lazy" onError={(event) => { event.currentTarget.hidden = true; }} />}
                    <div className="exercise-main"><strong>{exercise.name}</strong><span>{exercise.description || 'Move with control and use a comfortable range of motion.'}</span></div>
                    <div className="exercise-prescription"><span><b>{exercise.sets || 3}</b> sets</span><span><b>{exercise.reps || '8–12'}</b> reps</span><span><b>{exercise.rest || '60 sec'}</b> rest</span></div>
                    <div className="performance-entry">
                      <label>Sets completed
                        <input
                          aria-label={`${exercise.name} sets completed`}
                          type="number"
                          min="1"
                          max="10"
                          value={performance[exercise.id]?.sets ?? exercise.sets ?? ''}
                          onChange={(event) => setPerformance((current) => ({
                            ...current,
                            [exercise.id]: { ...current[exercise.id], sets: event.target.value },
                          }))}
                        />
                      </label>
                      <label>Top reps
                        <input
                          aria-label={`${exercise.name} reps completed`}
                          type="number"
                          min="0"
                          max="100"
                          placeholder="Optional"
                          value={performance[exercise.id]?.reps ?? ''}
                          onChange={(event) => setPerformance((current) => ({
                            ...current,
                            [exercise.id]: { ...current[exercise.id], reps: event.target.value },
                          }))}
                        />
                      </label>
                      <label>Load (kg)
                        <input
                          aria-label={`${exercise.name} load in kilograms`}
                          type="number"
                          min="0"
                          step="0.5"
                          placeholder="Bodyweight/optional"
                          value={performance[exercise.id]?.weight_kg ?? exercise.weight_kg ?? ''}
                          onChange={(event) => setPerformance((current) => ({
                            ...current,
                            [exercise.id]: { ...current[exercise.id], weight_kg: event.target.value },
                          }))}
                        />
                      </label>
                      <label>Effort
                        <select
                          aria-label={`${exercise.name} effort`}
                          value={performance[exercise.id]?.effort ?? 'moderate'}
                          onChange={(event) => setPerformance((current) => ({
                            ...current,
                            [exercise.id]: { ...current[exercise.id], effort: event.target.value },
                          }))}
                        >
                          <option value="easy">Easy</option>
                          <option value="moderate">Moderate</option>
                          <option value="hard">Hard</option>
                        </select>
                      </label>
                      {exercise.progression && <span className="subtle-label">{exercise.progression}</span>}
                    </div>
                  </article>
                ))}
              </div>
            ) : workout.is_recovery_day
              ? <p className="empty-state">Today is a planned recovery day. Gentle movement is optional; prioritize rest and stop if anything hurts.</p>
              : <p className="empty-state">No exercises match your current profile. Add the equipment you have or update your training preferences.</p>}
          </section>

          {workout.weekly_schedule?.length > 0 && (
            <section className="content-card">
              <div className="content-card-heading"><div><span className="eyebrow">YOUR TRAINING WEEK</span><h2>Weekly schedule</h2></div><span className="subtle-label">Built around your selected training days</span></div>
              <div className="weekly-schedule">
                {workout.weekly_schedule.map((day) => (
                  <article className={`weekly-schedule-day ${day.day_index === workout.day_index ? 'is-today' : ''}`} key={day.day}>
                    <strong>{day.day}</strong>
                    <span>{day.title}</span>
                    <small>{day.is_rest_day ? 'Recovery' : `${day.exercises.length} exercises · ${day.muscle_groups.join(', ')}`}</small>
                  </article>
                ))}
              </div>
            </section>
          )}

          <div className="action-row">
            <button className="button button-primary" type="button" disabled={saving || alreadyLoggedToday} onClick={() => logWorkout(workout.is_recovery_day ? 'skipped' : 'completed')}>
              {saving ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />} {alreadyLoggedToday ? 'Today’s activity is logged' : workout.is_recovery_day ? 'Log recovery day' : 'Mark workout complete'}
            </button>
            {!workout.is_recovery_day && <button className="button button-outline" type="button" disabled={saving || alreadyLoggedToday} onClick={() => logWorkout('skipped')}>Log as rest day</button>}
            <Link className="text-link" to="/profile"><ArrowLeft size={15} /> Adjust profile</Link>
          </div>
        </>
      )}

      {!workout && !loading && !error && (
        <section className="workout-unavailable content-card">
          <span className="icon-tile icon-indigo"><Dumbbell size={21} /></span>
          <div><h2>Your session is waiting</h2><p>We couldn't build a workout from your current profile. Try again or review your training preferences.</p></div>
          <div className="action-row"><button className="button button-primary" type="button" onClick={refreshWorkout}><RefreshCw size={16} /> Try again</button><Link className="button button-outline" to="/profile">Review profile</Link></div>
        </section>
      )}

      <section className="content-card">
        <div className="content-card-heading"><div><span className="eyebrow">RECENT SESSIONS</span><h2>Your training log</h2></div></div>
        {history.length ? history.slice(0, 5).map((entry, index) => (
          <div className="history-row" key={`${entry.date}-${entry.template_id}-${index}`}><span className="history-date">{entry.date}</span><strong>{entry.template_id?.replaceAll('_', ' ') || 'Workout'}</strong><span className={`history-status ${entry.status === 'completed' ? 'is-complete' : ''}`}>{entry.status}</span></div>
        )) : <p className="empty-state">Your completed workouts and rest days will appear here.</p>}
      </section>
    </div>
  );
}

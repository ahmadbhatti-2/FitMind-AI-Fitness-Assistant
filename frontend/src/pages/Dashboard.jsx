import { useCallback, useEffect, useState } from 'react';
import { ArrowUpRight, CalendarDays, CheckCircle2, CircleAlert, Clock3, Dumbbell, Flame, LoaderCircle, RefreshCw, Salad, Scale, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import useAuth from '../auth/useAuth';
import api, { apiEndpoints } from '../services/api';
import { mealImage, workoutImage } from '../services/visualAssets';

function messageFrom(error) {
  return error.response?.data?.detail || 'Unable to load this recommendation. Check your connection and try again.';
}

function dashboardStateFrom(results) {
  const nextData = {};
  const nextErrors = {};
  ['workout', 'meal', 'progress', 'profile', 'history'].forEach((key, index) => {
    if (results[index].status === 'fulfilled') {
      nextData[key] = results[index].value.data;
    } else {
      nextErrors[key] = messageFrom(results[index].reason);
    }
  });
  return { data: nextData, errors: nextErrors };
}

function Recommendation({ kind, item, error, loading, onRetry }) {
  const isWorkout = kind === 'workout';
  const Icon = isWorkout ? Dumbbell : Salad;
  const title = item?.title || item?.meal_name;
  const image = isWorkout ? workoutImage(item) : mealImage(item);
  const target = isWorkout ? '/workouts' : '/nutrition';
  const details = isWorkout
    ? [
      item?.duration_minutes ? `${item.duration_minutes} min` : null,
      item?.exercises ? `${item.exercises.length} exercises` : null,
      item?.muscle_groups?.length ? item.muscle_groups.join(', ') : null,
    ].filter(Boolean)
    : [
      item?.calories_est ? `${item.calories_est} kcal` : null,
      item?.is_high_protein ? 'Protein-rich option' : null,
    ].filter(Boolean);
  const ingredients = item?.ingredients?.slice(0, 3).map((ingredient) => ingredient.replaceAll('_', ' ')).join(' · ');

  return (
    <article className={`recommendation-card ${isWorkout ? 'recommendation-workout' : 'recommendation-meal'}`} aria-busy={loading}>
      {image && <div className="recommendation-visual">
        <img src={image} alt={isWorkout ? `${title} training session` : title} loading="lazy" onError={(event) => { event.currentTarget.closest('.recommendation-visual').hidden = true; }} />
        <span>{title}</span>
      </div>}
      <div className="recommendation-topline">
        <span className={`icon-tile ${isWorkout ? 'icon-indigo' : 'icon-emerald'}`}><Icon size={21} /></span>
        <span className="status-pill"><span className="status-dot" /> TODAY'S {isWorkout ? 'WORKOUT' : 'MEAL'}</span>
      </div>
      {loading ? (
        <div className="recommendation-loading" role="status"><LoaderCircle className="spin" size={18} /> Loading recommendation…</div>
      ) : error ? (
        <div className="recommendation-failure" role="alert">
          <h2>Unable to load today's {isWorkout ? 'workout' : 'meal'} recommendation.</h2>
          <p>{error}</p>
          <button className="button button-outline" type="button" onClick={onRetry}><RefreshCw size={15} /> Try again</button>
        </div>
      ) : item ? (
        <>
          <h2>{title || (isWorkout ? 'Your training plan' : 'Your meal idea')}</h2>
          {details.length > 0 && <div className="recommendation-facts">{details.map((detail) => <span key={detail}>{isWorkout && detail.includes('min') ? <Clock3 size={14} /> : null}{detail}</span>)}</div>}
          {!isWorkout && ingredients && <p className="recommendation-summary">{ingredients}</p>}
          <p className="why-note"><Sparkles size={15} /> {item.reasons?.[0] || 'Matched to your saved profile and preferences.'}</p>
          <Link className="button button-primary" to={target}>
            {isWorkout ? 'View & start workout' : 'Explore this meal'} <ArrowUpRight size={17} />
          </Link>
        </>
      ) : (
        <div className="recommendation-failure">
          <h2>No recommendation available yet.</h2>
          <p>Complete your profile so FitMind can find a plan that fits you.</p>
          <Link className="button button-outline" to="/profile">Review your profile <ArrowUpRight size={16} /></Link>
        </div>
      )}
    </article>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState({ workout: null, meal: null, progress: null, profile: null, history: null });
  const [errors, setErrors] = useState({ workout: '', meal: '', progress: '', profile: '', history: '' });
  const [loading, setLoading] = useState(true);

  const requestDashboard = useCallback(() => Promise.allSettled([
      api.get(apiEndpoints.getWorkoutRec(user.user_id)),
      api.get(apiEndpoints.getMealRec(user.user_id, 'lunch')),
      api.get(apiEndpoints.getUserProgress(user.user_id)),
      api.get(apiEndpoints.getUserProfile(user.user_id)),
      api.get(apiEndpoints.getWorkoutHistory(user.user_id)),
    ]), [user.user_id]);

  useEffect(() => {
    let active = true;
    requestDashboard()
      .then((results) => {
        if (!active) return;
        const next = dashboardStateFrom(results);
        setData((previous) => ({ ...previous, ...next.data }));
        setErrors(next.errors);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [requestDashboard]);

  const refreshDashboard = async () => {
    setLoading(true);
    const results = await requestDashboard();
    const next = dashboardStateFrom(results);
    setData((previous) => ({ ...previous, ...next.data }));
    setErrors(next.errors);
    setLoading(false);
  };

  const latestWeight = data.progress?.weight_history?.at(-1)?.weight ?? data.profile?.weight;
  const hasHistory = Array.isArray(data.history) && data.history.length > 0;

  return (
    <div className="page-stack">
      <section className="welcome-banner">
        <div>
          <span className="eyebrow eyebrow-light">YOUR PERSONAL FITNESS SPACE</span>
          <h1>Small steps. Stronger you, {user.username.split(' ')[0]}.</h1>
          <p>Your plan is based on the goals, preferences, and training history saved to your profile.</p>
          <div className="welcome-date"><CalendarDays size={16} /> Your plan, refreshed from your latest activity</div>
        </div>
        <div className="welcome-art" aria-hidden="true"><Sparkles size={34} /></div>
      </section>

      {errors.profile && (
        <div className="inline-message inline-warning"><CircleAlert size={17} /> {errors.profile} <Link to="/profile">Review profile</Link></div>
      )}

      <section>
        <div className="section-heading">
          <div><span className="eyebrow">TODAY, MADE PERSONAL</span><h2>Today's recommendations</h2></div>
          <button className="button button-outline dashboard-refresh" type="button" onClick={refreshDashboard} disabled={loading}>
            {loading ? <LoaderCircle className="spin" size={15} /> : <RefreshCw size={15} />}
            {loading ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
        <div className="recommendation-grid">
          <Recommendation kind="workout" item={data.workout} error={errors.workout} loading={loading} onRetry={refreshDashboard} />
          <Recommendation kind="meal" item={data.meal} error={errors.meal} loading={loading} onRetry={refreshDashboard} />
        </div>
      </section>

      <section>
        <div className="section-heading"><div><span className="eyebrow">YOUR ACTIVITY</span><h2>Progress that adds up</h2></div><Link className="text-link" to="/progress">See progress <ArrowUpRight size={16} /></Link></div>
        <div className="stat-grid">
          <article className="stat-card"><span className="stat-icon icon-indigo"><Scale size={20} /></span><span className="stat-label">Latest weight</span><strong>{latestWeight ? `${latestWeight} kg` : 'Not logged'}</strong></article>
          <article className="stat-card"><span className="stat-icon icon-orange"><Flame size={20} /></span><span className="stat-label">Training streak</span><strong>{data.progress?.current_streak ?? '—'} <small>weeks</small></strong></article>
          <article className="stat-card"><span className="stat-icon icon-emerald"><CheckCircle2 size={20} /></span><span className="stat-label">Completed sessions</span><strong>{data.progress?.total_workouts_completed ?? '—'}</strong></article>
        </div>
        {!loading && !errors.history && !hasHistory && (
          <div className="history-empty-state">
            <span className="icon-tile icon-indigo"><Dumbbell size={19} /></span>
            <div><strong>No workout history yet.</strong><p>Complete your first workout to start tracking progress.</p></div>
            <Link className="text-link" to="/workouts">Find a workout <ArrowUpRight size={15} /></Link>
          </div>
        )}
        {!loading && errors.history && <div className="inline-message inline-warning" role="status"><CircleAlert size={16} /> Unable to load your workout history. <button className="inline-retry" type="button" onClick={refreshDashboard}>Try again</button></div>}
      </section>
    </div>
  );
}

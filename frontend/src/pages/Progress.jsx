import { useEffect, useState } from 'react';
import { Activity, Award, CalendarDays, CircleAlert, LoaderCircle, Plus, Scale, TrendingUp } from 'lucide-react';
import useAuth from '../auth/useAuth';
import api, { apiEndpoints } from '../services/api';

function errorMessage(error) {
  return error.response?.data?.detail || 'Progress data is temporarily unavailable.';
}

function fetchProgressData(userId) {
  return Promise.allSettled([
    api.get(apiEndpoints.getUserProgress(userId)),
    api.get(apiEndpoints.getUserProfile(userId)),
  ]);
}

export default function Progress() {
  const { user } = useAuth();
  const [progress, setProgress] = useState(null);
  const [profile, setProfile] = useState(null);
  const [weight, setWeight] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let active = true;
    fetchProgressData(user.user_id).then((results) => {
      if (!active) return;
      if (results[0].status === 'fulfilled') setProgress(results[0].value.data);
      else setError(errorMessage(results[0].reason));
      if (results[1].status === 'fulfilled') setProfile(results[1].value.data);
      setLoading(false);
    });
    return () => { active = false; };
  }, [user.user_id]);

  const saveWeight = async (event) => {
    event.preventDefault();
    const value = Number(weight);
    if (!Number.isFinite(value) || value < 25 || value > 350) {
      setError('Enter a body weight between 25 and 350 kg.');
      return;
    }
    setSaving(true);
    setError('');
    setNotice('');
    try {
      await api.post(apiEndpoints.updateProgress(user.user_id), { metric_type: 'body_weight', value });
      setWeight('');
      setNotice('Weight entry saved to your progress history.');
      const results = await fetchProgressData(user.user_id);
      if (results[0].status === 'fulfilled') setProgress(results[0].value.data);
      if (results[1].status === 'fulfilled') setProfile(results[1].value.data);
    } catch (saveError) {
      setError(errorMessage(saveError));
    } finally {
      setSaving(false);
    }
  };

  const history = progress?.weight_history || [];
  const latestWeight = history.at(-1)?.weight ?? profile?.weight;
  const chartValues = history.slice(-8);
  const maxWeight = Math.max(...chartValues.map((entry) => Number(entry.weight) || 0), 1);

  if (loading) return <div className="loading-state"><LoaderCircle className="spin" /> Loading your progress…</div>;

  return (
    <div className="page-stack">
      <div className="page-title-row"><div><span className="eyebrow">CONSISTENCY OVER PERFECTION</span><h1>Your progress</h1><p>Track training activity and body-weight entries saved to your account.</p></div></div>
      {error && <div className="inline-message inline-error" role="alert"><CircleAlert size={17} /> {error}</div>}
      {notice && <div className="inline-message inline-success" role="status"><Activity size={17} /> {notice}</div>}

      <section className="stat-grid">
        <article className="stat-card"><span className="stat-icon icon-indigo"><Scale size={20} /></span><span className="stat-label">Latest weight</span><strong>{latestWeight ? `${latestWeight} kg` : 'Not logged'}</strong></article>
        <article className="stat-card"><span className="stat-icon icon-orange"><CalendarDays size={20} /></span><span className="stat-label">Training streak</span><strong>{progress?.current_streak ?? 0} <small>weeks</small></strong></article>
        <article className="stat-card"><span className="stat-icon icon-emerald"><Award size={20} /></span><span className="stat-label">30-day consistency</span><strong>{progress?.consistency_percentage ?? 0}<small>%</small></strong></article>
        <article className="stat-card"><span className="stat-icon icon-blue"><TrendingUp size={20} /></span><span className="stat-label">Sessions completed</span><strong>{progress?.total_workouts_completed ?? 0}</strong></article>
      </section>

      <div className="progress-grid">
        <section className="content-card">
          <div className="content-card-heading"><div><span className="eyebrow">BODY WEIGHT</span><h2>Log a measurement</h2></div><Scale size={19} className="muted-icon" /></div>
          <p className="section-copy">A single entry is just a data point. Focus on longer-term patterns, not day-to-day changes.</p>
          <form className="weight-form" onSubmit={saveWeight}>
            <label className="field-label" htmlFor="weight-entry">Weight in kilograms</label>
            <div className="weight-input-row"><input id="weight-entry" type="number" min="25" max="350" step="0.1" value={weight} onChange={(event) => setWeight(event.target.value)} placeholder="e.g. 72.5" required /><button className="button button-primary" type="submit" disabled={saving}>{saving ? <LoaderCircle className="spin" size={17} /> : <Plus size={17} />} Save entry</button></div>
          </form>
          {chartValues.length > 1 && (
            <div className="weight-chart" role="img" aria-label="Recent body weight measurements">
              {chartValues.map((entry, index) => <div className="chart-column" key={`${entry.date}-${index}`}><span className="chart-value">{entry.weight}</span><span className="chart-bar" style={{ height: `${Math.max(8, (entry.weight / maxWeight) * 100)}%` }} /><span className="chart-label">{entry.date.slice(5)}</span></div>)}
            </div>
          )}
        </section>

        <section className="content-card">
          <div className="content-card-heading"><div><span className="eyebrow">TRAINING TARGET</span><h2>Build your rhythm</h2></div><Activity size={19} className="muted-icon" /></div>
          <p className="section-copy">You set a goal of <strong>{profile?.training_days ?? 3} training days per week</strong>. Completed workouts and rest days are recorded from your workout plan.</p>
          <div className="consistency-track"><span style={{ width: `${Math.min(progress?.consistency_percentage ?? 0, 100)}%` }} /></div>
          <p className="subtle-label">{progress?.consistency_percentage ?? 0}% of expected sessions logged in the past 30 days</p>
        </section>
      </div>

      <section className="content-card">
        <div className="content-card-heading"><div><span className="eyebrow">MEASUREMENTS</span><h2>Weight history</h2></div></div>
        {history.length ? (
          <div className="table-scroll"><table className="data-table"><thead><tr><th>Date</th><th className="align-right">Weight</th></tr></thead><tbody>{[...history].reverse().map((entry, index) => <tr key={`${entry.date}-${index}`}><td>{entry.date}</td><td className="align-right"><strong>{entry.weight} kg</strong></td></tr>)}</tbody></table></div>
        ) : <p className="empty-state">No measurements have been logged yet. Add your first entry above.</p>}
      </section>
    </div>
  );
}

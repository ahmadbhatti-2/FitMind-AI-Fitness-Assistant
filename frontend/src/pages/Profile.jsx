import { useEffect, useState } from 'react';
import { AlertTriangle, Check, CircleAlert, LoaderCircle, Save, ShieldCheck, UserRound } from 'lucide-react';
import useAuth from '../auth/useAuth';
import api, { apiEndpoints } from '../services/api';

const EMPTY_PROFILE = {
  age: '', gender: '', height: '', weight: '',
  goal: 'general_fitness', experience: 'beginner', training_days: 3,
  equipment: ['bodyweight'], diet_preference: 'omnivore',
  allergies: [], restrictions: [], injuries: [],
};

const LIST_FIELDS = [
  { name: 'equipment', label: 'Equipment you can use', placeholder: 'bodyweight, dumbbells, bench' },
  { name: 'allergies', label: 'Food allergies', placeholder: 'peanuts, milk, eggs' },
  { name: 'restrictions', label: 'Ingredients to avoid', placeholder: 'gluten, milk, soy' },
  { name: 'injuries', label: 'Injuries or movement limitations', placeholder: 'knee severe pain, shoulder mild discomfort' },
];

function errorMessage(error) {
  return error.response?.data?.detail || 'Your profile could not be saved. Please try again.';
}

function fetchProfile(userId) {
  return api.get(apiEndpoints.getUserProfile(userId));
}

function profileListValue(name, value) {
  if (!Array.isArray(value)) return value || '';
  return value.map((item) => {
    if (name !== 'injuries' || !item || typeof item !== 'object') return item;
    return [item.name, item.severity, item.context].filter(Boolean).join(' ');
  }).join(', ');
}

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(EMPTY_PROFILE);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let active = true;
    fetchProfile(user.user_id)
      .then(({ data }) => {
        if (active) setProfile({ ...EMPTY_PROFILE, ...data });
      })
      .catch((loadError) => {
        if (active) setError(errorMessage(loadError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [user.user_id]);

  const update = (event) => {
    const { name, value } = event.target;
    setSaved(false);
    setProfile((current) => ({ ...current, [name]: value }));
  };

  const saveProfile = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSaved(false);
    const payload = { ...profile };
    ['age', 'height', 'weight', 'training_days'].forEach((field) => {
      payload[field] = payload[field] === '' ? null : Number(payload[field]);
    });
    LIST_FIELDS.forEach(({ name }) => {
      const value = payload[name];
      payload[name] = (Array.isArray(value) ? value : String(value || '').split(','))
        .map((item) => {
          if (name === 'injuries' && item && typeof item === 'object') {
            return {
              name: String(item.name || '').trim().toLowerCase(),
              severity: item.severity || 'moderate',
              context: String(item.context || '').trim(),
            };
          }
          return String(item).trim().toLowerCase();
        })
        .filter((item) => (typeof item === 'string' ? item : item.name));
    });
    try {
      await api.put(apiEndpoints.updateUserProfile(user.user_id), payload);
      setProfile(payload);
      setSaved(true);
    } catch (saveError) {
      setError(errorMessage(saveError));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading-state"><LoaderCircle className="spin" /> Loading your fitness profile…</div>;

  return (
    <div className="page-stack page-narrow">
      <div className="page-title-row">
        <div><span className="eyebrow">YOUR PLAN STARTS HERE</span><h1>Fitness profile</h1><p>Honest details help FitMind make more useful, safer suggestions.</p></div>
        <div className="profile-avatar"><UserRound size={22} /></div>
      </div>
      {error && <div className="inline-message inline-error" role="alert"><CircleAlert size={17} /> {error}</div>}
      {saved && <div className="inline-message inline-success" role="status"><Check size={17} /> Profile saved. Your next recommendations will use these updates.</div>}

      <form className="page-stack" onSubmit={saveProfile}>
        <section className="content-card form-section">
          <div className="content-card-heading"><div><span className="eyebrow">ABOUT YOU</span><h2>Basics</h2></div></div>
          <div className="form-grid">
            <label className="field-label">Age (years)<input name="age" type="number" min="13" max="120" value={profile.age ?? ''} onChange={update} placeholder="e.g. 28" /></label>
            <label className="field-label">Gender<select name="gender" value={profile.gender ?? ''} onChange={update}><option value="">Prefer not to say</option><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option></select></label>
            <label className="field-label">Height (cm)<input name="height" type="number" min="80" max="250" step="0.1" value={profile.height ?? ''} onChange={update} placeholder="e.g. 175" /></label>
            <label className="field-label">Current weight (kg)<input name="weight" type="number" min="25" max="350" step="0.1" value={profile.weight ?? ''} onChange={update} placeholder="e.g. 72" /></label>
          </div>
        </section>

        <section className="content-card form-section">
          <div className="content-card-heading"><div><span className="eyebrow">TRAINING PLAN</span><h2>Your goals and routine</h2></div></div>
          <div className="form-grid">
            <label className="field-label">Primary goal<select name="goal" value={profile.goal || 'general_fitness'} onChange={update}><option value="general_fitness">General fitness</option><option value="muscle_gain">Build muscle</option><option value="fat_loss">Fat loss</option><option value="strength">Build strength</option></select></label>
            <label className="field-label">Training experience<select name="experience" value={profile.experience || 'beginner'} onChange={update}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></label>
            <label className="field-label">Training days per week<select name="training_days" value={profile.training_days ?? 3} onChange={update}>{[1, 2, 3, 4, 5, 6, 7].map((days) => <option key={days} value={days}>{days} {days === 1 ? 'day' : 'days'}</option>)}</select></label>
          </div>
        </section>

        <section className="content-card form-section">
          <div className="content-card-heading"><div><span className="eyebrow">NUTRITION</span><h2>Food preferences</h2></div></div>
          <label className="field-label">Diet preference<select name="diet_preference" value={profile.diet_preference || 'omnivore'} onChange={update}><option value="omnivore">Omnivore</option><option value="vegetarian">Vegetarian</option><option value="vegan">Vegan</option><option value="pescatarian">Pescatarian</option></select></label>
        </section>

        <section className="content-card form-section">
          <div className="content-card-heading"><div><span className="eyebrow">SAFETY & ACCESS</span><h2>Restrictions and equipment</h2></div><ShieldCheck size={20} className="text-emerald-600" /></div>
          <div className="form-grid">
            {LIST_FIELDS.map(({ name, label, placeholder }) => (
              <label className="field-label" key={name}>{label}<input name={name} value={profileListValue(name, profile[name])} onChange={update} placeholder={placeholder} /></label>
            ))}
          </div>
          <p className="safety-note"><AlertTriangle size={15} /> Add injury site, severity, and movement context when known (for example, “knee severe pain”). Severe/acute notes further restrict related movements. Meal exclusions can only use catalog labels; consult a qualified professional about injuries or dietary needs.</p>
        </section>

        <div className="form-footer">
          <span className="subtle-label">Account: {user.email}</span>
          <button className="button button-primary" type="submit" disabled={saving}>
            {saving ? <LoaderCircle className="spin" size={17} /> : <Save size={17} />} Save profile
          </button>
        </div>
      </form>
    </div>
  );
}

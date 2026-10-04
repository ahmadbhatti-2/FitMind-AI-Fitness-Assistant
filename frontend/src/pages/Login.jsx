import { useState } from 'react';
import { ArrowRight, Eye, EyeOff, LoaderCircle, ShieldCheck, Sparkles } from 'lucide-react';
import useAuth from '../auth/useAuth';
import api from '../services/api';
import BrandMark from '../components/BrandMark';

function getErrorMessage(error) {
  return error.response?.data?.detail || 'Could not connect to FitMind. Check that the backend is running and try again.';
}

export default function Login() {
  const { signIn } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ username: '', email: '', password: '' });

  const update = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
    setError('');
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      const endpoint = isRegistering ? '/auth/register' : '/auth/login';
      const payload = isRegistering
        ? { username: form.username.trim(), email: form.email.trim(), password: form.password }
        : { email: form.email.trim(), password: form.password };
      const { data } = await api.post(endpoint, payload);
      signIn(data);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="auth-page auth-single-page">
      <div className="auth-atmosphere" aria-hidden="true"><span /><span /><span /></div>
      <section className="auth-panel">
        <div className="auth-form-wrap auth-single-card">
          <a className="brand auth-card-brand" href="/" aria-label="FitMind home">
            <span className="brand-mark"><BrandMark /></span>
            <span>fitmind<span className="brand-dot">.</span></span>
          </a>
          <div className="auth-card-intro">
            <span className="auth-form-kicker"><Sparkles size={13} /> YOUR PLAN. YOUR PACE.</span>
            <h1>{isRegistering ? <>Start your<br /><span>stronger story.</span></> : <>Make room for<br /><span>your best self.</span></>}</h1>
            <p>{isRegistering ? 'A smarter routine, built around your real life.' : 'Your personal training and nutrition plan is ready when you are.'}</p>
          </div>
          <span className="auth-form-kicker">{isRegistering ? 'YOUR NEXT CHAPTER STARTS HERE' : 'GOOD TO SEE YOU AGAIN'}</span>
          <h2>{isRegistering ? 'Create your account' : 'Welcome back'}</h2>

          <form onSubmit={submit} className="auth-form">
            {isRegistering && (
              <label className="field-label">
                Name
                <input autoComplete="name" name="username" value={form.username} onChange={update} minLength={3} maxLength={50} required placeholder="Your name" />
              </label>
            )}
            <label className="field-label">
              Email address
              <input autoComplete="email" type="email" name="email" value={form.email} onChange={update} maxLength={100} required placeholder="you@example.com" />
            </label>
            <label className="field-label">
              Password
              <span className="password-field">
                <input autoComplete={isRegistering ? 'new-password' : 'current-password'} type={showPassword ? 'text' : 'password'} name="password" value={form.password} onChange={update} minLength={isRegistering ? 8 : 1} maxLength={128} required placeholder={isRegistering ? 'At least 8 characters' : 'Your password'} />
                <button className="icon-button password-toggle" type="button" onClick={() => setShowPassword((visible) => !visible)} aria-label={showPassword ? 'Hide password' : 'Show password'}>
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
            </label>

            {error && <p className="form-error" role="alert">{error}</p>}

            <button className="button button-primary auth-submit" type="submit" disabled={busy}>
              {busy ? <LoaderCircle className="spin" size={18} /> : <>{isRegistering ? 'Create account' : 'Sign in'} <ArrowRight size={18} /></>}
            </button>
          </form>

          <p className="auth-switch">
            {isRegistering ? 'Already have an account?' : 'New to FitMind?'}
            <button type="button" onClick={() => { setIsRegistering((value) => !value); setShowPassword(false); setError(''); }}>
              {isRegistering ? 'Sign in' : 'Create an account'}
            </button>
          </p>
          <p className="auth-footnote"><ShieldCheck size={13} /> Your account and health notes stay private. For training and nutrition education only.</p>
        </div>
      </section>
    </main>
  );
}

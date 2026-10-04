import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Bot, CircleAlert, Dumbbell, Send, Sparkles, UserRound } from 'lucide-react';
import { Link } from 'react-router-dom';
import ChatBubble from '../components/ChatBubble';
import useAuth from '../auth/useAuth';
import api, { apiEndpoints } from '../services/api';

const SUGGESTIONS = [
  'What workout should I do today?',
  'Suggest a meal for my goal',
  'How should I adjust after my recent workouts?',
];

export default function AICoach() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([
    { role: 'ai', content: `Hi ${user.username.split(' ')[0]} — I can use your saved profile and logged workout history to help plan your next session or meal. What would you like help with?` },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [failedPrompt, setFailedPrompt] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const sendMessage = async (text = input, appendUser = true) => {
    const message = text.trim();
    if (!message || loading) return;
    setInput('');
    setError('');
    setFailedPrompt('');
    if (appendUser) setMessages((current) => [...current, { role: 'user', content: message }]);
    setLoading(true);
    try {
      const { data } = await api.post(apiEndpoints.agentChat, { message });
      if (data.status === 'error') throw new Error(data.message || 'The coach could not complete this request.');
      setMessages((current) => [...current, { role: 'ai', content: data.response || 'I could not form a response. Please try asking in another way.' }]);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail || requestError.message || 'The AI coach is temporarily unavailable.';
      setError(detail);
      setFailedPrompt(message);
    } finally {
      setLoading(false);
    }
  };

  const retryMessage = () => sendMessage(failedPrompt, false);

  return (
    <section className="coach-shell">
      <header className="coach-header">
        <span className="coach-avatar"><Bot size={22} /></span>
        <div><span className="eyebrow">YOUR FITNESS ASSISTANT</span><h1>AI Coach</h1></div>
        <span className="coach-context"><Sparkles size={15} /> Uses your saved profile & history</span>
      </header>
      <div className="coach-messages" aria-live="polite">
        {messages.map((message, index) => {
          const previousPrompt = message.role === 'ai'
            ? messages.slice(0, index).reverse().find((entry) => entry.role === 'user')?.content || ''
            : '';
          const isWorkoutRecommendation = message.role === 'ai'
            && /\b(workout|train(?:ing)?|exercise|gym|muscle|legs?|chest|back|recovery|rest day|session)\b/i.test(previousPrompt);

          return (
            <div className={`coach-message ${message.role === 'user' ? 'coach-message-user' : ''}`} key={`${index}-${message.role}`}>
              <span className={`message-avatar ${message.role === 'user' ? 'message-avatar-user' : ''}`}>{message.role === 'user' ? <UserRound size={16} /> : <Bot size={16} />}</span>
              <div className="message-content">
                <span className="message-author">{message.role === 'user' ? 'You' : 'FitMind Coach'}</span>
                <ChatBubble message={message.content} isAi={message.role === 'ai'} />
                {isWorkoutRecommendation && (
                  <article className="coach-recommendation-card">
                    <span className="coach-recommendation-icon"><Dumbbell size={18} /></span>
                    <div className="coach-recommendation-copy">
                      <span className="eyebrow">YOUR NEXT SESSION</span>
                      <strong>Workout recommendation</strong>
                      <p>Based on your saved profile and recent training history.</p>
                    </div>
                    <Link className="button button-primary" to="/workouts">View & start workout <ArrowUpRight size={16} /></Link>
                  </article>
                )}
              </div>
            </div>
          );
        })}
        {loading && <div className="coach-thinking"><span /><span /><span /> Reviewing your profile and training context…</div>}
        <div ref={bottomRef} />
      </div>
      {error && <div className="inline-message inline-error coach-error" role="alert"><CircleAlert size={16} /> <span>{error}</span>{failedPrompt && <button className="inline-retry" type="button" onClick={retryMessage} disabled={loading}>Try again</button>}</div>}
      <div className="coach-compose-area">
        {messages.length === 1 && <div className="suggestion-list">{SUGGESTIONS.map((suggestion) => <button className="suggestion-chip" type="button" key={suggestion} onClick={() => sendMessage(suggestion)} disabled={loading}>{suggestion}</button>)}</div>}
        <form className="coach-compose" onSubmit={(event) => { event.preventDefault(); sendMessage(); }}>
          <label className="sr-only" htmlFor="coach-input">Message the fitness coach</label>
          <input id="coach-input" value={input} onChange={(event) => setInput(event.target.value)} maxLength={2000} placeholder="Ask about today's workout, recovery, or meals…" disabled={loading} />
          <button className="button button-primary" type="submit" disabled={loading || !input.trim()} aria-label="Send message"><Send size={18} /></button>
        </form>
        <p className="coach-disclaimer">Fitness guidance is educational and not a substitute for care from a qualified health professional.</p>
      </div>
    </section>
  );
}

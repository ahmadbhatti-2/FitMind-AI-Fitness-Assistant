import { useCallback, useEffect, useState } from 'react';
import { Apple, Check, CircleAlert, Heart, LoaderCircle, RefreshCw, ThumbsDown, Utensils } from 'lucide-react';
import { Link } from 'react-router-dom';
import useAuth from '../auth/useAuth';
import api, { apiEndpoints } from '../services/api';
import { mealImage } from '../services/visualAssets';

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'];

function fetchMealRecommendations(userId) {
  return Promise.allSettled(
    MEAL_TYPES.map((type) => api.get(apiEndpoints.getMealRec(userId, type))),
  );
}

function errorMessage(error) {
  return error.response?.data?.detail || 'Could not load this meal. Update your profile or try again.';
}

export default function Nutrition() {
  const { user } = useAuth();
  const [meals, setMeals] = useState({});
  const [errors, setErrors] = useState({});
  const [logged, setLogged] = useState({});
  const [busy, setBusy] = useState({});
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState('');

  const loadMeals = useCallback(async () => {
    const results = await fetchMealRecommendations(user.user_id);
    const nextMeals = {};
    const nextErrors = {};
    results.forEach((result, index) => {
      const type = MEAL_TYPES[index];
      if (result.status === 'fulfilled') nextMeals[type] = result.value.data;
      else nextErrors[type] = errorMessage(result.reason);
    });
    setMeals(nextMeals);
    setErrors(nextErrors);
    setLoading(false);
  }, [user.user_id]);

  useEffect(() => {
    let active = true;
    fetchMealRecommendations(user.user_id).then((results) => {
      if (!active) return;
      const nextMeals = {};
      const nextErrors = {};
      results.forEach((result, index) => {
        const type = MEAL_TYPES[index];
        if (result.status === 'fulfilled') nextMeals[type] = result.value.data;
        else nextErrors[type] = errorMessage(result.reason);
      });
      setMeals(nextMeals);
      setErrors(nextErrors);
      setLoading(false);
    });
    return () => { active = false; };
  }, [user.user_id]);

  const logMeal = async (type, meal) => {
    setBusy((current) => ({ ...current, [type]: true }));
    setNotice('');
    try {
      await api.post(apiEndpoints.getMealHistory(user.user_id), {
        meal_id: meal.id,
        meal_type: type,
      });
      setLogged((current) => ({ ...current, [type]: true }));
      setNotice(`${type[0].toUpperCase()}${type.slice(1)} saved to your food history.`);
    } catch (error) {
      setErrors((current) => ({ ...current, [type]: errorMessage(error) }));
    } finally {
      setBusy((current) => ({ ...current, [type]: false }));
    }
  };

  const sendFeedback = async (meal, value) => {
    try {
      await api.post(apiEndpoints.saveFeedback(user.user_id), {
        item_id: meal.id,
        item_type: 'meal',
        feedback_type: value,
      });
      setNotice('Thanks — your feedback will inform future recommendations.');
    } catch (error) {
      setNotice(errorMessage(error));
    }
  };

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div><span className="eyebrow">EAT WELL, WITHOUT THE GUESSWORK</span><h1>Your meal ideas</h1><p>Suggestions account for your goal, diet, allergies, and recent meal log.</p></div>
        <button className="button button-outline" type="button" onClick={() => { setLoading(true); loadMeals(); }} disabled={loading}><RefreshCw size={16} /> Refresh</button>
      </div>
      {notice && <div className="inline-message inline-success" role="status"><Check size={17} /> {notice}</div>}
      {loading && <div className="loading-state"><LoaderCircle className="spin" /> Finding meals that fit your preferences…</div>}

      {!loading && (
        <div className="meal-grid">
          {MEAL_TYPES.map((type) => {
            const meal = meals[type];
            const image = mealImage(meal);
            return (
              <article className="meal-card" key={type}>
                {image && <div className="meal-visual">
                  <img src={image} alt={meal?.meal_name || ''} loading="lazy" onError={(event) => { event.currentTarget.closest('.meal-visual').hidden = true; }} />
                  <span className="meal-visual-label"><Apple size={14} /> {meal?.meal_name}</span>
                </div>}
                <div className="meal-card-body">
                  <div className="meal-card-top"><span className="icon-tile icon-emerald"><Apple size={20} /></span><span className="meal-type">{type}</span></div>
                  {meal ? (
                    <>
                      <h2>{meal.meal_name}</h2>
                      <div className="ingredient-list">{meal.ingredients?.map((ingredient) => <span key={ingredient}>{ingredient.replaceAll('_', ' ')}</span>)}</div>
                      <p className="why-note"><Utensils size={15} /> {meal.reasons?.[1] || 'Matched to your saved preferences.'}</p>
                      {meal.is_high_protein && <span className="nutrition-badge">Protein-rich option</span>}
                      <div className="meal-actions">
                        <button className="button button-primary" type="button" disabled={busy[type] || logged[type]} onClick={() => logMeal(type, meal)}>
                          {busy[type] ? <LoaderCircle className="spin" size={16} /> : <Check size={16} />} {logged[type] ? 'Logged today' : 'Log as eaten'}
                        </button>
                        <button className="icon-button feedback-button" type="button" onClick={() => sendFeedback(meal, 'liked')} aria-label={`Like ${meal.meal_name}`} title="I like this meal"><Heart size={18} /></button>
                        <button className="icon-button feedback-button" type="button" onClick={() => sendFeedback(meal, 'disliked')} aria-label={`Avoid ${meal.meal_name}`} title="Don't recommend this meal again"><ThumbsDown size={17} /></button>
                      </div>
                      {errors[type] && <p className="inline-message inline-error"><CircleAlert size={15} /> {errors[type]}</p>}
                    </>
                  ) : (
                    <div className="meal-empty">
                      <h2>Could not find a match</h2>
                      <p>{errors[type] || 'No meal currently matches your preferences.'}</p>
                      <Link className="text-link" to="/profile">Review diet and allergy settings</Link>
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
